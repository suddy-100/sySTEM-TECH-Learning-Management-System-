from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import timedelta
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.permanent_session_lifetime = timedelta(days=7)

DATABASE = "site.db"

# --- Initialize DB and create tables if they don't exist ---
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Users table
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL
    )
    ''')

    # Registrations table
    c.execute('''
    CREATE TABLE IF NOT EXISTS registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT NOT NULL,
        email TEXT NOT NULL,
        dob_day TEXT,
        dob_month TEXT,
        dob_year TEXT,
        gender TEXT,
        role TEXT,
        subjects TEXT,
        locations TEXT
    )
    ''')

    # Dashboard table
    c.execute('''
    CREATE TABLE IF NOT EXISTS dashboard (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        homework_assigned TEXT,
        homework_submitted TEXT,
        attendance_students TEXT,
        attendance_tutor TEXT,
        registered_tutors TEXT,
        registered_students TEXT,
        dropout_tutors TEXT,
        dropout_students TEXT
    )
    ''')

    # Weekly schedule table
    c.execute('''
    CREATE TABLE IF NOT EXISTS weekly_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        monday TEXT,
        tuesday TEXT,
        wednesday TEXT,
        thursday TEXT,
        friday TEXT,
        saturday TEXT,
        sunday TEXT
    )
    ''')

    # Invoices table
    c.execute('''
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_no TEXT NOT NULL,
        due_date TEXT,
        client_name TEXT,
        client_email TEXT,
        company_name TEXT,
        company_address TEXT,
        items TEXT,
        subtotal TEXT,
        tax TEXT,
        total TEXT,
        payment_method TEXT,
        invoice_date TEXT,
        username TEXT
    )
    ''')

    conn.commit()
    conn.close()

# Initialize DB on startup
if not os.path.exists(DATABASE):
    init_db()

# --- Database helpers ---
def add_user(username, password):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()

def get_user_by_username_password(username, password):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT username, password FROM users WHERE username=? AND password=?", (username, password))
    row = cursor.fetchone()
    conn.close()
    return row

# --- Routes ---

# Homepage / Create Account
@app.route('/')
def index():
    session.pop('username', None)
    return render_template('Create_account.html')

@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))

        add_user(username, password)

        if remember:
            session['username'] = username
            flash("Account created successfully! Your details have been stored.", "success")
        else:
            flash("Account created successfully! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('Create_account.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        keep_logged_in = bool(request.form.get('keep_logged_in'))

        user = get_user_by_username_password(username, password)
        if user:
            session['username'] = username
            session.permanent = keep_logged_in
            if keep_logged_in:
                session['saved_username'] = username
                session['saved_password'] = password
                flash("Login successful! Your details have been stored.", "success")
            else:
                session.pop('saved_username', None)
                session.pop('saved_password', None)
                flash("Login successful! Welcome back.", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid username or password", "error")
            return redirect(url_for('login'))

    saved_username = session.get('saved_username', '')
    saved_password = session.get('saved_password', '')
    return render_template('Login_page.html', saved_username=saved_username, saved_password=saved_password)

# Forgot password
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if new_password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect(url_for('forgot_password'))

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()

        if user:
            cursor.execute("UPDATE users SET password=? WHERE username=?", (new_password, username))
            conn.commit()
            conn.close()
            flash(f"Password successfully updated for {username}", "success")
            return redirect(url_for('login'))
        else:
            conn.close()
            flash("Username not found!", "error")
            return redirect(url_for('forgot_password'))

    return render_template('Forgot_password.html')

# Home Page
@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('Home_page.html', username=session['username'])

# Static pages
@app.route('/about')
def about():
    return render_template('about_us.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/our_locations')
def our_locations():
    return render_template('our_locations.html')

# --- Registration ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form.get('fullname', '')
        email = request.form.get('email', '')
        dob_day = request.form.get('dob_day', '')
        dob_month = request.form.get('dob_month', '')
        dob_year = request.form.get('dob_year', '')
        gender = request.form.get('gender', '')
        role = request.form.get('role', '')
        subjects = request.form.getlist('subject')
        locations = request.form.getlist('location')
        subjects_str = ",".join(subjects)
        locations_str = ",".join(locations)

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO registrations (fullname, email, dob_day, dob_month, dob_year, gender, role, subjects, locations)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (fullname, email, dob_day, dob_month, dob_year, gender, role, subjects_str, locations_str))

        cursor.execute('''
            INSERT INTO dashboard (email, homework_assigned, homework_submitted, attendance_students,
                                   attendance_tutor, registered_tutors, registered_students,
                                   dropout_tutors, dropout_students)
            VALUES (?, '', '', '', '', '', '', '', '')
        ''', (email,))

        cursor.execute('''
            INSERT INTO weekly_schedule (email, monday, tuesday, wednesday, thursday, friday, saturday, sunday)
            VALUES (?, '', '', '', '', '', '', '')
        ''', (email,))

        conn.commit()
        conn.close()

        session['username'] = email
        session.permanent = True
        flash(f'Registration successful! Welcome, {fullname}!')
        return redirect(url_for('dashboard'))

    return render_template('registrations.html')

# --- Dashboard ---
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    if request.method == 'POST':
        data = [request.form.get(field, '') for field in [
            'homework_assigned', 'homework_submitted', 'attendance_students', 'attendance_tutor',
            'registered_tutors', 'registered_students', 'dropout_tutors', 'dropout_students'
        ]]
        cursor.execute('''
            UPDATE dashboard SET
                homework_assigned=?, homework_submitted=?, attendance_students=?,
                attendance_tutor=?, registered_tutors=?, registered_students=?,
                dropout_tutors=?, dropout_students=?
            WHERE email=?
        ''', (*data, username))
        conn.commit()
        conn.close()
        flash("Dashboard data saved successfully!", "success")
        return redirect(url_for('weekly_schedule'))

    cursor.execute('''
        SELECT homework_assigned, homework_submitted, attendance_students, attendance_tutor,
               registered_tutors, registered_students, dropout_tutors, dropout_students
        FROM dashboard WHERE email=?
    ''', (username,))
    row = cursor.fetchone()
    conn.close()

    dashboard_data = {
        "homework_assigned": row[0] if row else '',
        "homework_submitted": row[1] if row else '',
        "attendance_students": row[2] if row else '',
        "attendance_tutor": row[3] if row else '',
        "registered_tutors": row[4] if row else '',
        "registered_students": row[5] if row else '',
        "dropout_tutors": row[6] if row else '',
        "dropout_students": row[7] if row else ''
    }

    return render_template('dashboard.html', username=username, dashboard_data=dashboard_data)

# --- Weekly schedule ---
@app.route('/weekly_schedule', methods=['GET', 'POST'])
def weekly_schedule():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    if request.method == 'POST':
        data = [request.form.get(day, '') for day in ['monday','tuesday','wednesday','thursday','friday','saturday','sunday']]
        cursor.execute('''
            UPDATE weekly_schedule SET
                monday=?, tuesday=?, wednesday=?, thursday=?, friday=?, saturday=?, sunday=?
            WHERE email=?
        ''', (*data, username))
        conn.commit()
        conn.close()
        flash("Weekly schedule saved!", "success")
        return redirect(url_for('view_database'))

    cursor.execute('SELECT monday, tuesday, wednesday, thursday, friday, saturday, sunday FROM weekly_schedule WHERE email=?', (username,))
    row = cursor.fetchone()
    conn.close()

    schedule_data = {day: row[i] if row else '' for i, day in enumerate(['monday','tuesday','wednesday','thursday','friday','saturday','sunday'])}
    return render_template('weekly_schedule.html', schedule_data=schedule_data)

# --- Invoices ---
@app.route('/invoices', methods=['GET', 'POST'])
def invoices():
    if request.method == 'POST':
        invoice_items = []
        for i in range(1, 11):
            desc = request.form.get(f"desc_{i}")
            price = request.form.get(f"price_{i}")
            if desc or price:
                invoice_items.append(f"{desc}: {price}")

        invoice_no = request.form.get("invoice_no")
        due_date = request.form.get("due_date")
        client_name = request.form.get("client_name")
        client_email = request.form.get("client_email")
        company_name = request.form.get("company_name")
        company_address = request.form.get("company_address")
        subtotal = request.form.get("subtotal")
        tax = request.form.get("tax")
        total = request.form.get("total")
        payment_method = request.form.get("payment_method")
        invoice_date = request.form.get("invoice_date")
        username = session.get('username', '')

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO invoices (
                invoice_no, due_date, client_name, client_email,
                company_name, company_address, items, subtotal,
                tax, total, payment_method, invoice_date, username
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            invoice_no, due_date, client_name, client_email,
            company_name, company_address, ",".join(invoice_items),
            subtotal, tax, total, payment_method, invoice_date, username
        ))
        conn.commit()
        conn.close()
        flash("Invoice saved successfully!", "success")
        return redirect(url_for('view_database'))

    invoice = {
        "invoice_no": "",
        "due_date": "",
        "client_name": "",
        "client_email": "",
        "company_name": "",
        "company_address": "",
        "invoice_items": [{"description": "Tutoring services", "price": "$"}],
        "subtotal": "",
        "tax": "",
        "total": "",
        "payment_method": "",
        "invoice_date": ""
    }
    return render_template("invoices.html", invoice=invoice)

# --- View database ---
@app.route('/view_database')
def view_database():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    c.execute("SELECT * FROM registrations")
    registrations = c.fetchall()
    c.execute("SELECT * FROM dashboard")
    dashboard = c.fetchall()
    c.execute("SELECT * FROM weekly_schedule")
    weekly_schedule_data = c.fetchall()
    c.execute("SELECT * FROM invoices")
    invoices = c.fetchall()
    conn.close()

    return render_template(
        "view_database.html",
        users=users,
        registrations=registrations,
        dashboard=dashboard,
        weekly_schedule=weekly_schedule_data,
        invoices=invoices
    )

if __name__ == '__main__':
    app.run(debug=True)
