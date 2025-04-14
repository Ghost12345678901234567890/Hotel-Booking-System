import sqlite3
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

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QStackedWidget, QHBoxLayout
)
import sys
import hashlib

# main.py

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



class LoginScreen(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("👤 Username:"))
        self.username_input = QLineEdit()
        layout.addWidget(self.username_input)

        layout.addWidget(QLabel("🔒 Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.handle_login)
        layout.addWidget(login_btn)

        register_btn = QPushButton("Register")
        register_btn.clicked.connect(self.show_register)
        layout.addWidget(register_btn)

        self.setLayout(layout)

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        user = login_user(username, password)

        if user:
            user_id, is_admin = user
            if is_admin:
                self.stacked_widget.setCurrentWidget(self.stacked_widget.admin_dashboard)
            else:
                self.stacked_widget.user_dashboard.set_user_id(user_id)
                self.stacked_widget.setCurrentWidget(self.stacked_widget.user_dashboard)
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")

    def show_register(self):
        self.stacked_widget.setCurrentWidget(self.stacked_widget.register_screen)


class RegisterScreen(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Username:"))
        self.username_input = QLineEdit()
        layout.addWidget(self.username_input)

        layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        self.admin_checkbox = QPushButton("Register as Admin")
        self.admin_checkbox.setCheckable(True)
        layout.addWidget(self.admin_checkbox)

        register_btn = QPushButton("Register")
        register_btn.clicked.connect(self.handle_register)
        layout.addWidget(register_btn)

        back_btn = QPushButton("Back to Login")
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.stacked_widget.login_screen))
        layout.addWidget(back_btn)

        self.setLayout(layout)

    def handle_register(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        is_admin = self.admin_checkbox.isChecked()

        if not username or not password:
            QMessageBox.warning(self, "Error", "All fields are required.")
            return

        register_user(username, password, is_admin)
        QMessageBox.information(self, "Success", "User registered successfully.")
        self.stacked_widget.setCurrentWidget(self.stacked_widget.login_screen)


class AdminDashboard(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("👑 Admin Dashboard"))
        layout.addWidget(QLabel("Features: Add Rooms, View Reservations, etc."))
        # Add actual functionality here
        self.setLayout(layout)


class UserDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.user_id = None
        layout = QVBoxLayout()
        self.label = QLabel("👤 User Dashboard")
        layout.addWidget(self.label)
        layout.addWidget(QLabel("Features: Book rooms, View/Cancel Reservations"))
        self.setLayout(layout)

    def set_user_id(self, user_id):
        self.user_id = user_id
        self.label.setText(f"👤 User Dashboard (User ID: {user_id})")


class HotelApp(QStackedWidget):
    
    def __init__(self):
        super().__init__()
        self.login_screen = LoginScreen(self)
        self.register_screen = RegisterScreen(self)
        self.admin_dashboard = AdminDashboard()
        self.user_dashboard = UserDashboard()

        self.addWidget(self.login_screen)
        self.addWidget(self.register_screen)
        self.addWidget(self.admin_dashboard)
        self.addWidget(self.user_dashboard)

        self.setCurrentWidget(self.login_screen)
class AdminDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("👑 Admin Dashboard")
        layout.addWidget(title)

        self.rooms_list = QLabel()
        layout.addWidget(self.rooms_list)

        refresh_btn = QPushButton("🔄 Refresh Room List")
        refresh_btn.clicked.connect(self.load_rooms)
        layout.addWidget(refresh_btn)

        layout.addWidget(QLabel("➕ Add New Room"))
        self.room_type = QLineEdit()
        self.room_type.setPlaceholderText("Room Type (Single, Double, etc.)")
        self.room_number = QLineEdit()
        self.room_number.setPlaceholderText("Room Number")
        self.room_price = QLineEdit()
        self.room_price.setPlaceholderText("Price per Night")

        layout.addWidget(self.room_type)
        layout.addWidget(self.room_number)
        layout.addWidget(self.room_price)

        add_btn = QPushButton("Add Room")
        add_btn.clicked.connect(self.add_room)
        layout.addWidget(add_btn)

        self.setLayout(layout)
        self.load_rooms()
        logout_btn = QPushButton("🔙 Log Out")
        logout_btn.clicked.connect(self.logout)
        layout.addWidget(logout_btn)
    
    def logout(self):
        self.user_id = None
        self.parent().setCurrentIndex(0)  # assuming LoginScreen is at index 0


    def load_rooms(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT room_number, room_type, price FROM rooms")
        rooms = cursor.fetchall()
        conn.close()

        if rooms:
            text = "\n".join([f"Room {r[0]} - {r[1]} - ${r[2]:.2f}" for r in rooms])
        else:
            text = "No rooms added yet."
        self.rooms_list.setText(text)

    def add_room(self):
        room_type = self.room_type.text().strip()
        room_number = self.room_number.text().strip()
        try:
            price = float(self.room_price.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Enter a valid price.")
            return

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO rooms (room_type, room_number, price) VALUES (?, ?, ?)",
                           (room_type, room_number, price))
            conn.commit()
            QMessageBox.information(self, "Success", "Room added successfully.")
            self.room_type.clear()
            self.room_number.clear()
            self.room_price.clear()
            self.load_rooms()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Duplicate", "Room number already exists.")
        finally:
            conn.close()
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("👑 Admin Dashboard")
        layout.addWidget(title)

        # -- Room display and adding --
        self.rooms_list = QLabel()
        layout.addWidget(self.rooms_list)

        refresh_btn = QPushButton("🔄 Refresh Room List")
        refresh_btn.clicked.connect(self.load_rooms)
        layout.addWidget(refresh_btn)

        layout.addWidget(QLabel("➕ Add New Room"))
        self.room_type = QLineEdit()
        self.room_type.setPlaceholderText("Room Type (Single, Double, etc.)")
        self.room_number = QLineEdit()
        self.room_number.setPlaceholderText("Room Number")
        self.room_price = QLineEdit()
        self.room_price.setPlaceholderText("Price per Night")

        layout.addWidget(self.room_type)
        layout.addWidget(self.room_number)
        layout.addWidget(self.room_price)

        add_btn = QPushButton("Add Room")
        add_btn.clicked.connect(self.add_room)
        layout.addWidget(add_btn)

        # -- Reservation viewing --
        layout.addWidget(QLabel("📋 All Reservations:"))
        self.reservations_label = QLabel("No reservations yet.")
        self.reservations_label.setWordWrap(True)
        layout.addWidget(self.reservations_label)

        view_res_btn = QPushButton("🔄 Refresh Reservations")
        view_res_btn.clicked.connect(self.load_reservations)
        layout.addWidget(view_res_btn)

        self.setLayout(layout)
        self.load_rooms()
        self.load_reservations()

    def load_rooms(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT room_number, room_type, price FROM rooms")
        rooms = cursor.fetchall()
        conn.close()

        if rooms:
            text = "\n".join([f"Room {r[0]} - {r[1]} - ${r[2]:.2f}" for r in rooms])
        else:
            text = "No rooms added yet."
        self.rooms_list.setText(text)

    def add_room(self):
        room_type = self.room_type.text().strip()
        room_number = self.room_number.text().strip()
        try:
            price = float(self.room_price.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Enter a valid price.")
            return

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO rooms (room_type, room_number, price) VALUES (?, ?, ?)",
                           (room_type, room_number, price))
            conn.commit()
            QMessageBox.information(self, "Success", "Room added successfully.")
            self.room_type.clear()
            self.room_number.clear()
            self.room_price.clear()
            self.load_rooms()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Duplicate", "Room number already exists.")
        finally:
            conn.close()

    def load_reservations(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT res.reservation_id, res.customer_id, rm.room_number, rm.room_type, rm.price,
                   res.start_date, res.end_date
            FROM reservations res
            JOIN rooms rm ON res.room_id = rm.room_id
        ''')
        reservations = cursor.fetchall()
        conn.close()

        if reservations:
            text = "\n".join([
                f"ResID: {r[0]} | CustID: {r[1]} | Room: {r[2]} ({r[3]}) | "
                f"${r[4]:.2f} | {r[5]} to {r[6]}"
                for r in reservations
            ])
        else:
            text = "No reservations found."

        self.reservations_label.setText(text) 
                   
class UserDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.user_id = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.label = QLabel("👤 User Dashboard")
        layout.addWidget(self.label)

        self.room_type = QLineEdit()
        self.room_type.setPlaceholderText("Enter room type to search (e.g. Single)")
        layout.addWidget(self.room_type)

        self.start_date = QLineEdit()
        self.start_date.setPlaceholderText("Start Date (YYYY-MM-DD)")
        layout.addWidget(self.start_date)

        self.end_date = QLineEdit()
        self.end_date.setPlaceholderText("End Date (YYYY-MM-DD)")
        layout.addWidget(self.end_date)

        search_btn = QPushButton("🔍 Check Availability")
        search_btn.clicked.connect(self.check_availability)
        layout.addWidget(search_btn)

        self.available_rooms = QLabel("")
        layout.addWidget(self.available_rooms)

        self.room_id_input = QLineEdit()
        self.room_id_input.setPlaceholderText("Room ID to book")
        layout.addWidget(self.room_id_input)

        book_btn = QPushButton("📅 Book Room")
        book_btn.clicked.connect(self.book_room)
        layout.addWidget(book_btn)

        self.reservation_list = QLabel("Your Reservations:")
        layout.addWidget(self.reservation_list)

        refresh_btn = QPushButton("🔄 Refresh Reservations")
        refresh_btn.clicked.connect(self.load_reservations)
        layout.addWidget(refresh_btn)

        self.cancel_input = QLineEdit()
        self.cancel_input.setPlaceholderText("Reservation ID to cancel")
        layout.addWidget(self.cancel_input)

        cancel_btn = QPushButton("❌ Cancel Reservation")
        cancel_btn.clicked.connect(self.cancel_reservation)
        layout.addWidget(cancel_btn)

        self.setLayout(layout)
        logout_btn = QPushButton("🔙 Log Out")
        logout_btn.clicked.connect(self.logout)
        layout.addWidget(logout_btn)
    
    def logout(self):
        self.user_id= None
        self.parent().setCurrentIndex(0)    


    def set_user_id(self, user_id):
        self.user_id = user_id
        self.label.setText(f"👤 User Dashboard (User ID: {user_id})")
        self.load_reservations()

    def check_availability(self):
        room_type = self.room_type.text().strip()
        start = self.start_date.text().strip()
        end = self.end_date.text().strip()

        conn = sqlite3.connect(DB_NAME)
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
        ''', (room_type, start, end))
        rooms = cursor.fetchall()
        conn.close()

        if rooms:
            text = "\n".join([f"ID: {r[0]}, Room {r[1]}, ${r[2]}" for r in rooms])
        else:
            text = "No available rooms found."
        self.available_rooms.setText(text)

    def book_room(self):
        try:
            room_id = int(self.room_id_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Enter a valid Room ID.")
            return

        start = self.start_date.text().strip()
        end = self.end_date.text().strip()

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM reservations
            WHERE room_id = ? AND NOT (
                date(end_date) <= date(?) OR date(start_date) >= date(?)
            )
        ''', (room_id, start, end))

        if cursor.fetchone():
            QMessageBox.warning(self, "Unavailable", "Room is already booked for selected dates.")
        else:
            cursor.execute('''
                INSERT INTO reservations (customer_id, room_id, start_date, end_date)
                VALUES (?, ?, ?, ?)
            ''', (self.user_id, room_id, start, end))
            conn.commit()
            QMessageBox.information(self, "Success", "Room booked!")
            self.load_reservations()
        conn.close()

    def load_reservations(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT reservation_id, room_id, start_date, end_date FROM reservations
            WHERE customer_id = ?
        ''', (self.user_id,))
        res = cursor.fetchall()
        conn.close()
        if res:
            text = "\n".join([f"ID: {r[0]}, Room: {r[1]}, {r[2]} to {r[3]}" for r in res])
        else:
            text = "You have no reservations."
        self.reservation_list.setText(text)

    def cancel_reservation(self):
        try:
            res_id = int(self.cancel_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Enter a valid Reservation ID.")
            return

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM reservations WHERE reservation_id = ? AND customer_id = ?', (res_id, self.user_id))
        conn.commit()
        conn.close()
        QMessageBox.information(self, "Cancelled", "Reservation cancelled.")
        self.load_reservations()


def launch_gui():
    app = QApplication(sys.argv)
    window = HotelApp()
    window.setWindowTitle("Hotel Booking System")
    window.resize(400, 300)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    create_tables()  # Ensure tables are created before launching GUI
    launch_gui()
    
  