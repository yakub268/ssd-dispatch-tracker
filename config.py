"""
SSD Dispatch Tracker - Configuration Management
Handles application settings, paths, and constants
"""
import os
import json
import sys
from pathlib import Path

class Config:
    """Application configuration with automatic path detection"""

    # Application metadata
    APP_NAME = "SSD Dispatch Tracker"
    VERSION = "1.0.0"

    # Detect base directory (works for both .py and .exe)
    if getattr(sys, 'frozen', False):
        # Running as compiled .exe
        BASE_DIR = Path(sys.executable).parent
    else:
        # Running as .py script
        BASE_DIR = Path(__file__).parent

    # Database configuration
    DB_PATH = BASE_DIR / "data" / "database.db"
    DB_BACKUP_DIR = BASE_DIR / "data" / "backups"

    # Photo configuration
    PHOTO_DIR = BASE_DIR / "data" / "badge_photos"
    PHOTO_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif']
    DEFAULT_PHOTO_SIZE = (150, 150)

    # CSV import paths
    CSV_IMPORT_DIR = BASE_DIR / "data" / "csv_imports"

    # Warehouse configuration
    CLUSTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M']
    AISLES_PER_CLUSTER = 30

    # Position types
    POSITION_TYPES = [
        'DOCK',
        'STOW',
        'PICK',
        'PACK',
        'SHIP_CLERK',
        'PROBLEM_SOLVE',
        'WATER_SPIDER',
        'QUALITY',
        'LEADERSHIP'
    ]

    # Shift types
    SHIFTS = ['DAY', 'NIGHT', 'TWILIGHT']

    # Training levels
    TRAINING_LEVELS = ['LC1', 'LC2', 'LC3', 'AMBASSADOR', 'TRAINER']

    # Sync configuration
    SYNC_INTERVAL_MS = 5000  # Check for DB changes every 5 seconds
    DB_BUSY_TIMEOUT_MS = 5000  # Wait up to 5 seconds for DB lock

    # UI configuration
    WINDOW_WIDTH = 1400
    WINDOW_HEIGHT = 900
    PHOTO_CACHE_SIZE = 500  # Cache up to 500 photos in memory

    @classmethod
    def ensure_directories(cls):
        """Create required directories if they don't exist"""
        directories = [
            cls.DB_BACKUP_DIR,
            cls.CSV_IMPORT_DIR,
            cls.PHOTO_DIR
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def load_custom_config(cls):
        """Load custom configuration from config.json if exists"""
        config_file = cls.BASE_DIR / "config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    custom_config = json.load(f)
                    # Override defaults with custom values
                    for key, value in custom_config.items():
                        if hasattr(cls, key):
                            setattr(cls, key, value)
            except Exception as e:
                print(f"Error loading custom config: {e}")

    @classmethod
    def save_config(cls, config_dict):
        """Save custom configuration to config.json"""
        config_file = cls.BASE_DIR / "config.json"
        try:
            with open(config_file, 'w') as f:
                json.dump(config_dict, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

# Initialize configuration on import
Config.ensure_directories()
Config.load_custom_config()
