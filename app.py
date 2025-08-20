from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.permanent_session_lifetime = timedelta(days=7)

# Fake "database"
users = {
    "admin": "password123",
    "user": "pass456"
}

# DEFAULT route → redirect to Create Account page
@app.route('/')
def index():
    session.pop('username', None)  # optional: clear any existing login session
    return render_template('Create_account.html')

@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember')

        # Check if the exact combination already exists
        if username in users and users[username] == password:
            flash('This account already exists!')
            return redirect(url_for('create_account'))

        # Save/update the user in the fake DB
        users[username] = password

        # Optional: remember username in session
        if remember:
            session['username'] = username

        flash('Account created successfully! Please log in.')
        return redirect(url_for('login'))

    return render_template('Create_account.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        keep_logged_in = request.form.get('keep_logged_in')

        if username in users and users[username] == password:
            session['username'] = username
            session.permanent = bool(keep_logged_in)  # "Remember me" sets session permanent
            flash('Logged in successfully!')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')
            return redirect(url_for('login'))

    return render_template('Login_page.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        # You can add logic here to send a password reset email
        flash(f'Password reset instructions sent to {email}', 'info')
        return redirect(url_for('login'))  # <-- This sends the user back to login
    return render_template('Forgot_password.html')


@app.route('/home')
def home():
    if 'username' in session:
        return render_template('Home_page.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        dob_day = request.form.get('dob_day')
        dob_month = request.form.get('dob_month')
        dob_year = request.form.get('dob_year')
        gender = request.form.get('gender')

        # For simplicity, use the email as username and a default password
        username = email
        password = 'defaultpassword'  # you could let user set this in the form if you want

        # Save to fake DB
        users[username] = password

        # Automatically log the user in
        session['username'] = username
        session.permanent = True  # keeps them logged in

        flash(f'Registration successful! Welcome, {fullname}!')
        return redirect(url_for('dashboard'))  # redirect to dashboard after registration

    return render_template('registrations.html')

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template('dashboard.html', username=session['username'])
    return redirect(url_for('login'))

# NEW About Us page route
@app.route('/about')
def about():
    return render_template('about_us.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/our_locations')
def our_locations():
    return render_template('our_locations.html')

@app.route('/weekly_schedule')
def weekly_schedule():
    return render_template('weekly_schedule.html')

@app.route('/invoices')
def invoicing():
    return render_template('invoices.html')


if __name__ == '__main__':
    app.run(debug=True)
