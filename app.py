"""
NutriPulse — Main Flask Application
Routes: food logging, dashboard, AI features.
Auth removed for simplicity — uses a default user.
Run with: python app.py
"""
import os
from uuid import uuid4
from flask import (Flask, render_template, request, redirect,
                   url_for, session, jsonify, send_from_directory)
from dotenv import load_dotenv

from models import (init_db, create_user, get_user_by_id,
                    add_food_entry, get_food_entries_today, delete_food_entry,
                    get_daily_summary, update_calorie_goal,
                    add_exercise, log_steps, get_fitness_summary, update_integration)
from ai_service import analyze_food_image, get_meal_recommendations, is_ai_available

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'nutripulse-dev-secret-2024')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

init_db()

# Default user ID — auto-created on first run, no login needed
DEFAULT_USER_ID = None


def get_default_user_id():
    """Create or retrieve the default demo user. Called once at startup."""
    global DEFAULT_USER_ID
    if DEFAULT_USER_ID:
        return DEFAULT_USER_ID
    from models import get_user_by_email
    user = get_user_by_email('demo@nutripulse.app')
    if user:
        DEFAULT_USER_ID = user['id']
    else:
        DEFAULT_USER_ID = create_user('demo@nutripulse.app', 'NutriPulse User', 'no-auth')
    return DEFAULT_USER_ID


# Auto-set session on every request so all pages work without login
@app.before_request
def auto_login():
    if 'user_id' not in session:
        uid = get_default_user_id()
        session['user_id'] = uid
        session['user_name'] = 'NutriPulse User'


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ── Page Routes ──

@app.route('/')
def index():
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    user = get_user_by_id(session['user_id'])
    summary = get_daily_summary(session['user_id'])
    fitness = get_fitness_summary(session['user_id'])
    entries = get_food_entries_today(session['user_id'])
    return render_template('dashboard.html', user=user, summary=summary, fitness=fitness,
                           entries=entries, ai_available=is_ai_available())


@app.route('/food-log')
def food_log():
    entries = get_food_entries_today(session['user_id'])
    return render_template('food_log.html', entries=entries,
                           ai_available=is_ai_available())


@app.route('/recommendations')
def recommendations():
    return render_template('recommendations.html', ai_available=is_ai_available())


# ── API Routes ──

@app.route('/api/food', methods=['POST'])
def api_add_food():
    """Add a food entry manually."""
    data = request.get_json()
    if not data or not data.get('food_name'):
        return jsonify({'error': 'Food name is required'}), 400
    entry_id = add_food_entry(session['user_id'], data)
    return jsonify({'success': True, 'id': entry_id})


@app.route('/api/food/<int:entry_id>', methods=['DELETE'])
def api_delete_food(entry_id):
    delete_food_entry(entry_id, session['user_id'])
    return jsonify({'success': True})


@app.route('/api/food/analyze', methods=['POST'])
def api_analyze_food():
    """Upload image → AI analyzes → return nutrition data."""
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    file = request.files['image']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file. Use JPG, PNG, GIF, or WebP.'}), 400

    # Save image
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # AI analysis
    result = analyze_food_image(filepath)
    if 'error' in result:
        return jsonify(result), 500

    result['image_filename'] = filename
    return jsonify(result)


@app.route('/api/dashboard-data')
def api_dashboard_data():
    user = get_user_by_id(session['user_id'])
    summary = get_daily_summary(session['user_id'])
    entries = get_food_entries_today(session['user_id'])
    return jsonify({
        'summary': summary,
        'entries': entries,
        'calorie_goal': user['daily_calorie_goal']
    })


@app.route('/api/recommendations', methods=['POST'])
def api_recommendations():
    user = get_user_by_id(session['user_id'])
    entries = get_food_entries_today(session['user_id'])
    result = get_meal_recommendations(entries, user['daily_calorie_goal'])
    if 'error' in result:
        return jsonify(result), 500
    return jsonify(result)


@app.route('/api/settings', methods=['POST'])
def api_settings():
    data = request.get_json()
    goal = data.get('daily_calorie_goal')
    if goal and isinstance(goal, (int, float)) and 500 <= goal <= 10000:
        update_calorie_goal(session['user_id'], int(goal))
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid calorie goal (500-10000)'}), 400


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/api/exercise', methods=['POST'])
def api_exercise():
    data = request.get_json()
    if not data or not data.get('activity_name'):
        return jsonify({'error': 'Activity name is required'}), 400
    add_exercise(session['user_id'], data['activity_name'], data.get('duration_min', 0), data.get('calories_burned', 0))
    return jsonify({'success': True})


@app.route('/api/steps', methods=['POST'])
def api_steps():
    data = request.get_json()
    steps = data.get('step_count', 0)
    log_steps(session['user_id'], steps)
    return jsonify({'success': True})


@app.route('/api/integrations', methods=['POST'])
def api_integrations():
    data = request.get_json()
    integration = data.get('integration')
    status = data.get('status', 1)
    if integration in ['spotify', 'strava']:
        update_integration(session['user_id'], integration, status)
        
        # Simulate syncing data from Strava when connected
        if integration == 'strava' and status == 1:
            add_exercise(session['user_id'], "Strava: Morning Run", 45, 420)
            add_exercise(session['user_id'], "Strava: Afternoon Ride", 30, 250)
            
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid integration'}), 400


# ── Error Handlers ──

@app.errorhandler(404)
def not_found(e):
    return redirect(url_for('dashboard'))


@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum 16MB.'}), 413


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)
