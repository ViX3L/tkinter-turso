"""
Reusable UI components for the Pet Manager application.
Provides styled widgets with consistent appearance.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, List, Dict, Any
from ui.styles import COLORS, FONTS, PADDING, DIMENSIONS


class StyledButton(tk.Button):
    """Custom styled button with hover effects."""
    
    def __init__(self, parent, text: str, command: Callable = None,
                 style: str = "primary", **kwargs):
        # Determine colors based on style
        bg_colors = {
            "primary": (COLORS["primary"], COLORS["primary_dark"]),
            "secondary": (COLORS["secondary"], COLORS["dark"]),
            "success": (COLORS["success"], "#218838"),
            "danger": (COLORS["danger"], "#C82333"),
            "warning": (COLORS["warning"], "#E0A800")
        }
        
        bg, hover_bg = bg_colors.get(style, bg_colors["primary"])
        fg = COLORS["white"] if style != "warning" else COLORS["dark"]
        
        super().__init__(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            font=FONTS["button"],
            relief=tk.FLAT,
            cursor="hand2",
            padx=PADDING["medium"],
            pady=PADDING["small"],
            **kwargs
        )
        
        self._bg = bg
        self._hover_bg = hover_bg
        
        # Bind hover events
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, event):
        self.config(bg=self._hover_bg)
    
    def _on_leave(self, event):
        self.config(bg=self._bg)


class StyledEntry(tk.Entry):
    """Custom styled entry field with placeholder support."""
    
    def __init__(self, parent, placeholder: str = "", show: str = None, **kwargs):
        super().__init__(
            parent,
            font=FONTS["body"],
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["primary"],
            **kwargs
        )
        
        self._placeholder = placeholder
        self._show_char = show
        self._has_placeholder = False
        
        if placeholder:
            self._show_placeholder()
            self.bind("<FocusIn>", self._on_focus_in)
            self.bind("<FocusOut>", self._on_focus_out)
    
    def _show_placeholder(self):
        self.config(show="", fg=COLORS["text_muted"])
        self.delete(0, tk.END)
        self.insert(0, self._placeholder)
        self._has_placeholder = True
    
    def _on_focus_in(self, event):
        if self._has_placeholder:
            self.delete(0, tk.END)
            self.config(fg=COLORS["text"])
            if self._show_char:
                self.config(show=self._show_char)
            self._has_placeholder = False
    
    def _on_focus_out(self, event):
        if not self.get():
            self._show_placeholder()
    
    def get_value(self) -> str:
        """Get the actual value (empty string if placeholder is shown)."""
        if self._has_placeholder:
            return ""
        return self.get()


class StyledLabel(tk.Label):
    """Custom styled label."""
    
    def __init__(self, parent, text: str = "", style: str = "body", **kwargs):
        font = FONTS.get(style, FONTS["body"])
        fg = kwargs.pop("fg", COLORS["text"])
        
        super().__init__(
            parent,
            text=text,
            font=font,
            fg=fg,
            bg=kwargs.pop("bg", COLORS["card_bg"]),
            **kwargs
        )


class StatusIndicator(tk.Frame):
    """Visual indicator for online/offline status."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLORS["card_bg"], **kwargs)
        
        self._indicator = tk.Canvas(self, width=12, height=12, 
                                     bg=COLORS["card_bg"], highlightthickness=0)
        self._indicator.pack(side=tk.LEFT, padx=(0, 5))
        
        self._label = StyledLabel(self, text="Offline", style="small")
        self._label.pack(side=tk.LEFT)
        
        self._draw_indicator(False)
    
    def _draw_indicator(self, is_online: bool):
        self._indicator.delete("all")
        color = COLORS["online"] if is_online else COLORS["offline"]
        self._indicator.create_oval(2, 2, 10, 10, fill=color, outline=color)
    
    def set_status(self, is_online: bool, pending: int = 0):
        """Update the status indicator."""
        self._draw_indicator(is_online)
        
        if is_online:
            text = "Online" if pending == 0 else f"Online ({pending} pending)"
        else:
            text = "Offline" if pending == 0 else f"Offline ({pending} pending)"
        
        self._label.config(text=text)


class DataTable(tk.Frame):
    """Styled table for displaying data with selection support."""
    
    def __init__(self, parent, columns: List[Dict[str, Any]], 
                 on_select: Callable = None, **kwargs):
        super().__init__(parent, bg=COLORS["card_bg"], **kwargs)
        
        self._columns = columns
        self._on_select = on_select
        self._data = []
        
        self._setup_table()
    
    def _setup_table(self):
        # Create treeview with scrollbar
        self._tree_frame = tk.Frame(self, bg=COLORS["card_bg"])
        self._tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure style
        style = ttk.Style()
        style.configure("Custom.Treeview",
                       font=FONTS["body"],
                       rowheight=DIMENSIONS["table_row_height"])
        style.configure("Custom.Treeview.Heading",
                       font=FONTS["body_bold"])
        
        # Create treeview
        col_ids = [col["id"] for col in self._columns]
        self._tree = ttk.Treeview(
            self._tree_frame,
            columns=col_ids,
            show="headings",
            style="Custom.Treeview",
            selectmode="browse"
        )
        
        # Configure columns
        for col in self._columns:
            self._tree.heading(col["id"], text=col["text"])
            self._tree.column(col["id"], width=col.get("width", 100),
                            anchor=col.get("anchor", "w"))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self._tree_frame, orient=tk.VERTICAL,
                                  command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection
        if self._on_select:
            self._tree.bind("<<TreeviewSelect>>", self._handle_select)
    
    def _handle_select(self, event):
        selection = self._tree.selection()
        if selection and self._on_select:
            item = self._tree.item(selection[0])
            self._on_select(item["values"])
    
    def set_data(self, data: List[Dict[str, Any]]):
        """Set table data."""
        self._data = data
        self._tree.delete(*self._tree.get_children())
        
        for row in data:
            values = [row.get(col["id"], "") for col in self._columns]
            self._tree.insert("", tk.END, values=values)
    
    def get_selected(self) -> Optional[List[Any]]:
        """Get currently selected row values."""
        selection = self._tree.selection()
        if selection:
            return self._tree.item(selection[0])["values"]
        return None
    
    def clear_selection(self):
        """Clear current selection."""
        self._tree.selection_remove(self._tree.selection())
