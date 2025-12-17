"""
Database module handling both local (offline) and remote (Turso) database operations.
Implements sync logic between local and remote databases.
"""

import libsql_experimental as libsql
import uuid
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from config import Config


class DatabaseManager:
    """
    Manages database connections and operations for both local and remote databases.
    Supports offline-first architecture with sync capabilities.
    """
    
    def __init__(self):
        self.local_conn = None
        self.remote_conn = None
        self._is_online = False
        self._init_local_db()
        self._try_connect_remote()
    
    def _init_local_db(self) -> None:
        """Initialize local SQLite database for offline storage."""
        self.local_conn = libsql.connect(str(Config.LOCAL_DB_PATH))
        self._create_tables(self.local_conn)
    
    def _try_connect_remote(self) -> bool:
        """
        Attempt to connect to remote Turso database.
        Returns True if connection successful, False otherwise.
        """
        if not Config.is_remote_configured():
            self._is_online = False
            return False
        
        try:
            self.remote_conn = libsql.connect(
                Config.TURSO_DATABASE_URL,
                auth_token=Config.TURSO_AUTH_TOKEN
            )
            self._create_tables(self.remote_conn)
            self._is_online = True
            return True
        except Exception as e:
            print(f"Remote connection failed: {e}")
            self._is_online = False
            return False
    
    def _create_tables(self, conn) -> None:
        """Create necessary tables if they don't exist."""
        # Users table for authentication
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                is_deleted INTEGER DEFAULT 0,
                sync_status TEXT DEFAULT 'synced'
            )
        """)
        
        # Pets table for pet management
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pets (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                species TEXT NOT NULL,
                breed TEXT,
                age INTEGER,
                weight REAL,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                is_deleted INTEGER DEFAULT 0,
                sync_status TEXT DEFAULT 'synced',
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Sync log to track changes
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sync_log (
                id TEXT PRIMARY KEY,
                table_name TEXT NOT NULL,
                record_id TEXT NOT NULL,
                operation TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                synced INTEGER DEFAULT 0
            )
        """)
        
        conn.commit()
    
    @property
    def is_online(self) -> bool:
        """Check if remote database is available."""
        return self._is_online
    
    def check_connection(self) -> bool:
        """Re-check remote connection status."""
        return self._try_connect_remote()
    
    def _generate_id(self) -> str:
        """Generate a unique ID for records."""
        return str(uuid.uuid4())
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.utcnow().isoformat()
    
    def _log_change(self, table: str, record_id: str, operation: str) -> None:
        """Log a change for sync purposes."""
        self.local_conn.execute(
            """INSERT INTO sync_log (id, table_name, record_id, operation, timestamp, synced)
               VALUES (?, ?, ?, ?, ?, 0)""",
            (self._generate_id(), table, record_id, operation, self._get_timestamp())
        )
        self.local_conn.commit()

    # ==================== USER OPERATIONS ====================
    
    def create_user(self, username: str, password_hash: str) -> Optional[str]:
        """
        Create a new user in the database.
        Returns user ID if successful, None if username exists.
        """
        user_id = self._generate_id()
        timestamp = self._get_timestamp()
        
        try:
            self.local_conn.execute(
                """INSERT INTO users (id, username, password_hash, created_at, updated_at, sync_status)
                   VALUES (?, ?, ?, ?, ?, 'pending')""",
                (user_id, username, password_hash, timestamp, timestamp)
            )
            self.local_conn.commit()
            self._log_change("users", user_id, "INSERT")
            
            # Try to sync immediately if online
            if self.is_online:
                self._sync_user_to_remote(user_id)
            
            return user_id
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Retrieve user by username."""
        result = self.local_conn.execute(
            "SELECT * FROM users WHERE username = ? AND is_deleted = 0",
            (username,)
        ).fetchone()
        
        if result:
            return self._row_to_dict(result, ["id", "username", "password_hash", 
                                               "created_at", "updated_at", "is_deleted", "sync_status"])
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user by ID."""
        result = self.local_conn.execute(
            "SELECT * FROM users WHERE id = ? AND is_deleted = 0",
            (user_id,)
        ).fetchone()
        
        if result:
            return self._row_to_dict(result, ["id", "username", "password_hash",
                                               "created_at", "updated_at", "is_deleted", "sync_status"])
        return None
    
    # ==================== PET OPERATIONS ====================
    
    def create_pet(self, user_id: str, name: str, species: str, 
                   breed: str = "", age: int = 0, weight: float = 0.0, 
                   notes: str = "") -> Optional[str]:
        """Create a new pet record."""
        pet_id = self._generate_id()
        timestamp = self._get_timestamp()
        
        try:
            self.local_conn.execute(
                """INSERT INTO pets (id, user_id, name, species, breed, age, weight, 
                   notes, created_at, updated_at, sync_status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')""",
                (pet_id, user_id, name, species, breed, age, weight, notes, timestamp, timestamp)
            )
            self.local_conn.commit()
            self._log_change("pets", pet_id, "INSERT")
            
            if self.is_online:
                self._sync_pet_to_remote(pet_id)
            
            return pet_id
        except Exception as e:
            print(f"Error creating pet: {e}")
            return None
    
    def get_pets_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all pets for a specific user."""
        results = self.local_conn.execute(
            "SELECT * FROM pets WHERE user_id = ? AND is_deleted = 0 ORDER BY name",
            (user_id,)
        ).fetchall()
        
        columns = ["id", "user_id", "name", "species", "breed", "age", 
                   "weight", "notes", "created_at", "updated_at", "is_deleted", "sync_status"]
        return [self._row_to_dict(row, columns) for row in results]
    
    def get_pet_by_id(self, pet_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific pet by ID."""
        result = self.local_conn.execute(
            "SELECT * FROM pets WHERE id = ? AND is_deleted = 0",
            (pet_id,)
        ).fetchone()
        
        if result:
            columns = ["id", "user_id", "name", "species", "breed", "age",
                       "weight", "notes", "created_at", "updated_at", "is_deleted", "sync_status"]
            return self._row_to_dict(result, columns)
        return None
    
    def update_pet(self, pet_id: str, **kwargs) -> bool:
        """Update a pet record with provided fields."""
        allowed_fields = {"name", "species", "breed", "age", "weight", "notes"}
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return False
        
        updates["updated_at"] = self._get_timestamp()
        updates["sync_status"] = "pending"
        
        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [pet_id]
        
        try:
            self.local_conn.execute(
                f"UPDATE pets SET {set_clause} WHERE id = ?",
                values
            )
            self.local_conn.commit()
            self._log_change("pets", pet_id, "UPDATE")
            
            if self.is_online:
                self._sync_pet_to_remote(pet_id)
            
            return True
        except Exception as e:
            print(f"Error updating pet: {e}")
            return False
    
    def delete_pet(self, pet_id: str) -> bool:
        """Soft delete a pet record."""
        timestamp = self._get_timestamp()
        
        try:
            self.local_conn.execute(
                "UPDATE pets SET is_deleted = 1, updated_at = ?, sync_status = 'pending' WHERE id = ?",
                (timestamp, pet_id)
            )
            self.local_conn.commit()
            self._log_change("pets", pet_id, "DELETE")
            
            if self.is_online:
                self._sync_pet_to_remote(pet_id)
            
            return True
        except Exception as e:
            print(f"Error deleting pet: {e}")
            return False

    # ==================== SYNC OPERATIONS ====================
    
    def _sync_user_to_remote(self, user_id: str) -> bool:
        """Sync a single user record to remote database."""
        if not self.is_online or not self.remote_conn:
            return False
        
        # Select specific columns (excluding sync_status which we set explicitly)
        user = self.local_conn.execute(
            "SELECT id, username, password_hash, created_at, updated_at, is_deleted FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        
        if not user:
            return False
        
        try:
            self.remote_conn.execute(
                """INSERT OR REPLACE INTO users 
                   (id, username, password_hash, created_at, updated_at, is_deleted, sync_status)
                   VALUES (?, ?, ?, ?, ?, ?, 'synced')""",
                user
            )
            self.remote_conn.commit()
            
            # Mark as synced locally
            self.local_conn.execute(
                "UPDATE users SET sync_status = 'synced' WHERE id = ?",
                (user_id,)
            )
            self.local_conn.commit()
            return True
        except Exception as e:
            print(f"Error syncing user to remote: {e}")
            return False
    
    def _sync_pet_to_remote(self, pet_id: str) -> bool:
        """Sync a single pet record to remote database."""
        if not self.is_online or not self.remote_conn:
            return False
        
        # Select specific columns (excluding sync_status which we set explicitly)
        pet = self.local_conn.execute(
            """SELECT id, user_id, name, species, breed, age, weight, notes, 
               created_at, updated_at, is_deleted FROM pets WHERE id = ?""",
            (pet_id,)
        ).fetchone()
        
        if not pet:
            return False
        
        try:
            self.remote_conn.execute(
                """INSERT OR REPLACE INTO pets 
                   (id, user_id, name, species, breed, age, weight, notes, 
                    created_at, updated_at, is_deleted, sync_status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'synced')""",
                pet
            )
            self.remote_conn.commit()
            
            self.local_conn.execute(
                "UPDATE pets SET sync_status = 'synced' WHERE id = ?",
                (pet_id,)
            )
            self.local_conn.commit()
            return True
        except Exception as e:
            print(f"Error syncing pet to remote: {e}")
            return False
    
    def sync_all_pending(self) -> Dict[str, int]:
        """
        Sync all pending changes to remote database.
        Returns count of synced records by table.
        """
        if not self.check_connection():
            return {"users": 0, "pets": 0, "status": "offline"}
        
        synced = {"users": 0, "pets": 0, "status": "online"}
        
        # Sync pending users
        pending_users = self.local_conn.execute(
            "SELECT id FROM users WHERE sync_status = 'pending'"
        ).fetchall()
        
        for (user_id,) in pending_users:
            if self._sync_user_to_remote(user_id):
                synced["users"] += 1
        
        # Sync pending pets
        pending_pets = self.local_conn.execute(
            "SELECT id FROM pets WHERE sync_status = 'pending'"
        ).fetchall()
        
        for (pet_id,) in pending_pets:
            if self._sync_pet_to_remote(pet_id):
                synced["pets"] += 1
        
        return synced
    
    def pull_from_remote(self, user_id: str) -> Dict[str, int]:
        """
        Pull latest data from remote for a specific user.
        Uses last-write-wins conflict resolution.
        """
        if not self.is_online or not self.remote_conn:
            return {"pets": 0, "status": "offline"}
        
        pulled = {"pets": 0, "status": "online"}
        
        try:
            # Pull pets for this user from remote
            remote_pets = self.remote_conn.execute(
                "SELECT * FROM pets WHERE user_id = ?", (user_id,)
            ).fetchall()
            
            for pet in remote_pets:
                pet_id = pet[0]
                remote_updated = pet[9]  # updated_at column
                
                # Check if local version exists
                local_pet = self.local_conn.execute(
                    "SELECT updated_at FROM pets WHERE id = ?", (pet_id,)
                ).fetchone()
                
                # Insert or update if remote is newer
                if not local_pet or local_pet[0] < remote_updated:
                    self.local_conn.execute(
                        """INSERT OR REPLACE INTO pets 
                           (id, user_id, name, species, breed, age, weight, notes,
                            created_at, updated_at, is_deleted, sync_status)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'synced')""",
                        pet
                    )
                    pulled["pets"] += 1
            
            self.local_conn.commit()
        except Exception as e:
            print(f"Error pulling from remote: {e}")
        
        return pulled
    
    def full_sync(self, user_id: str) -> Dict[str, Any]:
        """Perform a full bidirectional sync for a user."""
        push_result = self.sync_all_pending()
        pull_result = self.pull_from_remote(user_id)
        
        return {
            "pushed": push_result,
            "pulled": pull_result,
            "is_online": self.is_online
        }
    
    # ==================== UTILITY METHODS ====================
    
    def _row_to_dict(self, row, columns: List[str]) -> Dict[str, Any]:
        """Convert a database row to a dictionary."""
        return dict(zip(columns, row))
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status information."""
        pending_users = self.local_conn.execute(
            "SELECT COUNT(*) FROM users WHERE sync_status = 'pending'"
        ).fetchone()[0]
        
        pending_pets = self.local_conn.execute(
            "SELECT COUNT(*) FROM pets WHERE sync_status = 'pending'"
        ).fetchone()[0]
        
        return {
            "is_online": self.is_online,
            "pending_users": pending_users,
            "pending_pets": pending_pets,
            "total_pending": pending_users + pending_pets
        }
    
    def close(self) -> None:
        """Close database connections."""
        if self.local_conn:
            self.local_conn.close()
        if self.remote_conn:
            self.remote_conn.close()
