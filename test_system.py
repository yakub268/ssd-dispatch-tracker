"""
SSD Dispatch Tracker - System Test Utility
Comprehensive testing and validation of all system components
Run this to verify installation and diagnose issues
"""
import sys
from pathlib import Path
from datetime import datetime

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    """Print formatted header"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text:^60}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_success(text):
    """Print success message"""
    print(f"{GREEN}OK{RESET} {text}")

def print_error(text):
    """Print error message"""
    print(f"{RED}FAIL{RESET} {text}")

def print_warning(text):
    """Print warning message"""
    print(f"{YELLOW}WARN{RESET} {text}")

def test_python_version():
    """Test Python version"""
    print_header("Python Environment")

    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    if version.major >= 3 and version.minor >= 8:
        print_success(f"Python {version_str} (compatible)")
        return True
    else:
        print_error(f"Python {version_str} (requires 3.8+)")
        return False

def test_dependencies():
    """Test required Python packages"""
    print_header("Python Dependencies")

    packages = {
        'PyQt5': 'PyQt5',
        'pandas': 'pandas',
        'PIL': 'Pillow',
        'sqlite3': 'sqlite3 (built-in)'
    }

    all_ok = True

    for package, display_name in packages.items():
        try:
            __import__(package)
            print_success(f"{display_name} - installed")
        except ImportError:
            print_error(f"{display_name} - MISSING")
            all_ok = False

    return all_ok

def test_file_structure():
    """Test file structure"""
    print_header("File Structure")

    required_files = [
        'config.py',
        'database.py',
        'photo_manager.py',
        'csv_import.py',
        'main.py'
    ]

    all_ok = True

    for filename in required_files:
        filepath = Path(filename)
        if filepath.exists():
            size = filepath.stat().st_size
            print_success(f"{filename} - {size:,} bytes")
        else:
            print_error(f"{filename} - NOT FOUND")
            all_ok = False

    return all_ok

def test_photo_directory():
    """Test badge photo directory"""
    print_header("Badge Photo Directory")

    from config import Config
    photo_dir = Config.PHOTO_DIR

    if not photo_dir.exists():
        print_warning(f"Photo directory not found: {photo_dir}")
        print_warning("Create ./data/badge_photos/ and add employee photos")
        return False

    # Count photos by extension
    extensions = ['.jpg', '.jpeg', '.png', '.gif']
    total_photos = 0

    for ext in extensions:
        count = len(list(photo_dir.glob(f'*{ext}')))
        if count > 0:
            total_photos += count
            print_success(f"{count} {ext} files found")

    print(f"\n{BLUE}Total photos:{RESET} {total_photos}")

    if total_photos == 0:
        print_warning("No photos found - will use initials fallback")
    else:
        print_success(f"Photo directory operational ({total_photos} photos)")

    return True

def test_database():
    """Test database initialization"""
    print_header("Database System")

    try:
        from database import Database

        db = Database()
        print_success("Database connection established")

        # Test basic operations
        employees = db.get_all_employees()
        print_success(f"Query successful - {len(employees)} employees in database")

        # Test WAL mode
        cursor = db.connection.cursor()
        cursor.execute("PRAGMA journal_mode")
        mode = cursor.fetchone()[0]

        if mode == 'wal':
            print_success("WAL mode enabled (multi-user safe)")
        else:
            print_warning(f"Journal mode: {mode} (WAL recommended)")

        db.close()
        return True

    except Exception as e:
        print_error(f"Database test failed: {str(e)}")
        return False

def test_photo_manager():
    """Test photo management system"""
    print_header("Photo Management System")

    try:
        from photo_manager import PhotoManager

        pm = PhotoManager()
        print_success("PhotoManager initialized")

        # Test cache
        stats = pm.get_cache_stats()
        print_success(f"Cache capacity: {stats['max_size']} photos")
        print_success(f"Cache usage: {stats['usage_percent']:.1f}%")

        # Test photo generation (initials fallback)
        from PyQt5.QtGui import QPixmap
        pixmap = pm.get_photo('TEST123', 'Test User', size=(100, 100))

        if isinstance(pixmap, QPixmap):
            print_success("Photo generation functional")
        else:
            print_error("Photo generation failed")
            return False

        return True

    except Exception as e:
        print_error(f"PhotoManager test failed: {str(e)}")
        return False

def test_csv_import():
    """Test CSV import system"""
    print_header("CSV Import System")

    try:
        from csv_import import CSVImporter

        importer = CSVImporter()
        print_success("CSVImporter initialized")

        # Check if pandas is available
        try:
            import pandas
            print_success("pandas available (enhanced CSV processing)")
        except ImportError:
            print_warning("pandas not available (using standard csv module)")

        return True

    except Exception as e:
        print_error(f"CSV import test failed: {str(e)}")
        return False

def test_ui_framework():
    """Test PyQt5 UI framework"""
    print_header("UI Framework")

    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt

        print_success("PyQt5 core imported successfully")

        # Test application creation (non-GUI)
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        print_success("QApplication instantiation successful")

        return True

    except Exception as e:
        print_error(f"UI framework test failed: {str(e)}")
        return False

def run_comprehensive_test():
    """Run all tests"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{'SSD DISPATCH TRACKER - SYSTEM TEST':^60}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"\n{YELLOW}Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}\n")

    # Run all tests
    results = {
        'Python Version': test_python_version(),
        'Dependencies': test_dependencies(),
        'File Structure': test_file_structure(),
        'Photo Directory': test_photo_directory(),
        'Database System': test_database(),
        'Photo Manager': test_photo_manager(),
        'CSV Import': test_csv_import(),
        'UI Framework': test_ui_framework()
    }

    # Summary
    print_header("Test Summary")

    passed = sum(results.values())
    total = len(results)

    for test_name, passed_test in results.items():
        if passed_test:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")

    print(f"\n{BLUE}{'─'*60}{RESET}")

    if passed == total:
        print(f"\n{GREEN}ALL TESTS PASSED ({passed}/{total}){RESET}")
        print(f"\n{GREEN}System is ready for use!{RESET}")
        return 0
    else:
        print(f"\n{YELLOW}{passed}/{total} tests passed{RESET}")
        print(f"\n{YELLOW}Review failed tests and install missing dependencies{RESET}")
        return 1

if __name__ == '__main__':
    exit_code = run_comprehensive_test()

    print(f"\n{BLUE}{'─'*60}{RESET}\n")

    if exit_code == 0:
        print(f"{GREEN}Next steps:{RESET}")
        print("  1. Launch application: python main.py")
        print("  2. Add employee photos to: ./data/badge_photos/")
        print("  3. Import employees via CSV from the Employee Roster tab")
    else:
        print(f"{YELLOW}Fix issues above, then run test again{RESET}")

    print()
    sys.exit(exit_code)
