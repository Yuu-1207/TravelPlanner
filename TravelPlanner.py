from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTableWidget, QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QDialog, QFormLayout, QTextEdit, QHBoxLayout
from PyQt5.QtCore import Qt
import sqlite3

class TravelPlanner(QMainWindow):
    def __init__(self):
        super().__init__()
        print("Initializing TravelPlanner application...")
        self.setWindowTitle("旅行プラン")
        self.setGeometry(100, 100, 600, 400)
        self.connection = sqlite3.connect("travel_planner.db")
        print("Connected to SQLite database.")
        self.init_db()
        self.init_ui()

    def init_db(self):
        print("Initializing database...")
        cursor = self.connection.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date TEXT NOT NULL
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS plan_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,
            detail_date TEXT NOT NULL,
            destination TEXT NOT NULL,
            address TEXT,
            notes TEXT,
            FOREIGN KEY(plan_id) REFERENCES plans(id) ON DELETE CASCADE
        )
        """)
        self.connection.commit()
        print("Database initialized.")

    def init_ui(self):
        print("Setting up the UI...")
        layout = QVBoxLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("旅行プランを入力")
        layout.addWidget(QLabel("旅行プラン:"))
        layout.addWidget(self.name_input)

        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("日付を入力 (YYYY-MM-DD)")
        layout.addWidget(QLabel("日付:"))
        layout.addWidget(self.date_input)

        add_button = QPushButton("旅行プランを追加")
        add_button.clicked.connect(self.add_plan)
        layout.addWidget(add_button)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["旅行プラン", "日付", "削除"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.cellDoubleClicked.connect(self.open_plan_details)
        layout.addWidget(self.table)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.load_plans()
        print("UI setup complete.")

    def load_plans(self):
        print("Loading plans from database...")
        cursor = self.connection.cursor()
        cursor.execute("SELECT id, name, date FROM plans ORDER BY date ASC")
        rows = cursor.fetchall()

        self.table.setRowCount(0)
        for row in rows:
            row_index = self.table.rowCount()
            self.table.insertRow(row_index)

            travel_name_item = QTableWidgetItem(row[1])
            travel_name_item.setData(Qt.UserRole, row[0])
            self.table.setItem(row_index, 0, travel_name_item)

            self.table.setItem(row_index, 1, QTableWidgetItem(row[2]))

            delete_button = QPushButton("削除")
            delete_button.clicked.connect(lambda checked, plan_id=row[0]: self.delete_plan(plan_id))

            button_widget = QWidget()
            button_layout = QHBoxLayout()
            button_layout.addWidget(delete_button)
            button_layout.setContentsMargins(0, 0, 0, 0)
            button_widget.setLayout(button_layout)

            self.table.setCellWidget(row_index, 2, button_widget)
        print(f"Loaded {len(rows)} plans.")

    def add_plan(self):
        print("Attempting to add a new travel plan...")
        name = self.name_input.text()
        date = self.date_input.text()

        if not name or not date:
            print("Input validation failed: Travel Name and Date are required.")
            QMessageBox.warning(self, "Input Error", "Travel Name and Date are required fields!")
            return

        cursor = self.connection.cursor()
        cursor.execute("INSERT INTO plans (name, date) VALUES (?, ?)", (name, date))
        self.connection.commit()
        print("New travel plan added to database.")

        self.name_input.clear()
        self.date_input.clear()
        self.load_plans()

    def delete_plan(self, plan_id):
        print(f"Attempting to delete plan with ID={plan_id}...")
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
        self.connection.commit()
        print(f"Deleted plan with ID={plan_id}.")
        self.load_plans()

    def open_plan_details(self, row, column):
        print("Opening details for selected plan...")
        if column != 0:  # Ensure only the Travel Name column triggers this
            return

        plan_id = self.table.item(row, 0).data(Qt.UserRole)
        travel_name = self.table.item(row, 0).text()

        details_dialog = QDialog(self)
        details_dialog.setWindowTitle(f"{travel_name}詳細")
        details_dialog.resize(600, 400)
        layout = QVBoxLayout()

        self.details_table = QTableWidget()
        self.details_table.setColumnCount(5)
        self.details_table.setHorizontalHeaderLabels(["日時", "予定", "場所", "メモ", "削除"])
        layout.addWidget(self.details_table)

        self.load_plan_details(plan_id)

        add_detail_button = QPushButton("プラン詳細を追加")
        add_detail_button.clicked.connect(lambda: self.add_plan_detail(plan_id))
        layout.addWidget(add_detail_button)

        details_dialog.setLayout(layout)
        details_dialog.exec_()

    def load_plan_details(self, plan_id):
        print(f"Loading details for plan ID={plan_id}...")
        cursor = self.connection.cursor()
        cursor.execute("SELECT id, detail_date, destination, address, notes FROM plan_details WHERE plan_id = ? ORDER BY detail_date ASC", (plan_id,))
        rows = cursor.fetchall()

        self.details_table.setRowCount(0)
        for row in rows:
            row_index = self.details_table.rowCount()
            self.details_table.insertRow(row_index)

            for col_index, data in enumerate(row[1:]):
                self.details_table.setItem(row_index, col_index, QTableWidgetItem(data))

            delete_button = QPushButton("削除")
            delete_button.clicked.connect(lambda checked, detail_id=row[0]: self.delete_detail(detail_id))

            button_widget = QWidget()
            button_layout = QHBoxLayout()
            button_layout.addWidget(delete_button)
            button_layout.setContentsMargins(0, 0, 0, 0)
            button_widget.setLayout(button_layout)

            self.details_table.setCellWidget(row_index, 4, button_widget)
        print(f"Loaded {len(rows)} details.")

    def delete_detail(self, detail_id):
        print(f"Attempting to delete detail with ID={detail_id}...")
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM plan_details WHERE id = ?", (detail_id,))
        self.connection.commit()
        print(f"Deleted detail with ID={detail_id}.")
        self.load_plan_details(self.table.item(self.table.currentRow(), 0).data(Qt.UserRole))

    def add_plan_detail(self, plan_id):
        print(f"Adding a new detail to plan ID={plan_id}...")

        detail_dialog = QDialog(self)
        detail_dialog.setWindowTitle("プラン詳細追加")
        detail_dialog.resize(400, 400)

        form_layout = QFormLayout()

        date_input = QLineEdit()
        date_input.setPlaceholderText("日時を入力 (MM-DD hh-mm)")
        date_input.setMinimumWidth(255)
        form_layout.addRow("日時:", date_input)

        destination_input = QLineEdit()
        destination_input.setPlaceholderText("予定を入力")
        destination_input.setMinimumWidth(255)
        form_layout.addRow("予定:", destination_input)

        address_input = QLineEdit()
        address_input.setPlaceholderText("場所を入力")
        address_input.setMinimumWidth(255)
        form_layout.addRow("場所:", address_input)

        notes_input = QTextEdit()
        notes_input.setPlaceholderText("メモを入力")
        form_layout.addRow("メモ:", notes_input)

        save_button = QPushButton("プラン詳細を保存")
        save_button.clicked.connect(lambda: self.save_plan_detail(plan_id, date_input.text(), destination_input.text(), address_input.text(), notes_input.toPlainText(), detail_dialog))
        form_layout.addWidget(save_button)

        detail_dialog.setLayout(form_layout)
        detail_dialog.exec_()

    def save_plan_detail(self, plan_id, date, destination, address, notes, dialog):
        if not date or not destination:
            QMessageBox.warning(self, "Input Error", "Date and Destination are required fields!")
            return

        cursor = self.connection.cursor()
        cursor.execute("INSERT INTO plan_details (plan_id, detail_date, destination, address, notes) VALUES (?, ?, ?, ?, ?)", (plan_id, date, destination, address, notes))
        self.connection.commit()
        print(f"Added new detail to plan ID={plan_id}.")
        self.load_plan_details(plan_id)
        dialog.accept()

if __name__ == "__main__":
    print("Starting TravelPlanner application...")
    app = QApplication([])
    window = TravelPlanner()
    window.show()
    app.exec_()
    print("Application closed.")
