from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from mysql.connector import Error, ClientFlag
from functools import wraps
import os
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

app = Flask(__name__)
# Use environment variable if available, otherwise generate a new one
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)

# Store the key in an environment variable or config file for production
# You should save this key and reuse it, otherwise sessions will be invalidated on server restart

# Database configuration


def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            print("Successfully connected to the database")
        return connection
    except Error as e:
        print(f"Error connecting to MySQL Database: {e}")
        return None

# Login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session and 'is_guest' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                flash('Successfully logged in!', 'success')
                return redirect(url_for('dashboard'))
            
        flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/guest-login')
def guest_login():
    session['is_guest'] = True
    session['username'] = 'Guest'
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            
            # Check if username already exists
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            if cursor.fetchone():
                flash('Username already exists', 'error')
                return redirect(url_for('register'))
            
            # Create new user
            hashed_password = generate_password_hash(password)
            cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)',
                         (username, hashed_password))
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/teams')
@login_required
def teams():
    conn = get_db_connection()
    teams_data = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT id, team_name, country, founded_year, league 
                FROM teams 
                ORDER BY team_name
            ''')
            teams_data = cursor.fetchall()
        except Error as e:
            flash(f'Error fetching teams: {e}', 'error')
        finally:
            cursor.close()
            conn.close()
    return render_template('teams.html', teams=teams_data)

@app.route('/players')
@login_required
def players():
    conn = get_db_connection()
    players_data = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT p.id, p.name, t.team_name as team, p.position, p.age, p.nationality
                FROM players p
                LEFT JOIN teams t ON p.team_id = t.id
                ORDER BY p.name
            ''')
            players_data = cursor.fetchall()
        except Error as e:
            flash(f'Error fetching players: {e}', 'error')
        finally:
            cursor.close()
            conn.close()
    return render_template('players.html', players=players_data)

@app.route('/matches')
@login_required
def matches():
    conn = get_db_connection()
    matches_data = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT m.id, 
                       ht.team_name as home_team, 
                       at.team_name as away_team,
                       m.match_date,
                       m.match_time,
                       s.name as stadium,
                       m.score
                FROM matches m
                LEFT JOIN teams ht ON m.home_team_id = ht.id
                LEFT JOIN teams at ON m.away_team_id = at.id
                LEFT JOIN stadiums s ON m.stadium_id = s.id
                ORDER BY m.match_date DESC, m.match_time DESC
            ''')
            matches_data = cursor.fetchall()
        except Error as e:
            flash(f'Error fetching matches: {e}', 'error')
        finally:
            cursor.close()
            conn.close()
    return render_template('matches.html', matches=matches_data)

@app.route('/stadiums')
@login_required
def stadiums():
    conn = get_db_connection()
    stadiums_data = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT id, name, city, country, capacity, year_built
                FROM stadiums
                ORDER BY name
            ''')
            stadiums_data = cursor.fetchall()
        except Error as e:
            flash(f'Error fetching stadiums: {e}', 'error')
        finally:
            cursor.close()
            conn.close()
    return render_template('stadiums.html', stadiums=stadiums_data)

if __name__ == '__main__':
    app.run(debug=True) 