from PyQt5.QtWidgets import QApplication
from gui import HotelApp
from backend import create_tables
import sys

if __name__ == "__main__":
    create_tables()
    app = QApplication(sys.argv)
    window = HotelApp()
    window.setWindowTitle("Hotel Booking System")
    window.resize(500, 400)
    window.show()
    sys.exit(app.exec_())
