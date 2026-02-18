"""
SSD Dispatch Tracker - Main Application
Production-ready desktop application for labor assignment and management
"""
import sys
from datetime import datetime, date
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QComboBox, QDateEdit, QTextEdit, QSpinBox,
    QListWidget, QListWidgetItem, QGridLayout, QGroupBox, QScrollArea,
    QDialog, QDialogButtonBox, QSplitter
)
from PyQt5.QtCore import Qt, QTimer, QDate, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QFont

from config import Config
from database import Database
from photo_manager import PhotoManager
from csv_import import CSVImporter

class EmployeeWidget(QWidget):
    """Widget displaying employee with photo and info"""
    clicked = pyqtSignal(dict)

    def __init__(self, employee_data, photo_manager, parent=None):
        super().__init__(parent)
        self.employee_data = employee_data
        self.photo_manager = photo_manager

        self.setFixedSize(180, 220)
        self.setStyleSheet("""
            EmployeeWidget {
                background-color: white;
                border: 2px solid #ccc;
                border-radius: 8px;
            }
            EmployeeWidget:hover {
                border: 2px solid #007bff;
                background-color: #f0f8ff;
            }
        """)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # Employee photo
        photo_label = QLabel()
        photo_label.setAlignment(Qt.AlignCenter)
        pixmap = self.photo_manager.get_photo(
            self.employee_data['employee_id'],
            self.employee_data['name']
        )
        photo_label.setPixmap(pixmap)
        photo_label.setFixedSize(150, 150)
        photo_label.setScaledContents(True)
        layout.addWidget(photo_label)

        # Employee name
        name_label = QLabel(self.employee_data['name'])
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(name_label)

        # Employee ID
        id_label = QLabel(f"ID: {self.employee_data['employee_id']}")
        id_label.setAlignment(Qt.AlignCenter)
        id_label.setStyleSheet("font-size: 10px; color: #666;")
        layout.addWidget(id_label)

        self.setLayout(layout)

    def mousePressEvent(self, event):
        """Emit signal when clicked"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.employee_data)

class LaborBoardTab(QWidget):
    """Labor assignment board with drag-drop interface"""

    def __init__(self, database, photo_manager, parent=None):
        super().__init__(parent)
        self.database = database
        self.photo_manager = photo_manager
        self.current_date = date.today()

        self._setup_ui()
        self._load_today_assignments()

    def _setup_ui(self):
        main_layout = QVBoxLayout()

        # Top toolbar
        toolbar = QHBoxLayout()

        # Date selector
        toolbar.addWidget(QLabel("Shift Date:"))
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.dateChanged.connect(self._on_date_changed)
        toolbar.addWidget(self.date_edit)

        toolbar.addStretch()

        # Quick stats
        self.stats_label = QLabel("Assignments: 0")
        self.stats_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        toolbar.addWidget(self.stats_label)

        toolbar.addSpacing(20)

        # Action buttons
        btn_new_assignment = QPushButton("+ New Assignment")
        btn_new_assignment.clicked.connect(self._create_assignment)
        toolbar.addWidget(btn_new_assignment)

        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self._load_today_assignments)
        toolbar.addWidget(btn_refresh)

        main_layout.addLayout(toolbar)

        # Assignments table
        self.assignments_table = QTableWidget()
        self.assignments_table.setColumnCount(8)
        self.assignments_table.setHorizontalHeaderLabels([
            'Photo', 'Name', 'Employee ID', 'Cluster', 'Aisle',
            'Position', 'Assigned By', 'Actions'
        ])
        self.assignments_table.setAlternatingRowColors(True)
        self.assignments_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.assignments_table.verticalHeader().setDefaultSectionSize(60)

        # Set column widths
        self.assignments_table.setColumnWidth(0, 60)   # Photo
        self.assignments_table.setColumnWidth(1, 150)  # Name
        self.assignments_table.setColumnWidth(2, 100)  # ID
        self.assignments_table.setColumnWidth(3, 80)   # Cluster
        self.assignments_table.setColumnWidth(4, 60)   # Aisle
        self.assignments_table.setColumnWidth(5, 120)  # Position
        self.assignments_table.setColumnWidth(6, 120)  # Assigned By

        main_layout.addWidget(self.assignments_table)

        self.setLayout(main_layout)

    def _on_date_changed(self, qdate):
        """Handle date change"""
        self.current_date = qdate.toPyDate()
        self._load_today_assignments()

    def _load_today_assignments(self):
        """Load assignments for current date"""
        assignments = self.database.get_assignments_by_date(self.current_date)

        self.assignments_table.setRowCount(0)

        for assignment in assignments:
            row_position = self.assignments_table.rowCount()
            self.assignments_table.insertRow(row_position)

            # Photo
            photo_label = QLabel()
            pixmap = self.photo_manager.get_photo(
                assignment['employee_id'],
                assignment['name'],
                size=(50, 50)
            )
            photo_label.setPixmap(pixmap)
            photo_label.setScaledContents(True)
            photo_label.setAlignment(Qt.AlignCenter)
            self.assignments_table.setCellWidget(row_position, 0, photo_label)

            # Text fields
            self.assignments_table.setItem(row_position, 1,
                QTableWidgetItem(assignment['name']))
            self.assignments_table.setItem(row_position, 2,
                QTableWidgetItem(assignment['employee_id']))
            self.assignments_table.setItem(row_position, 3,
                QTableWidgetItem(assignment.get('cluster', '')))
            self.assignments_table.setItem(row_position, 4,
                QTableWidgetItem(str(assignment.get('aisle', ''))))
            self.assignments_table.setItem(row_position, 5,
                QTableWidgetItem(assignment.get('position_type', '')))
            self.assignments_table.setItem(row_position, 6,
                QTableWidgetItem(assignment.get('assigned_by', '')))

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(5, 5, 5, 5)

            btn_edit = QPushButton("Edit")
            btn_edit.setToolTip("Edit assignment")
            btn_edit.setMaximumWidth(40)

            btn_delete = QPushButton("Del")
            btn_delete.setToolTip("Delete assignment")
            btn_delete.setMaximumWidth(40)
            btn_delete.clicked.connect(
                lambda checked, aid=assignment['assignment_id']: self._delete_assignment(aid)
            )

            actions_layout.addWidget(btn_edit)
            actions_layout.addWidget(btn_delete)
            actions_widget.setLayout(actions_layout)

            self.assignments_table.setCellWidget(row_position, 7, actions_widget)

        # Update stats
        self.stats_label.setText(f"Assignments: {len(assignments)}")

    def _create_assignment(self):
        """Open dialog to create new assignment"""
        dialog = AssignmentDialog(self.database, self.photo_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            self._load_today_assignments()

    def _delete_assignment(self, assignment_id):
        """Delete assignment after confirmation"""
        reply = QMessageBox.question(
            self, 'Confirm Delete',
            'Are you sure you want to delete this assignment?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.database.delete_assignment(assignment_id)
            self._load_today_assignments()

class AssignmentDialog(QDialog):
    """Dialog for creating new assignments"""

    def __init__(self, database, photo_manager, parent=None):
        super().__init__(parent)
        self.database = database
        self.photo_manager = photo_manager
        self.selected_employee = None

        self.setWindowTitle("Create Assignment")
        self.setMinimumWidth(600)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()

        # Employee selection
        emp_group = QGroupBox("Select Employee")
        emp_layout = QVBoxLayout()

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter name or ID...")
        self.search_input.textChanged.connect(self._search_employees)
        search_layout.addWidget(self.search_input)
        emp_layout.addLayout(search_layout)

        self.employee_list = QListWidget()
        self.employee_list.itemClicked.connect(self._employee_selected)
        emp_layout.addWidget(self.employee_list)

        emp_group.setLayout(emp_layout)
        layout.addWidget(emp_group)

        # Assignment details
        details_group = QGroupBox("Assignment Details")
        details_layout = QGridLayout()

        details_layout.addWidget(QLabel("Cluster:"), 0, 0)
        self.cluster_combo = QComboBox()
        self.cluster_combo.addItems(Config.CLUSTERS)
        details_layout.addWidget(self.cluster_combo, 0, 1)

        details_layout.addWidget(QLabel("Aisle:"), 0, 2)
        self.aisle_spin = QSpinBox()
        self.aisle_spin.setRange(1, Config.AISLES_PER_CLUSTER)
        details_layout.addWidget(self.aisle_spin, 0, 3)

        details_layout.addWidget(QLabel("Position:"), 1, 0)
        self.position_combo = QComboBox()
        self.position_combo.addItems(Config.POSITION_TYPES)
        details_layout.addWidget(self.position_combo, 1, 1, 1, 3)

        details_layout.addWidget(QLabel("Assigned By:"), 2, 0)
        self.assigned_by_input = QLineEdit()
        self.assigned_by_input.setPlaceholderText("Your name or ID")
        details_layout.addWidget(self.assigned_by_input, 2, 1, 1, 3)

        details_layout.addWidget(QLabel("Notes:"), 3, 0)
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        details_layout.addWidget(self.notes_input, 3, 1, 1, 3)

        details_group.setLayout(details_layout)
        layout.addWidget(details_group)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._save_assignment)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

        # Load employees
        self._load_employees()

    def _load_employees(self):
        """Load active employees"""
        employees = self.database.get_all_employees()
        self.all_employees = employees
        self._display_employees(employees)

    def _display_employees(self, employees):
        """Display employees in list"""
        self.employee_list.clear()
        for emp in employees:
            item = QListWidgetItem(f"{emp['name']} (ID: {emp['employee_id']})")
            item.setData(Qt.UserRole, emp)
            self.employee_list.addItem(item)

    def _search_employees(self, text):
        """Filter employees by search text"""
        if not text:
            self._display_employees(self.all_employees)
        else:
            filtered = [
                emp for emp in self.all_employees
                if text.lower() in emp['name'].lower() or
                   text.lower() in emp['employee_id'].lower()
            ]
            self._display_employees(filtered)

    def _employee_selected(self, item):
        """Handle employee selection"""
        self.selected_employee = item.data(Qt.UserRole)

    def _save_assignment(self):
        """Save new assignment"""
        if not self.selected_employee:
            QMessageBox.warning(self, "Error", "Please select an employee")
            return

        if not self.assigned_by_input.text():
            QMessageBox.warning(self, "Error", "Please enter your name")
            return

        assignment_id = self.database.create_assignment(
            employee_id=self.selected_employee['employee_id'],
            shift_date=date.today(),
            cluster=self.cluster_combo.currentText(),
            aisle=self.aisle_spin.value(),
            position_type=self.position_combo.currentText(),
            assigned_by=self.assigned_by_input.text(),
            notes=self.notes_input.toPlainText()
        )

        if assignment_id:
            QMessageBox.information(self, "Success", "Assignment created successfully")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to create assignment")

class EmployeeRosterTab(QWidget):
    """Employee roster viewer and management"""

    def __init__(self, database, photo_manager, parent=None):
        super().__init__(parent)
        self.database = database
        self.photo_manager = photo_manager

        self._setup_ui()
        self._load_employees()

    def _setup_ui(self):
        layout = QVBoxLayout()

        # Toolbar
        toolbar = QHBoxLayout()

        toolbar.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name or ID...")
        self.search_input.textChanged.connect(self._filter_employees)
        toolbar.addWidget(self.search_input)

        toolbar.addWidget(QLabel("Shift:"))
        self.shift_filter = QComboBox()
        self.shift_filter.addItems(['All', 'DAY', 'NIGHT', 'TWILIGHT'])
        self.shift_filter.currentTextChanged.connect(self._filter_employees)
        toolbar.addWidget(self.shift_filter)

        toolbar.addStretch()

        self.count_label = QLabel("Employees: 0")
        self.count_label.setStyleSheet("font-weight: bold;")
        toolbar.addWidget(self.count_label)

        btn_import = QPushButton("Import CSV")
        btn_import.clicked.connect(self._import_csv)
        toolbar.addWidget(btn_import)

        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self._load_employees)
        toolbar.addWidget(btn_refresh)

        layout.addLayout(toolbar)

        # Employee grid (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.employee_grid_widget = QWidget()
        self.employee_grid = QGridLayout()
        self.employee_grid.setSpacing(10)
        self.employee_grid_widget.setLayout(self.employee_grid)

        scroll.setWidget(self.employee_grid_widget)
        layout.addWidget(scroll)

        self.setLayout(layout)

    def _load_employees(self):
        """Load all employees"""
        self.all_employees = self.database.get_all_employees()
        self._display_employees(self.all_employees)

    def _display_employees(self, employees):
        """Display employees in grid"""
        # Clear existing grid
        while self.employee_grid.count():
            child = self.employee_grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Add employees to grid (4 per row)
        for idx, emp in enumerate(employees):
            row = idx // 4
            col = idx % 4

            emp_widget = EmployeeWidget(emp, self.photo_manager)
            emp_widget.clicked.connect(self._employee_clicked)
            self.employee_grid.addWidget(emp_widget, row, col)

        # Update count
        self.count_label.setText(f"Employees: {len(employees)}")

    def _filter_employees(self):
        """Filter employees by search and shift"""
        filtered = self.all_employees

        # Search filter
        search_text = self.search_input.text().lower()
        if search_text:
            filtered = [
                emp for emp in filtered
                if search_text in emp['name'].lower() or
                   search_text in emp['employee_id'].lower()
            ]

        # Shift filter
        shift = self.shift_filter.currentText()
        if shift != 'All':
            filtered = [emp for emp in filtered if emp.get('shift') == shift]

        self._display_employees(filtered)

    def _employee_clicked(self, employee_data):
        """Handle employee click - show details"""
        msg = QMessageBox()
        msg.setWindowTitle(f"Employee: {employee_data['name']}")
        msg.setText(f"""
        <b>Name:</b> {employee_data['name']}<br>
        <b>ID:</b> {employee_data['employee_id']}<br>
        <b>Shift:</b> {employee_data.get('shift', 'N/A')}<br>
        <b>Status:</b> {employee_data.get('status', 'active')}<br>
        """)
        msg.exec_()

    def _import_csv(self):
        """Import employees from CSV"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Import Employee CSV", "", "CSV Files (*.csv)"
        )

        if filepath:
            importer = CSVImporter()
            employees, errors = importer.import_employees(Path(filepath))

            if errors:
                QMessageBox.warning(
                    self, "Import Errors",
                    f"Import completed with errors:\n" + "\n".join(errors[:5])
                )

            if employees:
                success, error_count = self.database.bulk_import_employees(employees)
                QMessageBox.information(
                    self, "Import Complete",
                    f"Successfully imported {success} employees\nErrors: {error_count}"
                )
                self._load_employees()

class DispatchTrackerMainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()

        # Initialize core systems
        self.database = Database()
        self.photo_manager = PhotoManager()

        self.setWindowTitle(f"{Config.APP_NAME} v{Config.VERSION}")
        self.setGeometry(100, 100, Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT)

        self._setup_ui()

        # Auto-refresh timer (every 5 seconds)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._auto_refresh)
        self.refresh_timer.start(Config.SYNC_INTERVAL_MS)

    def _setup_ui(self):
        """Setup main window UI"""
        # Central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        # Header
        header = QHBoxLayout()
        title = QLabel(Config.APP_NAME)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #007bff;")
        header.addWidget(title)

        header.addStretch()

        version_label = QLabel(f"v{Config.VERSION}")
        version_label.setStyleSheet("color: #666;")
        header.addWidget(version_label)

        layout.addLayout(header)

        # Tab widget
        self.tabs = QTabWidget()

        # Labor Board tab
        self.labor_board = LaborBoardTab(self.database, self.photo_manager)
        self.tabs.addTab(self.labor_board, "Labor Board")

        # Employee Roster tab
        self.employee_roster = EmployeeRosterTab(self.database, self.photo_manager)
        self.tabs.addTab(self.employee_roster, "Employee Roster")

        layout.addWidget(self.tabs)

        # Status bar
        self.statusBar().showMessage("Ready")

        central_widget.setLayout(layout)

    def _auto_refresh(self):
        """Auto-refresh data from database"""
        # Only refresh active tab to minimize overhead
        current_tab = self.tabs.currentWidget()

        if isinstance(current_tab, LaborBoardTab):
            current_tab._load_today_assignments()

    def closeEvent(self, event):
        """Handle application close"""
        self.database.close()
        event.accept()

def main():
    """Application entry point"""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    # Create and show main window
    window = DispatchTrackerMainWindow()
    window.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
