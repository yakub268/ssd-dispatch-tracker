"""
SSD Dispatch Tracker - Photo Manager
Handles loading, caching, and fallback for employee badge photos
"""
from pathlib import Path
from typing import Optional
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from PyQt5.QtGui import QPixmap, QImage, QPainter, QColor, QFont
from PyQt5.QtCore import Qt, QRect
import io

from config import Config

class PhotoManager:
    """Manage employee badge photos with caching and fallback"""

    def __init__(self):
        self.photo_cache = {}  # employee_id -> QPixmap
        self.cache_size = Config.PHOTO_CACHE_SIZE

    def get_photo(self, employee_id: str, name: str = None,
                  size: tuple = None) -> QPixmap:
        """
        Get employee photo as QPixmap
        Returns cached photo, loads from disk, or generates initials fallback
        """
        size = size or Config.DEFAULT_PHOTO_SIZE

        # Check cache first
        cache_key = f"{employee_id}_{size[0]}x{size[1]}"
        if cache_key in self.photo_cache:
            return self.photo_cache[cache_key]

        # Try to load from disk
        photo_path = self._find_photo(employee_id)

        if photo_path and photo_path.exists():
            pixmap = self._load_photo_from_disk(photo_path, size)
        else:
            # Generate initials fallback
            pixmap = self._generate_initials_photo(employee_id, name, size)

        # Cache the result
        self._add_to_cache(cache_key, pixmap)

        return pixmap

    def _find_photo(self, employee_id: str) -> Optional[Path]:
        """Find photo file for employee (try multiple extensions)"""
        for ext in Config.PHOTO_EXTENSIONS:
            photo_path = Config.PHOTO_DIR / f"{employee_id}{ext}"
            if photo_path.exists():
                return photo_path

        return None

    def _load_photo_from_disk(self, photo_path: Path, size: tuple) -> QPixmap:
        """Load and resize photo from disk"""
        try:
            if PIL_AVAILABLE:
                # Use PIL for better quality resizing
                img = Image.open(photo_path)
                img = img.convert('RGB')
                img.thumbnail(size, Image.Resampling.LANCZOS)

                # Convert to QPixmap
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='PNG')
                img_bytes.seek(0)

                qimage = QImage()
                qimage.loadFromData(img_bytes.read())

                return QPixmap.fromImage(qimage)
            else:
                # Direct Qt loading
                pixmap = QPixmap(str(photo_path))
                return pixmap.scaled(size[0], size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation)

        except Exception as e:
            print(f"Error loading photo {photo_path}: {e}")
            return self._generate_initials_photo(photo_path.stem, None, size)

    def _generate_initials_photo(self, employee_id: str,
                                name: str = None,
                                size: tuple = (150, 150)) -> QPixmap:
        """Generate photo with employee initials using Qt"""
        try:
            # Create pixmap
            pixmap = QPixmap(size[0], size[1])
            pixmap.fill(QColor('#2C3E50'))  # Dark blue-gray background

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            # Generate initials
            if name:
                parts = name.split()
                initials = ''.join([p[0].upper() for p in parts[:2]])
            else:
                # Use last 2 chars of employee ID
                initials = employee_id[-2:].upper() if len(employee_id) >= 2 else employee_id.upper()

            # Draw initials
            font = QFont('Arial', size[0] // 3, QFont.Bold)
            painter.setFont(font)

            # Draw shadow
            painter.setPen(QColor('#000000'))
            painter.drawText(QRect(2, 2, size[0], size[1]), Qt.AlignCenter, initials)

            # Draw text
            painter.setPen(QColor('#ECF0F1'))  # Light gray
            painter.drawText(QRect(0, 0, size[0], size[1]), Qt.AlignCenter, initials)

            painter.end()

            return pixmap

        except Exception as e:
            print(f"Error generating initials photo: {e}")
            # Return blank pixmap as last resort
            pixmap = QPixmap(size[0], size[1])
            pixmap.fill(QColor('#CCCCCC'))
            return pixmap

    def _add_to_cache(self, key: str, pixmap: QPixmap):
        """Add photo to cache, evict oldest if cache full"""
        if len(self.photo_cache) >= self.cache_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self.photo_cache))
            del self.photo_cache[oldest_key]

        self.photo_cache[key] = pixmap

    def preload_photos(self, employee_ids: list):
        """Preload photos for multiple employees (background operation)"""
        for emp_id in employee_ids:
            cache_key = f"{emp_id}_{Config.DEFAULT_PHOTO_SIZE[0]}x{Config.DEFAULT_PHOTO_SIZE[1]}"
            if cache_key not in self.photo_cache:
                self.get_photo(emp_id)

    def clear_cache(self):
        """Clear photo cache"""
        self.photo_cache.clear()

    def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        return {
            'size': len(self.photo_cache),
            'max_size': self.cache_size,
            'usage_percent': (len(self.photo_cache) / self.cache_size) * 100
        }
