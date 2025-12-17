"""
Configuration module for the Pet Manager application.
Handles environment variables and application settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration settings."""
    
    # Base directory for the application
    BASE_DIR = Path(__file__).parent
    
    # Local SQLite database path (for offline storage)
    LOCAL_DB_PATH = BASE_DIR / "local_pets.db"
    
    # Turso remote database configuration
    TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL", "")
    TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "")
    
    # Session settings
    SESSION_FILE = BASE_DIR / "session.json"
    SESSION_EXPIRY_DAYS = 7
    
    # Sync settings
    SYNC_INTERVAL_SECONDS = 30  # Auto-sync interval when online
    
    @classmethod
    def is_remote_configured(cls) -> bool:
        """Check if remote Turso database is configured."""
        return bool(cls.TURSO_DATABASE_URL and cls.TURSO_AUTH_TOKEN)
