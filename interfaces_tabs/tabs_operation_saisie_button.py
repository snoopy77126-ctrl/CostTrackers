from tkinter import ttk
import tkinter as tk
from typing import Dict, Optional, Callable

from interfaces_tabs._tabs_generique_button import EditeurActions


class OperationTypeButton(EditeurActions):
    def __init__(self, parent, callbacks: Optional[Dict[str, Callable]] = None):
        super().__init__(parent)
        self.callbacks = callbacks or {}
        self.buttons = {}

        self.container = ttk.Frame(self, padding=5)
        self.container.pack(fill="x")

        self._build_widgets()

    def _build_widgets(self):
        self.buttons["Debit"] = self._add_tk_btn("Debit", "action_select_debit", side="left")
        self.buttons["Credit"] = self._add_tk_btn("Credit", "action_select_credit", side="left")
        self.buttons["Virement"] = self._add_tk_btn("Virement", "action_select_virement", side="right")

    def _add_tk_btn(self, text, cb_name, side="left"):
        """Crée un tk.Button (et non ttk.Button) pour autoriser bg/fg/relief."""
        btn = tk.Button(
            self.container,
            text=text,
            command=lambda: self._trigger(cb_name)
        )
        btn.pack(side=side, padx=2, pady=2)
        return btn

    def set_button_style(self, type_name: str, active: bool):
        """Change le style visuel d'un bouton selon son état actif/inactif."""
        btn = self.buttons.get(type_name)
        if btn:
            if active:
                btn.config(bg="#2f4f7f", fg="white", relief="sunken")
            else:
                btn.config(bg="#d7e4f0", fg="black", relief="raised")