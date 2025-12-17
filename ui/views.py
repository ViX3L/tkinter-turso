"""
Main view components for the Pet Manager application.
Contains login view and main dashboard view.
"""

import tkinter as tk
from typing import Callable, Optional
from ui.styles import COLORS, FONTS, PADDING, DIMENSIONS
from ui.components import StyledButton, StyledEntry, StyledLabel, StatusIndicator, DataTable
from ui.dialogs import PetDialog, confirm_dialog, show_error, show_info


class LoginView(tk.Frame):
    """Login and registration view."""
    
    def __init__(self, parent, on_login: Callable, on_register: Callable, **kwargs):
        super().__init__(parent, bg=COLORS["bg"], **kwargs)
        
        self._on_login = on_login
        self._on_register = on_register
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the login UI."""
        # Center container
        container = tk.Frame(self, bg=COLORS["card_bg"], padx=PADDING["xlarge"],
                            pady=PADDING["xlarge"])
        container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Title
        StyledLabel(container, text="🐾 Pet Manager", style="heading",
                   bg=COLORS["card_bg"]).pack(pady=(0, PADDING["large"]))
        
        StyledLabel(container, text="Sign in to manage your pets",
                   style="body", fg=COLORS["text_muted"],
                   bg=COLORS["card_bg"]).pack(pady=(0, PADDING["large"]))
        
        # Username field
        self._username_entry = StyledEntry(container, placeholder="Username",
                                           width=DIMENSIONS["entry_width"])
        self._username_entry.pack(pady=PADDING["small"], ipady=8)
        
        # Password field
        self._password_entry = StyledEntry(container, placeholder="Password",
                                           show="•", width=DIMENSIONS["entry_width"])
        self._password_entry.pack(pady=PADDING["small"], ipady=8)
        
        # Error label
        self._error_label = StyledLabel(container, text="", style="small",
                                        fg=COLORS["danger"], bg=COLORS["card_bg"])
        self._error_label.pack(pady=PADDING["small"])
        
        # Buttons
        btn_frame = tk.Frame(container, bg=COLORS["card_bg"])
        btn_frame.pack(pady=PADDING["medium"])
        
        StyledButton(btn_frame, text="Login", style="primary",
                    command=self._handle_login, width=12).pack(side=tk.LEFT,
                                                               padx=PADDING["small"])
        StyledButton(btn_frame, text="Register", style="secondary",
                    command=self._handle_register, width=12).pack(side=tk.LEFT,
                                                                   padx=PADDING["small"])
        
        # Bind Enter key
        self._password_entry.bind("<Return>", lambda e: self._handle_login())
    
    def _handle_login(self):
        """Handle login button click."""
        username = self._username_entry.get_value()
        password = self._password_entry.get_value()
        
        if not username or not password:
            self._show_error("Please enter username and password")
            return
        
        success, message = self._on_login(username, password)
        if not success:
            self._show_error(message)
    
    def _handle_register(self):
        """Handle register button click."""
        username = self._username_entry.get_value()
        password = self._password_entry.get_value()
        
        if not username or not password:
            self._show_error("Please enter username and password")
            return
        
        success, message = self._on_register(username, password)
        if success:
            self._show_error("")  # Clear error
            show_info(self, "Success", "Registration successful! You can now login.")
        else:
            self._show_error(message)
    
    def _show_error(self, message: str):
        """Display error message."""
        self._error_label.config(text=message)
    
    def clear(self):
        """Clear the form."""
        self._username_entry.delete(0, tk.END)
        self._password_entry.delete(0, tk.END)
        self._error_label.config(text="")


class DashboardView(tk.Frame):
    """Main dashboard view with pet management."""
    
    def __init__(self, parent, controller, **kwargs):
        super().__init__(parent, bg=COLORS["bg"], **kwargs)
        
        self._controller = controller
        self._selected_pet_id = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dashboard UI."""
        # Header
        self._setup_header()
        
        # Main content area
        content = tk.Frame(self, bg=COLORS["bg"], padx=PADDING["large"],
                          pady=PADDING["medium"])
        content.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Pet list
        self._setup_pet_list(content)
        
        # Right panel - Pet details
        self._setup_pet_details(content)
    
    def _setup_header(self):
        """Set up the header bar."""
        header = tk.Frame(self, bg=COLORS["primary"], padx=PADDING["medium"],
                         pady=PADDING["medium"])
        header.pack(fill=tk.X)
        
        # Title
        title_label = tk.Label(header, text="🐾 Pet Manager", font=FONTS["heading"],
                               bg=COLORS["primary"], fg=COLORS["white"])
        title_label.pack(side=tk.LEFT)
        
        # Right side - user info and controls
        right_frame = tk.Frame(header, bg=COLORS["primary"])
        right_frame.pack(side=tk.RIGHT)
        
        # Status indicator
        status_frame = tk.Frame(right_frame, bg=COLORS["primary"])
        status_frame.pack(side=tk.LEFT, padx=PADDING["medium"])
        
        self._status_indicator = StatusIndicator(status_frame)
        self._status_indicator.pack()
        
        # Sync button
        self._sync_btn = StyledButton(right_frame, text="↻ Sync", style="secondary",
                                      command=self._handle_sync)
        self._sync_btn.pack(side=tk.LEFT, padx=PADDING["small"])
        
        # User label
        self._user_label = tk.Label(right_frame, text="", font=FONTS["body"],
                                    bg=COLORS["primary"], fg=COLORS["white"])
        self._user_label.pack(side=tk.LEFT, padx=PADDING["medium"])
        
        # Logout button
        StyledButton(right_frame, text="Logout", style="danger",
                    command=self._controller.logout).pack(side=tk.LEFT)
    
    def _setup_pet_list(self, parent):
        """Set up the pet list panel."""
        list_frame = tk.Frame(parent, bg=COLORS["card_bg"], padx=PADDING["medium"],
                             pady=PADDING["medium"])
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, PADDING["medium"]))
        
        # Header with add button
        list_header = tk.Frame(list_frame, bg=COLORS["card_bg"])
        list_header.pack(fill=tk.X, pady=(0, PADDING["medium"]))
        
        StyledLabel(list_header, text="My Pets", style="subheading").pack(side=tk.LEFT)
        StyledButton(list_header, text="+ Add Pet", style="success",
                    command=self._handle_add_pet).pack(side=tk.RIGHT)
        
        # Pet table
        columns = [
            {"id": "name", "text": "Name", "width": 120},
            {"id": "species", "text": "Species", "width": 100},
            {"id": "breed", "text": "Breed", "width": 100},
            {"id": "age", "text": "Age", "width": 60, "anchor": "center"},
            {"id": "sync_status", "text": "Sync", "width": 80, "anchor": "center"}
        ]
        
        self._pet_table = DataTable(list_frame, columns=columns,
                                    on_select=self._handle_pet_select)
        self._pet_table.pack(fill=tk.BOTH, expand=True)
    
    def _setup_pet_details(self, parent):
        """Set up the pet details panel."""
        self._details_frame = tk.Frame(parent, bg=COLORS["card_bg"],
                                       padx=PADDING["large"], pady=PADDING["large"],
                                       width=300)
        self._details_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self._details_frame.pack_propagate(False)
        
        # Placeholder when no pet selected
        self._no_selection_label = StyledLabel(
            self._details_frame,
            text="Select a pet to view details",
            style="body",
            fg=COLORS["text_muted"]
        )
        self._no_selection_label.pack(expand=True)
        
        # Details container (hidden initially)
        self._details_container = tk.Frame(self._details_frame, bg=COLORS["card_bg"])
        
        # Pet name
        self._detail_name = StyledLabel(self._details_container, text="",
                                        style="heading")
        self._detail_name.pack(anchor="w", pady=(0, PADDING["medium"]))
        
        # Details grid
        details_grid = tk.Frame(self._details_container, bg=COLORS["card_bg"])
        details_grid.pack(fill=tk.X, pady=PADDING["medium"])
        
        self._detail_labels = {}
        detail_fields = ["Species", "Breed", "Age", "Weight", "Notes"]
        
        for i, field in enumerate(detail_fields):
            StyledLabel(details_grid, text=f"{field}:", style="body_bold").grid(
                row=i, column=0, sticky="nw", pady=2
            )
            self._detail_labels[field.lower()] = StyledLabel(
                details_grid, text="-", style="body", wraplength=180
            )
            self._detail_labels[field.lower()].grid(row=i, column=1, sticky="nw",
                                                     padx=(PADDING["medium"], 0), pady=2)
        
        # Action buttons
        btn_frame = tk.Frame(self._details_container, bg=COLORS["card_bg"])
        btn_frame.pack(fill=tk.X, pady=(PADDING["large"], 0))
        
        StyledButton(btn_frame, text="Edit", style="primary",
                    command=self._handle_edit_pet).pack(side=tk.LEFT, padx=(0, PADDING["small"]))
        StyledButton(btn_frame, text="Delete", style="danger",
                    command=self._handle_delete_pet).pack(side=tk.LEFT)

    # ==================== EVENT HANDLERS ====================
    
    def _handle_pet_select(self, values):
        """Handle pet selection from table."""
        if values:
            # Get pet ID from the data (we need to look it up by name)
            pets = self._controller.get_pets()
            for pet in pets:
                if pet["name"] == values[0]:  # Match by name
                    self._selected_pet_id = pet["id"]
                    self._show_pet_details(pet)
                    break
    
    def _handle_add_pet(self):
        """Handle add pet button click."""
        def on_save(data):
            if self._controller.add_pet(data):
                self.refresh_pets()
                show_info(self, "Success", "Pet added successfully!")
            else:
                show_error(self, "Error", "Failed to add pet")
        
        PetDialog(self, title="Add Pet", on_save=on_save)
    
    def _handle_edit_pet(self):
        """Handle edit pet button click."""
        if not self._selected_pet_id:
            return
        
        pet = self._controller.get_pet(self._selected_pet_id)
        if not pet:
            return
        
        def on_save(data):
            if self._controller.update_pet(self._selected_pet_id, data):
                self.refresh_pets()
                # Refresh details
                updated_pet = self._controller.get_pet(self._selected_pet_id)
                if updated_pet:
                    self._show_pet_details(updated_pet)
                show_info(self, "Success", "Pet updated successfully!")
            else:
                show_error(self, "Error", "Failed to update pet")
        
        PetDialog(self, title="Edit Pet", pet_data=pet, on_save=on_save)
    
    def _handle_delete_pet(self):
        """Handle delete pet button click."""
        if not self._selected_pet_id:
            return
        
        if confirm_dialog(self, "Confirm Delete", 
                         "Are you sure you want to delete this pet?"):
            if self._controller.delete_pet(self._selected_pet_id):
                self._selected_pet_id = None
                self._hide_pet_details()
                self.refresh_pets()
                show_info(self, "Success", "Pet deleted successfully!")
            else:
                show_error(self, "Error", "Failed to delete pet")
    
    def _handle_sync(self):
        """Handle sync button click."""
        result = self._controller.sync()
        self.update_status()
        self.refresh_pets()
        
        if result.get("is_online"):
            pushed = result.get("pushed", {})
            pulled = result.get("pulled", {})
            show_info(self, "Sync Complete", 
                     f"Pushed: {pushed.get('pets', 0)} pets\n"
                     f"Pulled: {pulled.get('pets', 0)} pets")
        else:
            show_info(self, "Offline", "Cannot sync while offline. Changes saved locally.")
    
    # ==================== UI UPDATE METHODS ====================
    
    def _show_pet_details(self, pet: dict):
        """Display pet details in the details panel."""
        self._no_selection_label.pack_forget()
        self._details_container.pack(fill=tk.BOTH, expand=True)
        
        self._detail_name.config(text=pet.get("name", ""))
        self._detail_labels["species"].config(text=pet.get("species", "-"))
        self._detail_labels["breed"].config(text=pet.get("breed", "-") or "-")
        self._detail_labels["age"].config(
            text=f"{pet.get('age', 0)} years" if pet.get("age") else "-"
        )
        self._detail_labels["weight"].config(
            text=f"{pet.get('weight', 0)} kg" if pet.get("weight") else "-"
        )
        self._detail_labels["notes"].config(text=pet.get("notes", "-") or "-")
    
    def _hide_pet_details(self):
        """Hide the pet details panel."""
        self._details_container.pack_forget()
        self._no_selection_label.pack(expand=True)
    
    def refresh_pets(self):
        """Refresh the pet list."""
        pets = self._controller.get_pets()
        
        # Format data for table
        table_data = []
        for pet in pets:
            sync_icon = "✓" if pet.get("sync_status") == "synced" else "⏳"
            table_data.append({
                "name": pet.get("name", ""),
                "species": pet.get("species", ""),
                "breed": pet.get("breed", ""),
                "age": pet.get("age", ""),
                "sync_status": sync_icon
            })
        
        self._pet_table.set_data(table_data)
    
    def update_status(self):
        """Update the connection status indicator."""
        status = self._controller.get_sync_status()
        self._status_indicator.set_status(
            status.get("is_online", False),
            status.get("total_pending", 0)
        )
    
    def set_username(self, username: str):
        """Set the displayed username."""
        self._user_label.config(text=f"👤 {username}")
    
    def reset(self):
        """Reset the view state."""
        self._selected_pet_id = None
        self._hide_pet_details()
        self._pet_table.set_data([])
