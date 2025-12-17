"""
Authentication module handling user registration, login, and session management.
Supports both online and offline authentication with session persistence.
"""

import json
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
from config import Config
from database import DatabaseManager


class AuthManager:
    """
    Handles user authentication and session management.
    Sessions persist locally for offline access.
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self._current_user: Optional[Dict[str, Any]] = None
        self._session_data: Optional[Dict[str, Any]] = None
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def register(self, username: str, password: str) -> tuple[bool, str]:
        """
        Register a new user.
        Returns (success, message) tuple.
        """
        # Validate input
        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters"
        
        if not password or len(password) < 6:
            return False, "Password must be at least 6 characters"
        
        # Check if username exists
        existing = self.db.get_user_by_username(username)
        if existing:
            return False, "Username already exists"
        
        # Create user
        password_hash = self._hash_password(password)
        user_id = self.db.create_user(username, password_hash)
        
        if user_id:
            return True, "Registration successful"
        return False, "Registration failed"
    
    def login(self, username: str, password: str) -> tuple[bool, str]:
        """
        Authenticate user and create session.
        Returns (success, message) tuple.
        """
        user = self.db.get_user_by_username(username)
        
        if not user:
            return False, "Invalid username or password"
        
        if not self._verify_password(password, user["password_hash"]):
            return False, "Invalid username or password"
        
        # Create session
        self._current_user = user
        self._create_session(user)
        
        # Sync data if online
        if self.db.is_online:
            self.db.full_sync(user["id"])
        
        return True, "Login successful"
    
    def logout(self) -> None:
        """Log out current user and clear session."""
        self._current_user = None
        self._session_data = None
        self._clear_session_file()
    
    def _create_session(self, user: Dict[str, Any]) -> None:
        """Create and persist a session for the user."""
        expiry = datetime.utcnow() + timedelta(days=Config.SESSION_EXPIRY_DAYS)
        
        self._session_data = {
            "user_id": user["id"],
            "username": user["username"],
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expiry.isoformat()
        }
        
        self._save_session_file()
    
    def _save_session_file(self) -> None:
        """Save session data to file for persistence."""
        if self._session_data:
            with open(Config.SESSION_FILE, 'w') as f:
                json.dump(self._session_data, f)
    
    def _load_session_file(self) -> Optional[Dict[str, Any]]:
        """Load session data from file."""
        if not Config.SESSION_FILE.exists():
            return None
        
        try:
            with open(Config.SESSION_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    
    def _clear_session_file(self) -> None:
        """Remove session file."""
        if Config.SESSION_FILE.exists():
            Config.SESSION_FILE.unlink()
    
    def restore_session(self) -> bool:
        """
        Attempt to restore a previous session.
        Returns True if session was restored successfully.
        """
        session = self._load_session_file()
        
        if not session:
            return False
        
        # Check if session is expired
        expires_at = datetime.fromisoformat(session["expires_at"])
        if datetime.utcnow() > expires_at:
            self._clear_session_file()
            return False
        
        # Verify user still exists
        user = self.db.get_user_by_id(session["user_id"])
        if not user:
            self._clear_session_file()
            return False
        
        # Restore session
        self._current_user = user
        self._session_data = session
        
        return True
    
    @property
    def is_authenticated(self) -> bool:
        """Check if a user is currently authenticated."""
        return self._current_user is not None
    
    @property
    def current_user(self) -> Optional[Dict[str, Any]]:
        """Get the currently authenticated user."""
        return self._current_user
    
    @property
    def user_id(self) -> Optional[str]:
        """Get the current user's ID."""
        return self._current_user["id"] if self._current_user else None
    
    @property
    def username(self) -> Optional[str]:
        """Get the current user's username."""
        return self._current_user["username"] if self._current_user else None
