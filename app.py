from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import timedelta
import sqlite3
import os

# ----------------------------------------
# Flask App Configuration
# ----------------------------------------
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Secret key for session management and flash messages
app.permanent_session_lifetime = timedelta(days=7)  # Sessions last 7 days

DATABASE = "site.db"  # SQLite database file storing all app data

# ----------------------------------------
# Database Class
# ----------------------------------------
class Database:
    """
    Handles SQLite database connections and initializes required tables.
    
    Tables:
    - users: stores login credentials (username, password)
    - registrations: stores user registration info
    - dashboard: stores dashboard data for each user
    - weekly_schedule: stores weekly schedule per user
    - invoices: stores invoice information
    """

    @staticmethod
    def connect():
        """Establish a connection to the SQLite database."""
        return sqlite3.connect(DATABASE)

    @staticmethod
    def init_db():
        """
        Initialize all required database tables if they do not exist.
        Each table's columns are designed to store specific types of data
        needed for the software solution.
        """
        conn = Database.connect()
        cursor = conn.cursor()

        # Users table: store login credentials
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
        ''')

        # Registrations table: store user profiles
        cursor.execute('''
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

        # Dashboard table: track homework, attendance, and registrations
        cursor.execute('''
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

        # Weekly schedule table: store weekly schedules
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS weekly_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            monday TEXT,
            tuesday TEXT,
            wednesday TEXT,
            thursday TEXT,
            friday TEXT,
            saturday TEXT,
            sunday TEXT,
            month TEXT,
            week TEXT
        )
        ''')

        # Invoices table: store invoice details
        cursor.execute('''
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

# ----------------------------------------
# User Class
# ----------------------------------------
class User:
    """
    Represents a user account for login purposes.

    Attributes:
    - username: str, user's login name
    - password: str, user's login password
    """

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def save(self):
        """Insert user credentials into the database."""
        conn = Database.connect()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (self.username, self.password))
        conn.commit()
        conn.close()

    @staticmethod
    def get_by_username_password(username, password):
        """
        Retrieve user credentials from the database to verify login.

        Returns:
            tuple(username, password) if user exists, else None
        """
        conn = Database.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT username, password FROM users WHERE username=? AND password=?", (username, password))
        row = cursor.fetchone()
        conn.close()
        return row

    @staticmethod
    def update_password(username, new_password):
        """
        Update password for an existing user.
        """
        conn = Database.connect()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password=? WHERE username=?", (new_password, username))
        conn.commit()
        conn.close()

# ----------------------------------------
# Registration Class
# ----------------------------------------
class Registration:
    """
    Handles user registration and initial setup for dashboard and weekly schedule.

    Attributes:
    - fullname, email, dob_day/month/year, gender, role, subjects, locations
    """

    def __init__(self, fullname, email, dob_day, dob_month, dob_year, gender, role, subjects, locations):
        self.fullname = fullname
        self.email = email
        self.dob_day = dob_day
        self.dob_month = dob_month
        self.dob_year = dob_year
        self.gender = gender
        self.role = role
        self.subjects = ",".join(subjects)
        self.locations = ",".join(locations)

    def save(self):
        """
        Save registration data into registrations table.
        Also creates initial dashboard and weekly schedule records for the user.
        """
        conn = Database.connect()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO registrations (fullname, email, dob_day, dob_month, dob_year, gender, role, subjects, locations)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (self.fullname, self.email, self.dob_day, self.dob_month, self.dob_year,
              self.gender, self.role, self.subjects, self.locations))

        cursor.execute('''
            INSERT INTO dashboard (email, homework_assigned, homework_submitted, attendance_students,
                                   attendance_tutor, registered_tutors, registered_students,
                                   dropout_tutors, dropout_students)
            VALUES (?, '', '', '', '', '', '', '', '')
        ''', (self.email,))

        cursor.execute('''
            INSERT INTO weekly_schedule (email, monday, tuesday, wednesday, thursday, friday, saturday, sunday, month, week)
            VALUES (?, '', '', '', '', '', '', '', '', '')
        ''', (self.email,))

        conn.commit()
        conn.close()

# ----------------------------------------
# Dashboard Class
# ----------------------------------------
class Dashboard:
    """
    Represents a user's dashboard.

    Tracks homework, attendance, registered students/tutors, and dropouts.
    """

    FIELDS = ['homework_assigned', 'homework_submitted', 'attendance_students', 'attendance_tutor',
              'registered_tutors', 'registered_students', 'dropout_tutors', 'dropout_students']

    def __init__(self, email):
        self.email = email

    def get_data(self):
        """Retrieve all dashboard data for the user."""
        conn = Database.connect()
        cursor = conn.cursor()
        cursor.execute(f"SELECT {','.join(Dashboard.FIELDS)} FROM dashboard WHERE email=?", (self.email,))
        row = cursor.fetchone()
        conn.close()
        return {Dashboard.FIELDS[i]: row[i] if row else '' for i in range(len(Dashboard.FIELDS))}

    def update_data(self, data_dict):
        """Update dashboard data based on user input."""
        conn = Database.connect()
        cursor = conn.cursor()
        cursor.execute(f'''
            UPDATE dashboard SET {','.join([f"{f}=?" for f in Dashboard.FIELDS])} WHERE email=?
        ''', (*[data_dict[f] for f in Dashboard.FIELDS], self.email))
        conn.commit()
        conn.close()

# ----------------------------------------
# WeeklySchedule Class
# ----------------------------------------
class WeeklySchedule:
    """
    Represents a user's weekly schedule.
    """

    DAYS = ['monday','tuesday','wednesday','thursday','friday','saturday','sunday']

    def __init__(self, email):
        self.email = email

    def get_data(self):
        """Retrieve weekly schedule data."""
        conn = Database.connect()
        cursor = conn.cursor()
        cursor.execute(f"SELECT {','.join(WeeklySchedule.DAYS)}, month, week FROM weekly_schedule WHERE email=?", (self.email,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {**{WeeklySchedule.DAYS[i]: row[i] for i in range(7)}, 'month': row[7], 'week': row[8]}
        return {day: '' for day in WeeklySchedule.DAYS} | {'month': '', 'week': ''}

    def update_data(self, schedule_dict):
        """Update weekly schedule data in database."""
        conn = Database.connect()
        cursor = conn.cursor()
        cursor.execute(f'''
            UPDATE weekly_schedule SET {','.join([f"{day}=?" for day in WeeklySchedule.DAYS])}, month=?, week=? WHERE email=?
        ''', (*[schedule_dict[day] for day in WeeklySchedule.DAYS], schedule_dict['month'], schedule_dict['week'], self.email))
        conn.commit()
        conn.close()

# ----------------------------------------
# Invoice Class
# ----------------------------------------
class Invoice:
    """
    Represents an invoice with all relevant details.
    """

    def __init__(self, username, invoice_no, due_date, client_name, client_email, company_name,
                 company_address, items, subtotal, tax, total, payment_method, invoice_date):
        self.username = username
        self.invoice_no = invoice_no
        self.due_date = due_date
        self.client_name = client_name
        self.client_email = client_email
        self.company_name = company_name
        self.company_address = company_address
        self.items = ",".join(items)
        self.subtotal = subtotal
        self.tax = tax
        self.total = total
        self.payment_method = payment_method
        self.invoice_date = invoice_date

    def save(self):
        """Insert invoice into the database."""
        conn = Database.connect()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO invoices (invoice_no, due_date, client_name, client_email, company_name,
                                  company_address, items, subtotal, tax, total, payment_method, invoice_date, username)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (self.invoice_no, self.due_date, self.client_name, self.client_email, self.company_name,
              self.company_address, self.items, self.subtotal, self.tax, self.total, self.payment_method, self.invoice_date, self.username))
        conn.commit()
        conn.close()

# ----------------------------------------
# Initialize Database
# ----------------------------------------
if not os.path.exists(DATABASE):
    Database.init_db()

# ----------------------------------------
# Routes
# ----------------------------------------
@app.route('/')
def index():
    """
    Home route shows the create account page.
    Clears any active session.
    """
    session.pop('username', None)
    return render_template('Create_account.html')

#Create account app route 
@app.route('/create_account', methods=['GET','POST'])
def create_account():
    """
    Handles new user account creation.
    Validates username and password, then saves user to database or session.
    """
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','').strip()
        remember = bool(request.form.get('remember'))

        if not username or not password:
            flash("Username and password cannot be empty!", "error")
            return redirect(url_for('create_account'))

        if not (6 <= len(password) <= 20):
            flash("Password must be 6-20 characterss!", "error")
            return redirect(url_for('create_account'))

        user = User(username, password)
        if remember:
            user.save()
            session['username'] = username
        session['temp_username'] = username
        session['temp_password'] = password
        flash("Account created successfully!", "success")
        return redirect(url_for('login'))
    return render_template('Create_account.html')

#Login page app route 
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles user login.
    Checks database first, then session temporary accounts.
    Sets session for logged-in user.
    """
    if request.method == 'POST':
        strUsername = request.form.get('username', '').strip()
        strPassword = request.form.get('password', '').strip()
        boolKeepLoggedIn = bool(request.form.get('keep_logged_in'))

        if not strUsername or not strPassword:
            flash("Username and password cannot be empty!", "error")
            return redirect(url_for('login'))

        user = User.get_by_username_password(strUsername, strPassword)

        # Check temporary session if not in database
        if not user:
            temp_user = session.get('temp_username')
            temp_pass = session.get('temp_password')
            if temp_user == strUsername and temp_pass == strPassword:
                user = (strUsername, strPassword)

        if user:
            session['username'] = strUsername
            session.permanent = boolKeepLoggedIn
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid username or password", "error")
            return redirect(url_for('login'))
    return render_template('Login_page.html')

#Forgot password page app route 
@app.route('/forgot-password', methods=['GET','POST'])
def forgot_password():
    """
    Allows users to reset their password.
    Validates input, checks match, updates database.
    """
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        new_password = request.form.get('new_password','').strip()
        confirm_password = request.form.get('confirm_password','').strip()

       #Existence Validation Check
        if not username or not new_password or not confirm_password:
            flash("All fields are required!", "error")
            return redirect(url_for('forgot_password'))

       #Validation check to ensure new password and confirm passwords match
        if new_password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect(url_for('forgot_password'))

       #Validation check to ensure password is between 6-20 characters 
        if not (6 <= len(new_password) <= 20):
            flash("Password must be 6-20 characters!", "error")
            return redirect(url_for('forgot_password'))

        user_data = User.get_by_username_password(username, new_password)
        if user_data:
            flash("New password cannot be same as old password", "error")
            return redirect(url_for('forgot_password'))

        User.update_password(username, new_password)
        flash("Password updated successfully!", "success")
        return redirect(url_for('login'))

    return render_template('Forgot_password.html')

#Homepage app route
@app.route('/home')
def home():
    """
    Displays the home page after login.
    """
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('Home_page.html', username=session['username'])

#About us page app route 
@app.route('/about')
def about():
    """About Us page."""
    return render_template('about_us.html')

#Services page app route 
@app.route('/services')
def services():
    """Services page."""
    return render_template('services.html')

#Locations page app route 
@app.route('/our_locations')
def our_locations():
    """Our Locations page."""
    return render_template('our_locations.html')

#Registrations page app route 
@app.route('/register', methods=['GET','POST'])
def register():
    """
    Handles new user registration.
    Saves registration, dashboard, and weekly schedule.
    """
    if request.method == 'POST':
        fullname = request.form.get('fullname','').strip()
        email = request.form.get('email','').strip()
        dob_day = request.form.get('dob_day','').strip()
        dob_month = request.form.get('dob_month','').strip()
        dob_year = request.form.get('dob_year','').strip()
        gender = request.form.get('gender','').strip()
        role = request.form.get('role','').strip()
        subjects = request.form.getlist('subject')
        locations = request.form.getlist('location')

        if not fullname or not email or not dob_day or not dob_month or not dob_year or not gender or not role or not subjects or not locations:
            flash("All fields are required!", "error")
            return redirect(url_for('register'))

        reg = Registration(fullname, email, dob_day, dob_month, dob_year, gender, role, subjects, locations)
        reg.save()
        session['username'] = email
        session.permanent = True
        flash(f"Registration successful! Welcome {fullname}", "success")
        return redirect(url_for('dashboard'))
    return render_template('registrations.html')

#Dashboard app route 
@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
    """
    Dashboard page for user.
    Shows current dashboard data and allows updates.
    """
    if 'username' not in session:
        return redirect(url_for('login'))
    dashboard = Dashboard(session['username'])
    if request.method == 'POST':
        data_dict = {field: request.form.get(field,'').strip() for field in Dashboard.FIELDS}
        if any(not v for v in data_dict.values()):
            flash("All dashboard fields are required!", "error")
            return redirect(url_for('dashboard'))
        dashboard.update_data(data_dict)
        flash("Dashboard updated successfully!", "success")
        return redirect(url_for('weekly_schedule'))
    data = dashboard.get_data()
    return render_template('dashboard.html', username=session['username'], dashboard_data=data)

#Weekly schedule page app route 
@app.route('/weekly_schedule', methods=['GET','POST'])
def weekly_schedule():
    """
    Weekly schedule page.
    Shows and updates weekly schedule for the logged-in user.
    """
    if 'username' not in session:
        return redirect(url_for('login'))
    ws = WeeklySchedule(session['username'])
    if request.method == 'POST':
        schedule_dict = {day: request.form.get(day,'').strip() for day in WeeklySchedule.DAYS}
        schedule_dict['month'] = request.form.get('month','').strip()
        schedule_dict['week'] = request.form.get('week','').strip()
        if any(not v for v in schedule_dict.values()):
            flash("All fields are required!", "error")
            return redirect(url_for('weekly_schedule'))
        ws.update_data(schedule_dict)
        flash("Weekly schedule saved!", "success")
        return redirect(url_for('view_database'))
    data = ws.get_data()
    return render_template('weekly_schedule.html', schedule_data=data)

#Invoices page app route 
@app.route('/invoices', methods=['GET', 'POST'])
def invoices():
    """
    Invoice creation page.
    Validates all fields and items before saving invoice to database.
    """
    if request.method == 'POST':
        username = session.get('username', '')
        invoice_no = request.form.get("invoice_no", '').strip()
        due_date = request.form.get("due_date", '').strip()
        client_name = request.form.get("client_name", '').strip()
        client_email = request.form.get("client_email", '').strip()
        company_name = request.form.get("company_name", '').strip()
        company_address = request.form.get("company_address", '').strip()
        subtotal = request.form.get("subtotal", '').strip()
        tax = request.form.get("tax", '').strip()
        total = request.form.get("total", '').strip()
        payment_method = request.form.get("payment_method", '').strip()
        invoice_date = request.form.get("invoice_date", '').strip()

        # Validate required fields
        required_fields = {
            "Invoice number": invoice_no,
            "Client name": client_name,
            "Client email": client_email,
            "Company name": company_name,
            "Company address": company_address,
            "Subtotal": subtotal,
            "Tax": tax,
            "Total": total,
            "Payment method": payment_method
        }
        for field_name, value in required_fields.items():
            if not value:
                flash(f"{field_name} cannot be empty!", "error")
                return redirect(url_for('invoices'))

        # Validate numeric fields
        for num_field in ["subtotal", "tax", "total"]:
            try:
                val = float(request.form.get(num_field, 0))
                if val < 0:
                    flash(f"{num_field.capitalize()} cannot be negative!", "error")
                    return redirect(url_for('invoices'))
            except ValueError:
                flash(f"{num_field.capitalize()} must be a number!", "error")
                return redirect(url_for('invoices'))

        # Process invoice items
        items = []
        for i in range(1, 11):
            desc = request.form.get(f"desc_{i}", '').strip()
            price = request.form.get(f"price_{i}", '').strip()
            if desc or price:
                if not desc or not price:
                    flash(f"Item {i} must have both description and price!", "error")
                    return redirect(url_for('invoices'))
                try:
                    fl_price = float(price)
                    if fl_price < 0:
                        flash(f"Item {i} price cannot be negative!", "error")
                        return redirect(url_for('invoices'))
                except ValueError:
                    flash(f"Item {i} price must be a number!", "error")
                    return redirect(url_for('invoices'))
                items.append(f"{desc}: {price}")

        if not items:
            flash("You must add at least one invoice item!", "error")
            return redirect(url_for('invoices'))

        # Save invoice
        try:
            inv = Invoice(
                username=username,
                invoice_no=invoice_no,
                due_date=due_date,
                client_name=client_name,
                client_email=client_email,
                company_name=company_name,
                company_address=company_address,
                items=items,
                subtotal=subtotal,
                tax=tax,
                total=total,
                payment_method=payment_method,
                invoice_date=invoice_date
            )
            inv.save()
            flash("Invoice saved successfully!", "success")
        except Exception as e:
            flash(f"Error saving invoice: {str(e)}", "error")

        return redirect(url_for('view_database'))

    # GET request: show empty invoice form
    empty_invoice = {
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
    return render_template("invoices.html", invoice=empty_invoice)

#Database app route 
@app.route('/view_database')
def view_database():
    """
    Displays all records from registrations, dashboard, weekly_schedule, and invoices tables.
    """
    conn = Database.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registrations")
    regs = cursor.fetchall()
    cursor.execute("SELECT * FROM dashboard")
    dash = cursor.fetchall()
    cursor.execute("SELECT * FROM weekly_schedule")
    sched = cursor.fetchall()
    cursor.execute("SELECT * FROM invoices")
    invs = cursor.fetchall()
    conn.close()
    return render_template("view_database.html", registrations=regs, dashboard=dash, weekly_sched=sched, invoices=invs)

# ----------------------------------------
# Run the Flask App
# ----------------------------------------
if __name__ == '__main__':
    app.run(debug=True)

