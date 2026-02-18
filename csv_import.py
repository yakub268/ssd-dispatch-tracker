"""
SSD Dispatch Tracker - CSV Import System
Handles importing employees, training, and package data from CSV files
"""
import csv
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict, Tuple, Optional
import json

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("WARNING: pandas not available, using standard csv module")

from config import Config

class CSVImporter:
    """Handle CSV imports with auto-detection and validation"""

    # CSV file type detection patterns
    FILE_TYPE_PATTERNS = {
        'employees': ['employee_id', 'name', 'login'],
        'training': ['process_path', 'level', 'certified_date'],
        'packages': ['tracking_id', 'cluster', 'aisle'],
        'assignments': ['employee_id', 'shift_date', 'position']
    }

    def __init__(self):
        self.import_log = []

    def detect_file_type(self, filepath: Path) -> Optional[str]:
        """Auto-detect CSV file type based on headers"""
        try:
            if PANDAS_AVAILABLE:
                df = pd.read_csv(filepath, nrows=5)
                headers = [col.lower().replace(' ', '_') for col in df.columns]
            else:
                with open(filepath, 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    headers = [col.lower().replace(' ', '_') for col in next(reader)]

            # Check against patterns
            for file_type, required_cols in self.FILE_TYPE_PATTERNS.items():
                required_lower = [col.lower() for col in required_cols]
                if all(any(req in header for header in headers)
                      for req in required_lower):
                    return file_type

            return None

        except Exception as e:
            print(f"Error detecting file type: {e}")
            return None

    def import_employees(self, filepath: Path) -> Tuple[List[Dict], List[str]]:
        """
        Import employees from CSV
        Returns: (employees_list, errors_list)
        """
        employees = []
        errors = []

        try:
            if PANDAS_AVAILABLE:
                return self._import_employees_pandas(filepath)
            else:
                return self._import_employees_csv(filepath)
        except Exception as e:
            errors.append(f"File read error: {str(e)}")
            return ([], errors)

    def _import_employees_pandas(self, filepath: Path) -> Tuple[List[Dict], List[str]]:
        """Import using pandas"""
        employees = []
        errors = []

        df = pd.read_csv(filepath)
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]

        # Required columns
        required = ['employee_id', 'name']
        missing = [col for col in required if col not in df.columns]
        if missing:
            errors.append(f"Missing required columns: {missing}")
            return ([], errors)

        # Process each row
        for idx, row in df.iterrows():
            try:
                employee = {
                    'employee_id': str(row['employee_id']).strip(),
                    'name': str(row['name']).strip()
                }

                # Optional fields
                optional_mappings = {
                    'shift': 'shift',
                    'hire_date': 'hire_date',
                    'status': 'status',
                    'photo_path': 'photo_path'
                }

                for csv_col, db_col in optional_mappings.items():
                    if csv_col in df.columns and pd.notna(row[csv_col]):
                        value = row[csv_col]

                        # Handle date fields
                        if 'date' in csv_col:
                            try:
                                value = pd.to_datetime(value).date()
                            except:
                                pass

                        employee[db_col] = value

                # Handle JSON fields
                for json_field in ['schedule', 'certifications', 'restrictions']:
                    if json_field in df.columns and pd.notna(row[json_field]):
                        try:
                            if isinstance(row[json_field], str):
                                json.loads(row[json_field])
                                employee[json_field] = row[json_field]
                            else:
                                employee[json_field] = json.dumps(row[json_field])
                        except:
                            pass

                employees.append(employee)

            except Exception as e:
                errors.append(f"Row {idx+2}: {str(e)}")

        self._log_import('employees', filepath, len(employees), len(errors))
        return (employees, errors)

    def _import_employees_csv(self, filepath: Path) -> Tuple[List[Dict], List[str]]:
        """Import using standard csv module"""
        employees = []
        errors = []

        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            headers = [col.lower().replace(' ', '_') for col in reader.fieldnames]

            # Check required columns
            if 'employee_id' not in headers or 'name' not in headers:
                errors.append("Missing required columns: employee_id, name")
                return ([], errors)

            for idx, row in enumerate(reader, start=2):
                try:
                    # Normalize keys
                    row_normalized = {k.lower().replace(' ', '_'): v for k, v in row.items()}

                    employee = {
                        'employee_id': str(row_normalized.get('employee_id', '')).strip(),
                        'name': str(row_normalized.get('name', '')).strip()
                    }

                    # Add optional fields
                    for field in ['shift', 'hire_date', 'status', 'photo_path']:
                        if field in row_normalized and row_normalized[field]:
                            employee[field] = str(row_normalized[field]).strip()

                    employees.append(employee)

                except Exception as e:
                    errors.append(f"Row {idx}: {str(e)}")

        self._log_import('employees', filepath, len(employees), len(errors))
        return (employees, errors)

    def import_training(self, filepath: Path) -> Tuple[List[Dict], List[str]]:
        """
        Import training/certification data from CSV
        Returns: (certifications_list, errors_list)
        """
        certifications = []
        errors = []

        try:
            if PANDAS_AVAILABLE:
                return self._import_training_pandas(filepath)
            else:
                return self._import_training_csv(filepath)
        except Exception as e:
            errors.append(f"File read error: {str(e)}")
            return ([], errors)

    def _import_training_pandas(self, filepath: Path) -> Tuple[List[Dict], List[str]]:
        """Import training using pandas"""
        certifications = []
        errors = []

        df = pd.read_csv(filepath)
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]

        # Required columns
        required = ['employee_id', 'process_path']
        missing = [col for col in required if col not in df.columns]
        if missing:
            errors.append(f"Missing required columns: {missing}")
            return ([], errors)

        # Process each row
        for idx, row in df.iterrows():
            try:
                cert = {
                    'employee_id': str(row['employee_id']).strip(),
                    'process_path': str(row['process_path']).strip()
                }

                # Optional fields
                if 'level' in df.columns and pd.notna(row['level']):
                    cert['level'] = str(row['level']).strip()
                else:
                    cert['level'] = 'LC1'

                if 'certified_date' in df.columns and pd.notna(row['certified_date']):
                    try:
                        cert['certified_date'] = pd.to_datetime(row['certified_date']).date()
                    except:
                        cert['certified_date'] = date.today()
                else:
                    cert['certified_date'] = date.today()

                if 'trainer_id' in df.columns and pd.notna(row['trainer_id']):
                    cert['trainer_id'] = str(row['trainer_id']).strip()

                if 'expiration_date' in df.columns and pd.notna(row['expiration_date']):
                    try:
                        cert['expiration_date'] = pd.to_datetime(row['expiration_date']).date()
                    except:
                        pass

                certifications.append(cert)

            except Exception as e:
                errors.append(f"Row {idx+2}: {str(e)}")

        self._log_import('training', filepath, len(certifications), len(errors))
        return (certifications, errors)

    def _import_training_csv(self, filepath: Path) -> Tuple[List[Dict], List[str]]:
        """Import training using standard csv module"""
        certifications = []
        errors = []

        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            headers = [col.lower().replace(' ', '_') for col in reader.fieldnames]

            if 'employee_id' not in headers or 'process_path' not in headers:
                errors.append("Missing required columns")
                return ([], errors)

            for idx, row in enumerate(reader, start=2):
                try:
                    row_normalized = {k.lower().replace(' ', '_'): v for k, v in row.items()}

                    cert = {
                        'employee_id': str(row_normalized.get('employee_id', '')).strip(),
                        'process_path': str(row_normalized.get('process_path', '')).strip(),
                        'level': str(row_normalized.get('level', 'LC1')).strip(),
                        'certified_date': date.today()
                    }

                    certifications.append(cert)

                except Exception as e:
                    errors.append(f"Row {idx}: {str(e)}")

        self._log_import('training', filepath, len(certifications), len(errors))
        return (certifications, errors)

    def export_assignments(self, assignments: List[Dict],
                          output_path: Path) -> bool:
        """Export assignments to CSV"""
        try:
            if PANDAS_AVAILABLE:
                df = pd.DataFrame(assignments)
                df.to_csv(output_path, index=False)
            else:
                if not assignments:
                    return False

                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=assignments[0].keys())
                    writer.writeheader()
                    writer.writerows(assignments)

            self._log_import('assignments_export', output_path, len(assignments), 0)
            return True

        except Exception as e:
            print(f"Error exporting assignments: {e}")
            return False

    def _log_import(self, import_type: str, filepath: Path,
                   success_count: int, error_count: int):
        """Log import operation"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': import_type,
            'filepath': str(filepath),
            'success_count': success_count,
            'error_count': error_count
        }
        self.import_log.append(log_entry)

        # Write to log file
        log_file = Config.CSV_IMPORT_DIR / "import_log.json"
        try:
            existing_log = []
            if log_file.exists():
                with open(log_file, 'r') as f:
                    existing_log = json.load(f)

            existing_log.append(log_entry)
            existing_log = existing_log[-100:]  # Keep last 100

            with open(log_file, 'w') as f:
                json.dump(existing_log, f, indent=2)
        except Exception as e:
            print(f"Error writing import log: {e}")

    def get_import_log(self, limit: int = 20) -> List[Dict]:
        """Get recent import history"""
        return self.import_log[-limit:]

    def validate_csv_structure(self, filepath: Path) -> Tuple[bool, List[str]]:
        """Validate CSV file structure before import"""
        errors = []

        try:
            if PANDAS_AVAILABLE:
                df = pd.read_csv(filepath, nrows=5)

                if len(df) == 0:
                    errors.append("File is empty")

                if len(df.columns) < 2:
                    errors.append("File has too few columns (minimum 2)")

                if len(df.columns) != len(set(df.columns)):
                    errors.append("File contains duplicate column names")
            else:
                with open(filepath, 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    headers = next(reader)

                    if len(headers) < 2:
                        errors.append("File has too few columns")

                    if len(headers) != len(set(headers)):
                        errors.append("Duplicate column names")

            return (len(errors) == 0, errors)

        except Exception as e:
            errors.append(f"Cannot read file: {str(e)}")
            return (False, errors)
