"""
Dialog windows for the Pet Manager application.
Includes forms for adding/editing pets and confirmation dialogs.
"""

import tkinter as tk
from tkinter import messagebox
from typing import Callable, Optional, Dict, Any
from ui.styles import COLORS, FONTS, PADDING
from ui.components import StyledButton, StyledEntry, StyledLabel


class PetDialog(tk.Toplevel):
    """Dialog for adding or editing a pet."""
    
    # Common pet species for dropdown
    SPECIES_OPTIONS = ["Dog", "Cat", "Bird", "Fish", "Rabbit", "Hamster", "Other"]
    
    def __init__(self, parent, title: str = "Add Pet", 
                 pet_data: Optional[Dict[str, Any]] = None,
                 on_save: Callable = None):
        super().__init__(parent)
        
        self.title(title)
        self.configure(bg=COLORS["card_bg"])
        self.resizable(False, False)
        
        self._pet_data = pet_data or {}
        self._on_save = on_save
        self._result = None
        
        # Center dialog
        self.transient(parent)
        self.grab_set()
        
        self._setup_ui()
        self._populate_fields()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        main_frame = tk.Frame(self, bg=COLORS["card_bg"], padx=PADDING["large"],
                              pady=PADDING["large"])
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Name field
        self._create_field(main_frame, "Name:", 0)
        self._name_entry = StyledEntry(main_frame, width=30)
        self._name_entry.grid(row=0, column=1, pady=PADDING["small"], sticky="ew")
        
        # Species dropdown
        self._create_field(main_frame, "Species:", 1)
        self._species_var = tk.StringVar(value=self.SPECIES_OPTIONS[0])
        self._species_dropdown = tk.OptionMenu(main_frame, self._species_var, 
                                                *self.SPECIES_OPTIONS)
        self._species_dropdown.config(font=FONTS["body"], bg=COLORS["white"])
        self._species_dropdown.grid(row=1, column=1, pady=PADDING["small"], sticky="ew")
        
        # Breed field
        self._create_field(main_frame, "Breed:", 2)
        self._breed_entry = StyledEntry(main_frame, width=30)
        self._breed_entry.grid(row=2, column=1, pady=PADDING["small"], sticky="ew")
        
        # Age field
        self._create_field(main_frame, "Age (years):", 3)
        self._age_entry = StyledEntry(main_frame, width=30)
        self._age_entry.grid(row=3, column=1, pady=PADDING["small"], sticky="ew")
        
        # Weight field
        self._create_field(main_frame, "Weight (kg):", 4)
        self._weight_entry = StyledEntry(main_frame, width=30)
        self._weight_entry.grid(row=4, column=1, pady=PADDING["small"], sticky="ew")
        
        # Notes field
        self._create_field(main_frame, "Notes:", 5)
        self._notes_text = tk.Text(main_frame, width=30, height=4, font=FONTS["body"],
                                   relief=tk.FLAT, highlightthickness=1,
                                   highlightbackground=COLORS["border"])
        self._notes_text.grid(row=5, column=1, pady=PADDING["small"], sticky="ew")
        
        # Buttons
        btn_frame = tk.Frame(main_frame, bg=COLORS["card_bg"])
        btn_frame.grid(row=6, column=0, columnspan=2, pady=(PADDING["large"], 0))
        
        StyledButton(btn_frame, text="Cancel", style="secondary",
                    command=self.destroy).pack(side=tk.LEFT, padx=PADDING["small"])
        StyledButton(btn_frame, text="Save", style="success",
                    command=self._save).pack(side=tk.LEFT, padx=PADDING["small"])
    
    def _create_field(self, parent, label: str, row: int):
        """Create a form field label."""
        StyledLabel(parent, text=label, style="body_bold").grid(
            row=row, column=0, pady=PADDING["small"], padx=(0, PADDING["medium"]), sticky="e"
        )
    
    def _populate_fields(self):
        """Populate fields with existing pet data if editing."""
        if self._pet_data:
            self._name_entry.insert(0, self._pet_data.get("name", ""))
            self._species_var.set(self._pet_data.get("species", self.SPECIES_OPTIONS[0]))
            self._breed_entry.insert(0, self._pet_data.get("breed", ""))
            
            age = self._pet_data.get("age", "")
            if age:
                self._age_entry.insert(0, str(age))
            
            weight = self._pet_data.get("weight", "")
            if weight:
                self._weight_entry.insert(0, str(weight))
            
            self._notes_text.insert("1.0", self._pet_data.get("notes", ""))
    
    def _validate(self) -> tuple[bool, str]:
        """Validate form input."""
        name = self._name_entry.get().strip()
        if not name:
            return False, "Name is required"
        
        # Validate age if provided
        age_str = self._age_entry.get().strip()
        if age_str:
            try:
                age = int(age_str)
                if age < 0:
                    return False, "Age must be a positive number"
            except ValueError:
                return False, "Age must be a valid number"
        
        # Validate weight if provided
        weight_str = self._weight_entry.get().strip()
        if weight_str:
            try:
                weight = float(weight_str)
                if weight < 0:
                    return False, "Weight must be a positive number"
            except ValueError:
                return False, "Weight must be a valid number"
        
        return True, ""
    
    def _save(self):
        """Save the pet data."""
        valid, error = self._validate()
        if not valid:
            messagebox.showerror("Validation Error", error, parent=self)
            return
        
        # Collect data
        age_str = self._age_entry.get().strip()
        weight_str = self._weight_entry.get().strip()
        
        self._result = {
            "name": self._name_entry.get().strip(),
            "species": self._species_var.get(),
            "breed": self._breed_entry.get().strip(),
            "age": int(age_str) if age_str else 0,
            "weight": float(weight_str) if weight_str else 0.0,
            "notes": self._notes_text.get("1.0", tk.END).strip()
        }
        
        if self._on_save:
            self._on_save(self._result)
        
        self.destroy()
    
    @property
    def result(self) -> Optional[Dict[str, Any]]:
        """Get the dialog result."""
        return self._result


def confirm_dialog(parent, title: str, message: str) -> bool:
    """Show a confirmation dialog and return True if confirmed."""
    return messagebox.askyesno(title, message, parent=parent)


def show_error(parent, title: str, message: str):
    """Show an error message dialog."""
    messagebox.showerror(title, message, parent=parent)


def show_info(parent, title: str, message: str):
    """Show an info message dialog."""
    messagebox.showinfo(title, message, parent=parent)
