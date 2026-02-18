# SSD Dispatch Tracker

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15%2B-green)
![SQLite](https://img.shields.io/badge/SQLite-WAL%20mode-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

Real-time dispatch operations system for high-volume logistics facilities. Manages driver assignments, cluster-based labor allocation, and badge photo tracking across multi-shift operations.

## Features

- **PyQt5 desktop GUI** — responsive labor board with per-shift date navigation and live assignment table
- **SQLite WAL mode** — multi-user concurrent reads without blocking writes; auto-backup support
- **Badge photo management** — loads photos from disk with FIFO LRU cache (500 entries); generates initials fallback when photo is missing
- **CSV bulk import** — auto-detects file type from headers; supports both pandas and stdlib csv; imports employees and training certifications
- **Multi-user safe** — WAL journal mode + configurable busy timeout for shared network drives
- **Cluster-based assignment** — 13 clusters (A–M), 30 aisles per cluster, 9 position types (DOCK, STOW, PICK, PACK, SHIP_CLERK, PROBLEM_SOLVE, WATER_SPIDER, QUALITY, LEADERSHIP)
- **Certification tracking** — LC1/LC2/LC3/AMBASSADOR/TRAINER levels with expiration and trainer attribution
- **Assignment history** — rotation tracking with duration logging per position
- **5-second auto-refresh** — active tab polls database for changes without blocking UI

## Screenshots

_Screenshots coming soon._

## Setup

### Requirements

- Python 3.8+
- Windows, macOS, or Linux

### Install

```bash
git clone https://github.com/yakub268/ssd-dispatch-tracker.git
cd ssd-dispatch-tracker
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

### Verify installation

```bash
python test_system.py
```

### Add employee photos

Place badge photos in `./data/badge_photos/` named by employee ID (e.g., `EMP001.jpg`). Supported formats: `.jpg`, `.jpeg`, `.png`, `.gif`. If no photo is found, the app generates an initials placeholder automatically.

### Import employees

Use the **Employee Roster** tab → **Import CSV** button. Required columns: `employee_id`, `name`. Optional: `shift`, `hire_date`, `status`, `photo_path`.

### Custom configuration

Override defaults by creating a `config.json` file in the application directory:

```json
{
    "PHOTO_DIR": "/path/to/photos",
    "SYNC_INTERVAL_MS": 10000
}
```

## Architecture

| Module | Purpose |
|--------|---------|
| `main.py` | PyQt5 application entry point; `DispatchTrackerMainWindow`, `LaborBoardTab`, `EmployeeRosterTab`, `AssignmentDialog`, `EmployeeWidget` |
| `database.py` | SQLite manager; WAL mode; CRUD for employees, assignments, certifications, assignment history, metadata; bulk import; analytics queries |
| `config.py` | Centralized config; auto-detects base directory for `.py` and compiled `.exe`; loads overrides from `config.json` |
| `photo_manager.py` | Badge photo loader with PIL (high-quality) or Qt (fallback) resizing; FIFO cache; initials generator |
| `csv_import.py` | CSV ingestion with header auto-detection; pandas or stdlib csv; employee and training certification import; export to CSV; import log |
| `test_system.py` | Standalone test runner; validates Python version, dependencies, file structure, photo directory, database, photo manager, CSV importer, and Qt framework |

## Data directory layout

```
data/
  database.db          # SQLite database (WAL mode)
  backups/             # Timestamped database backups
  badge_photos/        # Employee badge photos (ID.jpg)
  csv_imports/
    import_log.json    # Last 100 import operations
```

## License

MIT License — see [LICENSE](LICENSE) for details.
