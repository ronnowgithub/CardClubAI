from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from functools import wraps
from enum import Enum
from datetime import datetime

class EventStatus(Enum):
    CANCELLED = "Cancelled"
    UPCOMING = "Upcoming"
    FINISHED = "Finished"

app = Flask(__name__)
app.secret_key = 'DummyWillChangeLater'  # Required for session management

def get_db():
    conn = sqlite3.connect('/tmp/users.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            won INTEGER DEFAULT 0,
            loss INTEGER DEFAULT 0
        )
    ''')
    
    # Create events table with date (YYYY-MM-DD format)
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            host_id INTEGER NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Cancelled', 'Upcoming', 'Finished')),
            FOREIGN KEY (host_id) REFERENCES users (id)
        )
    ''')
    
    # Create event_results table
    c.execute('''
        CREATE TABLE IF NOT EXISTS event_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events (id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(event_id, user_id)
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
    
    # Check if user exists
    c.execute('SELECT name FROM users WHERE name = ?', (username,))
    user = c.fetchone()
    conn.close()
    
    if user is None:
        flash('User does not exist. Please register first.')
        return redirect(url_for('login'))
    
    session['username'] = username
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        conn = get_db()
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (name) VALUES (?)', (username,))
            conn.commit()
            session['username'] = username
            return redirect(url_for('dashboard'))
        except sqlite3.IntegrityError:
            flash('Username already exists. Please choose another.')
            return redirect(url_for('register'))
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db()
    c = conn.cursor()
    
    # Get all users
    c.execute('SELECT id, name, won, loss FROM users')
    users = c.fetchall()
    
    # Get all events with host names and results
    c.execute('''
        SELECT 
            events.id,
            date(events.date) as date,
            users.name as host_name,
            events.status
        FROM events 
        JOIN users ON events.host_id = users.id
        ORDER BY events.date DESC
    ''')
    events = c.fetchall()
    
    # Get event results
    c.execute('''
        SELECT 
            event_results.event_id,
            event_results.user_id,
            users.name as user_name,
            event_results.amount
        FROM event_results
        JOIN users ON event_results.user_id = users.id
    ''')
    results = c.fetchall()
    
    # Organize results by event
    event_results = {}
    for result in results:
        event_id = result['event_id']
        if event_id not in event_results:
            event_results[event_id] = []
        event_results[event_id].append({
            'user_id': result['user_id'],
            'user_name': result['user_name'],
            'amount': result['amount']
        })
    
    conn.close()
    return render_template('dashboard.html', users=users, events=events, event_results=event_results)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/event/create', methods=['POST'])
@login_required
def create_event():
    date = request.form['date']  # Will be in YYYY-MM-DD format from the date input
    
    # Get host_id from the current user's name
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE name = ?', (session['username'],))
    host = c.fetchone()
    
    if host:
        try:
            c.execute('''
                INSERT INTO events (date, host_id, status)
                VALUES (?, ?, ?)
            ''', (date, host['id'], EventStatus.UPCOMING.value))
            conn.commit()
            flash('Event created successfully!')
        except sqlite3.Error as e:
            flash('Error creating event: ' + str(e))
    else:
        flash('Error: Host not found')
    
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/event/<int:event_id>/status', methods=['POST'])
@login_required
def update_event_status(event_id):
    if request.form['status'] == 'edit':
        # Redirect to an edit page or handle edit action
        flash('Edit functionality coming soon!')
        return redirect(url_for('dashboard'))
    
    new_status = request.form['status']
    if new_status not in [status.value for status in EventStatus]:
        flash('Invalid status')
        return redirect(url_for('dashboard'))
    
    conn = get_db()
    c = conn.cursor()
    
    # Verify if the current user is the host
    c.execute('''
        SELECT host_id, users.name as host_name 
        FROM events 
        JOIN users ON events.host_id = users.id 
        WHERE events.id = ?
    ''', (event_id,))
    event = c.fetchone()
    
    if event and event['host_name'] == session['username']:
        c.execute('UPDATE events SET status = ? WHERE id = ?', (new_status, event_id))
        conn.commit()
        flash('Event status updated successfully!')
    else:
        flash('You are not authorized to update this event')
    
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/event/<int:event_id>/result', methods=['POST'])
@login_required
def add_event_result(event_id):
    conn = get_db()
    c = conn.cursor()
    
    # Verify if the current user is the host
    c.execute('''
        SELECT host_id, users.name as host_name 
        FROM events 
        JOIN users ON events.host_id = users.id 
        WHERE events.id = ?
    ''', (event_id,))
    event = c.fetchone()
    
    if not event or event['host_name'] != session['username']:
        flash('You are not authorized to update this event')
        conn.close()
        return redirect(url_for('dashboard'))
    
    try:
        # Get all users
        c.execute('SELECT id FROM users')
        users = c.fetchall()
        
        # Start a transaction
        c.execute('BEGIN TRANSACTION')
        
        # Delete existing results for this event
        c.execute('DELETE FROM event_results WHERE event_id = ?', (event_id,))
        
        # Reset user totals for this event
        c.execute('''
            UPDATE users SET 
                won = won - CASE WHEN er.amount > 0 THEN er.amount ELSE 0 END,
                loss = loss - CASE WHEN er.amount < 0 THEN ABS(er.amount) ELSE 0 END
            FROM event_results er
            WHERE users.id = er.user_id AND er.event_id = ?
        ''', (event_id,))
        
        # Process each user's result
        for user in users:
            user_id = user['id']
            participated = request.form.get(f'participated_{user_id}') == 'on'
            
            if participated:
                try:
                    amount = int(request.form.get(f'amount_{user_id}', 0))
                    
                    # Add new result
                    c.execute('INSERT INTO event_results (event_id, user_id, amount) VALUES (?, ?, ?)',
                             (event_id, user_id, amount))
                    
                    # Update user totals
                    if amount > 0:
                        c.execute('UPDATE users SET won = won + ? WHERE id = ?', (amount, user_id))
                    else:
                        c.execute('UPDATE users SET loss = loss + ? WHERE id = ?', (abs(amount), user_id))
                except ValueError:
                    # Skip if amount is not a valid number
                    continue
        
        conn.commit()
        flash('Event results updated successfully!')
        
    except sqlite3.Error as e:
        conn.rollback()
        flash('Error updating results: ' + str(e))
    finally:
        conn.close()
    
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True) 