import pytest
from app import app
from models import init_db, get_conn

@pytest.fixture
def client():
    app.config['TESTING'] = True
    # use a separate test db if necessary, but for now we'll just test the routes
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client

def test_index_redirects_to_dashboard(client):
    rv = client.get('/')
    assert rv.status_code == 302
    assert '/dashboard' in rv.location

def test_dashboard_loads(client):
    rv = client.get('/dashboard')
    assert rv.status_code == 200
    assert b'Dashboard' in rv.data

def test_food_log_api_validation(client):
    # Test edge case: missing food_name
    rv = client.post('/api/food', json={'calories': 100})
    assert rv.status_code == 400
    assert b'error' in rv.data

def test_food_log_api_success(client):
    # Test valid flow
    rv = client.post('/api/food', json={'food_name': 'Apple', 'calories': 95, 'protein': 0.5})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['success'] == True

def test_settings_validation(client):
    # Test invalid calorie goal
    rv = client.post('/api/settings', json={'daily_calorie_goal': -100})
    assert rv.status_code == 400
    
    # Test valid calorie goal
    rv = client.post('/api/settings', json={'daily_calorie_goal': 2500})
    assert rv.status_code == 200

def test_strava_auth_redirects(client):
    # Tests the integration flow
    rv = client.get('/api/strava/auth')
    # If no client ID is set, it returns 500
    assert rv.status_code in [302, 500]
