"""
NutriPulse — Database Layer
SQLite database with users and food_entries tables.
Zero-config: creates DB file automatically on first run.
"""
import sqlite3
import os
from datetime import datetime, date

DB_PATH = os.path.join(os.path.dirname(__file__), 'nutripulse.db')
DATABASE_URL = os.getenv('DATABASE_URL')

class PostgresWrapper:
    def __init__(self, conn):
        self.conn = conn
    
    def execute(self, query, params=()):
        import psycopg2.extras
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        query = query.replace('?', '%s')
        
        # SQLite uses datetime('now'), PG uses now()
        query = query.replace("datetime('now')", "now()")
        query = query.replace("date('now')", "current_date")
        query = query.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        
        if 'last_insert_rowid()' in query:
            return cur # handled separately in code if needed
            
        cur.execute(query, params)
        return cur
        
    def commit(self):
        self.conn.commit()
        
    def close(self):
        self.conn.close()

def get_conn():
    if DATABASE_URL and DATABASE_URL.startswith('postgres'):
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        return PostgresWrapper(conn)
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            daily_calorie_goal INTEGER DEFAULT 2000,
            spotify_connected INTEGER DEFAULT 0,
            strava_connected INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS food_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            food_name TEXT NOT NULL,
            calories REAL DEFAULT 0,
            protein REAL DEFAULT 0,
            carbs REAL DEFAULT 0,
            fat REAL DEFAULT 0,
            fiber REAL DEFAULT 0,
            serving_size TEXT DEFAULT '1 serving',
            meal_type TEXT DEFAULT 'snack',
            health_score INTEGER DEFAULT 5,
            ai_insight TEXT,
            image_filename TEXT,
            logged_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_food_user_date
            ON food_entries(user_id, logged_at);

        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_name TEXT NOT NULL,
            duration_min INTEGER DEFAULT 0,
            calories_burned REAL DEFAULT 0,
            logged_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            step_count INTEGER DEFAULT 0,
            logged_date TEXT DEFAULT (date('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    conn.close()


# ── User Operations ──

def create_user(email, name, password_hash):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO users (email, name, password_hash) VALUES (?, ?, ?)",
            (email, name, password_hash)
        )
        conn.commit()
        if DATABASE_URL and DATABASE_URL.startswith('postgres'):
            user_id = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()['id']
        else:
            user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_user_by_email(email):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_calorie_goal(user_id, goal):
    conn = get_conn()
    conn.execute("UPDATE users SET daily_calorie_goal = ? WHERE id = ?", (goal, user_id))
    conn.commit()
    conn.close()


def update_integration(user_id, integration, status):
    conn = get_conn()
    col = 'spotify_connected' if integration == 'spotify' else 'strava_connected'
    conn.execute(f"UPDATE users SET {col} = ? WHERE id = ?", (status, user_id))
    conn.commit()
    conn.close()


# ── Exercise & Steps Operations ──

def add_exercise(user_id, activity_name, duration_min, calories_burned):
    conn = get_conn()
    conn.execute(
        "INSERT INTO exercises (user_id, activity_name, duration_min, calories_burned) VALUES (?, ?, ?, ?)",
        (user_id, activity_name, duration_min, calories_burned)
    )
    conn.commit()
    conn.close()

def log_steps(user_id, step_count):
    conn = get_conn()
    today = date.today().isoformat()
    # Upsert logic for steps
    existing = conn.execute("SELECT id FROM steps WHERE user_id = ? AND logged_date = ?", (user_id, today)).fetchone()
    if existing:
        conn.execute("UPDATE steps SET step_count = step_count + ? WHERE id = ?", (step_count, existing['id']))
    else:
        conn.execute("INSERT INTO steps (user_id, step_count, logged_date) VALUES (?, ?, ?)", (user_id, step_count, today))
    conn.commit()
    conn.close()

def get_fitness_summary(user_id):
    conn = get_conn()
    today = date.today().isoformat()
    
    ex_row = conn.execute("""
        SELECT COALESCE(SUM(calories_burned), 0) as total_burned
        FROM exercises WHERE user_id = ? AND date(logged_at) = ?
    """, (user_id, today)).fetchone()
    
    st_row = conn.execute("""
        SELECT COALESCE(step_count, 0) as steps
        FROM steps WHERE user_id = ? AND logged_date = ?
    """, (user_id, today)).fetchone()
    
    conn.close()
    return {
        'calories_burned': ex_row['total_burned'] if ex_row else 0,
        'steps': st_row['steps'] if st_row else 0
    }


# ── Food Entry Operations ──

def add_food_entry(user_id, data):
    conn = get_conn()
    conn.execute("""
        INSERT INTO food_entries
            (user_id, food_name, calories, protein, carbs, fat, fiber,
             serving_size, meal_type, health_score, ai_insight, image_filename)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, data['food_name'], data.get('calories', 0),
        data.get('protein', 0), data.get('carbs', 0), data.get('fat', 0),
        data.get('fiber', 0), data.get('serving_size', '1 serving'),
        data.get('meal_type', 'snack'), data.get('health_score', 5),
        data.get('ai_insight', ''), data.get('image_filename', None)
    ))
    conn.commit()
    if DATABASE_URL and DATABASE_URL.startswith('postgres'):
        entry_id = conn.execute("SELECT id FROM food_entries WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)).fetchone()['id']
    else:
        entry_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return entry_id


def get_food_entries_today(user_id):
    conn = get_conn()
    today = date.today().isoformat()
    rows = conn.execute("""
        SELECT * FROM food_entries
        WHERE user_id = ? AND date(logged_at) = ?
        ORDER BY logged_at DESC
    """, (user_id, today)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_food_entries_range(user_id, days=7):
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM food_entries
        WHERE user_id = ? AND logged_at >= datetime('now', ?)
        ORDER BY logged_at DESC
    """, (user_id, f'-{days} days')).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_food_entry(entry_id, user_id):
    conn = get_conn()
    conn.execute(
        "DELETE FROM food_entries WHERE id = ? AND user_id = ?",
        (entry_id, user_id)
    )
    conn.commit()
    conn.close()


def get_daily_summary(user_id):
    """Returns today's totals for calories, protein, carbs, fat."""
    conn = get_conn()
    today = date.today().isoformat()
    row = conn.execute("""
        SELECT
            COALESCE(SUM(calories), 0) as total_calories,
            COALESCE(SUM(protein), 0) as total_protein,
            COALESCE(SUM(carbs), 0) as total_carbs,
            COALESCE(SUM(fat), 0) as total_fat,
            COALESCE(SUM(fiber), 0) as total_fiber,
            COUNT(*) as entry_count,
            COALESCE(AVG(health_score), 0) as avg_health_score
        FROM food_entries
        WHERE user_id = ? AND date(logged_at) = ?
    """, (user_id, today)).fetchone()
    conn.close()
    return dict(row)
