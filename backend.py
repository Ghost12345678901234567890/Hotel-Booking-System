import sqlite3
import hashlib
from datetime import datetime

DB_NAME = 'hotel.db'

def connect():
    return sqlite3.connect(DB_NAME)

def create_tables():
    conn = connect()
    cursor = conn.cursor()

    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0  -- 1 = admin, 0 = user
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            room_id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_type TEXT NOT NULL,
            room_number TEXT NOT NULL UNIQUE,
            price REAL NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (room_id) REFERENCES rooms(room_id)
        )
    ''')

    conn.commit()
    conn.close()

def add_customer(first_name, last_name):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO customers (first_name, last_name) VALUES (?, ?)', (first_name, last_name))
    conn.commit()
    conn.close()


def check_availability(room_type, start_date, end_date):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT r.room_id, r.room_number, r.price FROM rooms r
        WHERE r.room_type = ?
        AND r.room_id NOT IN (
            SELECT room_id FROM reservations
            WHERE NOT (
                date(end_date) <= date(?) OR date(start_date) >= date(?)
            )
        )
    ''', (room_type, start_date, end_date))

    available = cursor.fetchall()
    conn.close()
    return available


def make_reservation(customer_id, room_id, start_date, end_date):
    conn = connect()
    cursor = conn.cursor()

    # Check for overlapping reservation
    cursor.execute('''
        SELECT * FROM reservations
        WHERE room_id = ? AND NOT (
            date(end_date) <= date(?) OR date(start_date) >= date(?)
        )
    ''', (room_id, start_date, end_date))

    if cursor.fetchone():
        conn.close()
        return False  # Room not available

    cursor.execute('''
        INSERT INTO reservations (customer_id, room_id, start_date, end_date)
        VALUES (?, ?, ?, ?)
    ''', (customer_id, room_id, start_date, end_date))

    conn.commit()
    conn.close()
    return True


def cancel_reservation(reservation_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM reservations WHERE reservation_id = ?', (reservation_id,))
    conn.commit()
    conn.close()


def view_reservations(customer_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT res.reservation_id, r.room_number, r.room_type, r.price, res.start_date, res.end_date
        FROM reservations res
        JOIN rooms r ON res.room_id = r.room_id
        WHERE res.customer_id = ?
    ''', (customer_id,))

    reservations = cursor.fetchall()
    conn.close()
    return reservations


def add_room(room_type, room_number, price):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO rooms (room_type, room_number, price)
            VALUES (?, ?, ?)
        ''', (room_type, room_number, price))
        conn.commit()
        print("✅ Room added successfully.")
    except sqlite3.IntegrityError:
        print("❌ Room number already exists.")
    finally:
        conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password, is_admin=False):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (username, password, is_admin)
            VALUES (?, ?, ?)
        ''', (username, hash_password(password), int(is_admin)))
        conn.commit()
        print("✅ User registered.")
    except sqlite3.IntegrityError:
        print("❌ Username already exists.")
    finally:
        conn.close()

def login_user(username, password):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, is_admin FROM users
        WHERE username = ? AND password = ?
    ''', (username, hash_password(password)))
    result = cursor.fetchone()
    conn.close()
    return result  # Returns (user_id, is_admin) or None
