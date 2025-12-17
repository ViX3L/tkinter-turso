"""
Main application controller for Pet Manager.
Coordinates between UI views, authentication, and database operations.
"""

import tkinter as tk
from typing import Optional, Dict, Any, List
from config import Config
from database import DatabaseManager
from auth import AuthManager
from ui.styles import COLORS, DIMENSIONS
from ui.views import LoginView, DashboardView


class PetManagerApp:
    """
    Main application class that manages the application lifecycle,
    view navigation, and coordinates between components.
    """
    
    def __init__(self):
        # Initialize core components
        self._db = DatabaseManager()
        self._auth = AuthManager(self._db)
        
        # Set up main window
        self._root = tk.Tk()
        self._root.title("Pet Manager")
        self._root.geometry(f"{DIMENSIONS['window_min_width']}x{DIMENSIONS['window_min_height']}")
        self._root.minsize(DIMENSIONS["window_min_width"], DIMENSIONS["window_min_height"])
        self._root.configure(bg=COLORS["bg"])
        
        # Center window on screen
        self._center_window()
        
        # Initialize views
        self._current_view: Optional[tk.Frame] = None
        self._login_view: Optional[LoginView] = None
        self._dashboard_view: Optional[DashboardView] = None
        
        # Set up auto-sync timer
        self._sync_timer_id = None
        
        # Handle window close
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Try to restore session, otherwise show login
        if self._auth.restore_session():
            self._show_dashboard()
        else:
            self._show_login()
    
    def _center_window(self):
        """Center the window on the screen."""
        self._root.update_idletasks()
        width = self._root.winfo_width()
        height = self._root.winfo_height()
        x = (self._root.winfo_screenwidth() // 2) - (width // 2)
        y = (self._root.winfo_screenheight() // 2) - (height // 2)
        self._root.geometry(f"+{x}+{y}")
    
    def _show_view(self, view: tk.Frame):
        """Switch to a different view."""
        if self._current_view:
            self._current_view.pack_forget()
        
        view.pack(fill=tk.BOTH, expand=True)
        self._current_view = view
    
    def _show_login(self):
        """Show the login view."""
        if not self._login_view:
            self._login_view = LoginView(
                self._root,
                on_login=self._handle_login,
                on_register=self._handle_register
            )
        else:
            self._login_view.clear()
        
        self._show_view(self._login_view)
        self._stop_auto_sync()
    
    def _show_dashboard(self):
        """Show the dashboard view."""
        if not self._dashboard_view:
            self._dashboard_view = DashboardView(self._root, controller=self)
        
        self._dashboard_view.set_username(self._auth.username or "User")
        self._dashboard_view.update_status()
        self._dashboard_view.refresh_pets()
        
        self._show_view(self._dashboard_view)
        self._start_auto_sync()
    
    # ==================== AUTH HANDLERS ====================
    
    def _handle_login(self, username: str, password: str) -> tuple[bool, str]:
        """Handle login attempt."""
        success, message = self._auth.login(username, password)
        if success:
            self._show_dashboard()
        return success, message
    
    def _handle_register(self, username: str, password: str) -> tuple[bool, str]:
        """Handle registration attempt."""
        return self._auth.register(username, password)
    
    def logout(self):
        """Log out the current user."""
        self._auth.logout()
        if self._dashboard_view:
            self._dashboard_view.reset()
        self._show_login()
    
    # ==================== PET OPERATIONS ====================
    
    def get_pets(self) -> List[Dict[str, Any]]:
        """Get all pets for the current user."""
        if not self._auth.user_id:
            return []
        return self._db.get_pets_by_user(self._auth.user_id)
    
    def get_pet(self, pet_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific pet by ID."""
        return self._db.get_pet_by_id(pet_id)
    
    def add_pet(self, data: Dict[str, Any]) -> bool:
        """Add a new pet."""
        if not self._auth.user_id:
            return False
        
        pet_id = self._db.create_pet(
            user_id=self._auth.user_id,
            name=data.get("name", ""),
            species=data.get("species", ""),
            breed=data.get("breed", ""),
            age=data.get("age", 0),
            weight=data.get("weight", 0.0),
            notes=data.get("notes", "")
        )
        return pet_id is not None
    
    def update_pet(self, pet_id: str, data: Dict[str, Any]) -> bool:
        """Update an existing pet."""
        return self._db.update_pet(pet_id, **data)
    
    def delete_pet(self, pet_id: str) -> bool:
        """Delete a pet."""
        return self._db.delete_pet(pet_id)
    
    # ==================== SYNC OPERATIONS ====================
    
    def sync(self) -> Dict[str, Any]:
        """Perform a full sync."""
        if not self._auth.user_id:
            return {"is_online": False}
        return self._db.full_sync(self._auth.user_id)
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status."""
        return self._db.get_sync_status()
    
    def _start_auto_sync(self):
        """Start automatic sync timer."""
        self._do_auto_sync()
    
    def _do_auto_sync(self):
        """Perform auto sync and schedule next."""
        if self._auth.is_authenticated:
            # Check connection and sync if online
            if self._db.check_connection():
                self._db.sync_all_pending()
            
            # Update status in dashboard
            if self._dashboard_view:
                self._dashboard_view.update_status()
        
        # Schedule next sync
        self._sync_timer_id = self._root.after(
            Config.SYNC_INTERVAL_SECONDS * 1000,
            self._do_auto_sync
        )
    
    def _stop_auto_sync(self):
        """Stop automatic sync timer."""
        if self._sync_timer_id:
            self._root.after_cancel(self._sync_timer_id)
            self._sync_timer_id = None
    
    # ==================== LIFECYCLE ====================
    
    def _on_close(self):
        """Handle application close."""
        self._stop_auto_sync()
        self._db.close()
        self._root.destroy()
    
    def run(self):
        """Start the application main loop."""
        self._root.mainloop()
