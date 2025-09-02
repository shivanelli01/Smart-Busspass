from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database setup function
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        balance INTEGER DEFAULT 0
                    )''')

    # Create travel_history table
    cursor.execute('''CREATE TABLE IF NOT EXISTS travel_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        bus_stop TEXT NOT NULL,
                        travel_date TEXT NOT NULL,
                        fare INTEGER NOT NULL,
                        FOREIGN KEY (username) REFERENCES users(username)
                    )''')

    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Home Route
@app.route('/')
def home():
    return render_template('index.html')

# Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            return redirect('/login')
        except sqlite3.IntegrityError:
            return "Username already exists. Please choose a different one."
        finally:
            conn.close()

    return render_template('register.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            return redirect(url_for('dashboard', username=username))
        else:
            return "Invalid credentials. Please try again."

    return render_template('login.html')

# Dashboard Route
@app.route('/dashboard')
def dashboard():
    username = request.args.get('username')

    if username:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Get balance
        cursor.execute("SELECT balance FROM users WHERE username = ?", (username,))
        balance = cursor.fetchone()[0]

        # Get travel history
        cursor.execute("SELECT bus_stop, travel_date, fare FROM travel_history WHERE username = ?", (username,))
        travel_history = cursor.fetchall()

        conn.close()

        return render_template('dashboard.html', balance=balance, username=username, travel_history=travel_history)
    else:
        return redirect('/login')
    
@app.route('/track_bus')
def track_bus():
    return render_template('track_bus.html')

# Travel Route
@app.route('/travel', methods=['POST'])
def travel():
    username = request.args.get('username')
    bus_stop = request.form['bus_stop']
    fare = 10  # Static fare for demonstration

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Get the user's current balance
    cursor.execute("SELECT balance FROM users WHERE username = ?", (username,))
    balance = cursor.fetchone()[0]

    if balance >= fare:
        new_balance = balance - fare

        # Update balance
        cursor.execute("UPDATE users SET balance = ? WHERE username = ?", (new_balance, username))

        # Insert travel history
        travel_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO travel_history (username, bus_stop, travel_date, fare) VALUES (?, ?, ?, ?)",
                       (username, bus_stop, travel_date, fare))
        conn.commit()
        conn.close()

        return redirect(url_for('dashboard', username=username))
    else:
        conn.close()
        return "Insufficient balance. Please recharge your account."

# Recharge Route
@app.route('/recharge', methods=['POST'])
def recharge():
    username = request.args.get('username')
    amount = int(request.form['amount'])

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (amount, username))
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard', username=username))

if __name__ == '__main__':
    app.run(debug=True)
