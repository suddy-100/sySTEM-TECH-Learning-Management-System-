import sqlite3
import os

DATABASE = "site.db"

# Remove old DB if it exists
if os.path.exists(DATABASE):
    os.remove(DATABASE)
    print("Old site.db removed.")

# Connect and create tables
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
print("Fresh site.db created successfully with all tables!")
