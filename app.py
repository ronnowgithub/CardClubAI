from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = 'DummyWillChangeLater'  # Required for session management

def get_db():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            won INTEGER DEFAULT 0,
            loss INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def login():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    username = request.form['username']
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (name) VALUES (?)', (username,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # User already exists
    finally:
        conn.close()
    session['username'] = username
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT name, won, loss FROM users')
    users = c.fetchall()
    conn.close()
    return render_template('dashboard.html', users=users)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True) 