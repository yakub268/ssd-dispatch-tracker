"""
SSD Dispatch Tracker - Database Management
SQLite with WAL mode for multi-user support
"""
import sqlite3
import json
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import shutil

from config import Config

class Database:
    """Database manager with WAL mode and auto-backup"""

    def __init__(self, db_path: Path = None):
        self.db_path = db_path or Config.DB_PATH
        self.connection = None
        self._initialize_database()

    def _initialize_database(self):
        """Initialize database with schema and WAL mode"""
        # Create database directory if it doesn't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
            timeout=Config.DB_BUSY_TIMEOUT_MS / 1000
        )
        self.connection.row_factory = sqlite3.Row

        # Enable WAL mode for multi-user access
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute(f"PRAGMA busy_timeout={Config.DB_BUSY_TIMEOUT_MS}")
        self.connection.execute("PRAGMA synchronous=NORMAL")

        # Create schema
        self._create_schema()

    def _create_schema(self):
        """Create database tables if they don't exist"""
        cursor = self.connection.cursor()

        # Employees table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                employee_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                photo_path TEXT,
                shift TEXT CHECK(shift IN ('DAY', 'NIGHT', 'TWILIGHT')),
                schedule TEXT,
                certifications TEXT,
                restrictions TEXT,
                hire_date DATE,
                status TEXT DEFAULT 'active' CHECK(status IN ('active', 'inactive', 'leave')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Assignments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assignments (
                assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                shift_date DATE NOT NULL,
                cluster TEXT CHECK(cluster IN ('A','B','C','D','E','F','G','H','I','J','K','L','M')),
                aisle INTEGER CHECK(aisle BETWEEN 1 AND 30),
                position_type TEXT,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                assigned_by TEXT,
                status TEXT DEFAULT 'active' CHECK(status IN ('active', 'completed', 'cancelled')),
                notes TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
            )
        """)

        # Certifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS certifications (
                cert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                process_path TEXT,
                level TEXT CHECK(level IN ('LC1', 'LC2', 'LC3', 'AMBASSADOR', 'TRAINER')),
                certified_date DATE,
                trainer_id TEXT,
                expiration_date DATE,
                status TEXT DEFAULT 'active' CHECK(status IN ('active', 'expired', 'revoked')),
                FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
            )
        """)

        # Assignment history (for rotation tracking)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assignment_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                position_type TEXT,
                cluster TEXT,
                aisle INTEGER,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                duration_minutes INTEGER,
                FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
            )
        """)

        # System metadata (for sync tracking)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_assignments_date
            ON assignments(shift_date, status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_assignments_employee
            ON assignments(employee_id, shift_date)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_certifications_employee
            ON certifications(employee_id, status)
        """)

        self.connection.commit()

    def backup_database(self) -> Path:
        """Create timestamped backup of database"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = Config.DB_BACKUP_DIR / f"database_backup_{timestamp}.db"

        try:
            shutil.copy2(self.db_path, backup_path)
            print(f"Database backed up to: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"Backup failed: {e}")
            return None

    # ==================== EMPLOYEE OPERATIONS ====================

    def add_employee(self, employee_id: str, name: str, **kwargs) -> bool:
        """Add new employee to database"""
        try:
            cursor = self.connection.cursor()

            # Prepare optional fields
            fields = ['employee_id', 'name']
            values = [employee_id, name]

            for key in ['photo_path', 'shift', 'schedule', 'certifications',
                       'restrictions', 'hire_date', 'status']:
                if key in kwargs:
                    fields.append(key)
                    values.append(kwargs[key])

            placeholders = ','.join(['?' for _ in values])
            field_names = ','.join(fields)

            cursor.execute(
                f"INSERT INTO employees ({field_names}) VALUES ({placeholders})",
                values
            )
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error adding employee {employee_id}: {e}")
            return False

    def update_employee(self, employee_id: str, **kwargs) -> bool:
        """Update employee information"""
        try:
            cursor = self.connection.cursor()

            # Build SET clause
            set_clause = ', '.join([f"{key}=?" for key in kwargs.keys()])
            set_clause += ", updated_at=CURRENT_TIMESTAMP"
            values = list(kwargs.values()) + [employee_id]

            cursor.execute(
                f"UPDATE employees SET {set_clause} WHERE employee_id=?",
                values
            )
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error updating employee {employee_id}: {e}")
            return False

    def get_employee(self, employee_id: str) -> Optional[Dict]:
        """Get employee by ID"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT * FROM employees WHERE employee_id=?",
                (employee_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            print(f"Error fetching employee {employee_id}: {e}")
            return None

    def get_all_employees(self, status: str = 'active') -> List[Dict]:
        """Get all employees, optionally filtered by status"""
        try:
            cursor = self.connection.cursor()
            if status:
                cursor.execute(
                    "SELECT * FROM employees WHERE status=? ORDER BY name",
                    (status,)
                )
            else:
                cursor.execute("SELECT * FROM employees ORDER BY name")

            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching employees: {e}")
            return []

    def search_employees(self, query: str) -> List[Dict]:
        """Search employees by name or ID"""
        try:
            cursor = self.connection.cursor()
            search_pattern = f"%{query}%"
            cursor.execute("""
                SELECT * FROM employees
                WHERE name LIKE ? OR employee_id LIKE ?
                ORDER BY name
            """, (search_pattern, search_pattern))

            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error searching employees: {e}")
            return []

    # ==================== ASSIGNMENT OPERATIONS ====================

    def create_assignment(self, employee_id: str, shift_date: date,
                         cluster: str, aisle: int, position_type: str,
                         assigned_by: str, **kwargs) -> Optional[int]:
        """Create new assignment"""
        try:
            cursor = self.connection.cursor()

            cursor.execute("""
                INSERT INTO assignments
                (employee_id, shift_date, cluster, aisle, position_type, assigned_by, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (employee_id, shift_date, cluster, aisle, position_type,
                  assigned_by, kwargs.get('notes', '')))

            self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error creating assignment: {e}")
            return None

    def update_assignment(self, assignment_id: int, **kwargs) -> bool:
        """Update assignment"""
        try:
            cursor = self.connection.cursor()

            set_clause = ', '.join([f"{key}=?" for key in kwargs.keys()])
            values = list(kwargs.values()) + [assignment_id]

            cursor.execute(
                f"UPDATE assignments SET {set_clause} WHERE assignment_id=?",
                values
            )
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error updating assignment {assignment_id}: {e}")
            return False

    def get_assignments_by_date(self, shift_date: date,
                                status: str = 'active') -> List[Dict]:
        """Get all assignments for a specific date"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT a.*, e.name, e.photo_path
                FROM assignments a
                JOIN employees e ON a.employee_id = e.employee_id
                WHERE a.shift_date = ? AND a.status = ?
                ORDER BY a.cluster, a.aisle
            """, (shift_date, status))

            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching assignments: {e}")
            return []

    def get_employee_assignments(self, employee_id: str,
                                days: int = 7) -> List[Dict]:
        """Get recent assignments for an employee"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM assignments
                WHERE employee_id = ?
                AND shift_date >= date('now', ?)
                ORDER BY shift_date DESC, assigned_at DESC
            """, (employee_id, f'-{days} days'))

            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching employee assignments: {e}")
            return []

    def delete_assignment(self, assignment_id: int) -> bool:
        """Delete assignment (or mark as cancelled)"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE assignments SET status='cancelled'
                WHERE assignment_id=?
            """, (assignment_id,))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error deleting assignment {assignment_id}: {e}")
            return False

    # ==================== CERTIFICATION OPERATIONS ====================

    def add_certification(self, employee_id: str, process_path: str,
                         level: str, certified_date: date,
                         trainer_id: str = None,
                         expiration_date: date = None) -> Optional[int]:
        """Add certification for employee"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO certifications
                (employee_id, process_path, level, certified_date, trainer_id, expiration_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (employee_id, process_path, level, certified_date,
                  trainer_id, expiration_date))

            self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error adding certification: {e}")
            return None

    def get_employee_certifications(self, employee_id: str) -> List[Dict]:
        """Get all certifications for an employee"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM certifications
                WHERE employee_id = ? AND status = 'active'
                ORDER BY certified_date DESC
            """, (employee_id,))

            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching certifications: {e}")
            return []

    def check_certification(self, employee_id: str,
                          process_path: str) -> bool:
        """Check if employee is certified for a process"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT COUNT(*) as count FROM certifications
                WHERE employee_id = ?
                AND process_path = ?
                AND status = 'active'
                AND (expiration_date IS NULL OR expiration_date > date('now'))
            """, (employee_id, process_path))

            result = cursor.fetchone()
            return result['count'] > 0
        except Exception as e:
            print(f"Error checking certification: {e}")
            return False

    # ==================== BULK IMPORT OPERATIONS ====================

    def bulk_import_employees(self, employees: List[Dict]) -> Tuple[int, int]:
        """Import multiple employees, returns (success_count, error_count)"""
        success = 0
        errors = 0

        for emp in employees:
            try:
                # Check if employee exists
                existing = self.get_employee(emp.get('employee_id'))

                if existing:
                    # Update existing employee
                    self.update_employee(emp.get('employee_id'), **emp)
                else:
                    # Add new employee
                    self.add_employee(**emp)

                success += 1
            except Exception as e:
                print(f"Error importing employee {emp.get('employee_id')}: {e}")
                errors += 1

        return (success, errors)

    def bulk_import_certifications(self, certifications: List[Dict]) -> Tuple[int, int]:
        """Import multiple certifications"""
        success = 0
        errors = 0

        for cert in certifications:
            try:
                self.add_certification(**cert)
                success += 1
            except Exception as e:
                print(f"Error importing certification: {e}")
                errors += 1

        return (success, errors)

    # ==================== ANALYTICS ====================

    def get_coverage_summary(self, shift_date: date) -> Dict:
        """Get assignment coverage summary for a date"""
        try:
            cursor = self.connection.cursor()

            # Total assignments
            cursor.execute("""
                SELECT COUNT(*) as total FROM assignments
                WHERE shift_date = ? AND status = 'active'
            """, (shift_date,))
            total = cursor.fetchone()['total']

            # Assignments by cluster
            cursor.execute("""
                SELECT cluster, COUNT(*) as count
                FROM assignments
                WHERE shift_date = ? AND status = 'active'
                GROUP BY cluster
                ORDER BY cluster
            """, (shift_date,))
            by_cluster = {row['cluster']: row['count']
                         for row in cursor.fetchall()}

            # Assignments by position type
            cursor.execute("""
                SELECT position_type, COUNT(*) as count
                FROM assignments
                WHERE shift_date = ? AND status = 'active'
                GROUP BY position_type
            """, (shift_date,))
            by_position = {row['position_type']: row['count']
                          for row in cursor.fetchall()}

            return {
                'total_assignments': total,
                'by_cluster': by_cluster,
                'by_position': by_position
            }
        except Exception as e:
            print(f"Error getting coverage summary: {e}")
            return {}

    def get_training_gaps(self) -> List[Dict]:
        """Identify employees without required certifications"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT e.employee_id, e.name, e.shift,
                       GROUP_CONCAT(DISTINCT c.process_path) as certifications
                FROM employees e
                LEFT JOIN certifications c ON e.employee_id = c.employee_id
                    AND c.status = 'active'
                WHERE e.status = 'active'
                GROUP BY e.employee_id, e.name, e.shift
            """)

            employees = [dict(row) for row in cursor.fetchall()]

            # Identify gaps (employees with few/no certifications)
            gaps = []
            for emp in employees:
                cert_count = len(emp['certifications'].split(',')) if emp['certifications'] else 0
                if cert_count < 2:  # Arbitrary threshold
                    gaps.append({
                        'employee_id': emp['employee_id'],
                        'name': emp['name'],
                        'shift': emp['shift'],
                        'certification_count': cert_count
                    })

            return gaps
        except Exception as e:
            print(f"Error getting training gaps: {e}")
            return []

    # ==================== METADATA ====================

    def set_metadata(self, key: str, value: str):
        """Set metadata value"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO metadata (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, value))
            self.connection.commit()
        except Exception as e:
            print(f"Error setting metadata {key}: {e}")

    def get_metadata(self, key: str) -> Optional[str]:
        """Get metadata value"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT value FROM metadata WHERE key=?", (key,))
            row = cursor.fetchone()
            return row['value'] if row else None
        except Exception as e:
            print(f"Error getting metadata {key}: {e}")
            return None

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
