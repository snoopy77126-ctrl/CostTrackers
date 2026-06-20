# operations_import_helpers.py
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk


class MappingDialog(tk.Toplevel):
    def __init__(self, parent, title, item_label, missing_value, existing_items):
        super().__init__(parent)
        self.title(title)
        self.geometry("420x250")
        self.resizable(False, False)

        # Rend la fenêtre modale (bloque le parent)
        self.transient(parent)
        self.grab_set()
        self.focus_set()  # Force le focus sur cette fenêtre

        self.result = {"action": "cancel", "apply_to_all": False}

        # Widgets
        ttk.Label(self, text="Élément inconnu détecté :", font=("Helvetica", 10, "bold")).pack(pady=(10, 2))
        ttk.Label(self, text=f"« {missing_value} »", foreground="#b00020").pack(pady=(0, 10))
        ttk.Label(self, text=f"Associer à un {item_label} existant :").pack(anchor="w", padx=20)

        self.combo_var = tk.StringVar()
        self.combo = ttk.Combobox(self, textvariable=self.combo_var, values=existing_items, state="readonly", width=50)
        self.combo.pack(pady=5, padx=20)

        # La Checkbox
        self.apply_to_all = tk.BooleanVar()
        ttk.Checkbutton(self, text="Appliquer ce choix à tous les éléments manquants",
                        variable=self.apply_to_all).pack(pady=10, padx=20, anchor="w")

        # Boutons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", side="bottom", pady=10, padx=20)

        ttk.Button(btn_frame, text="Créer automatiquement", command=self._on_create).pack(side="left")
        ttk.Button(btn_frame, text="Valider l'association", command=self._on_validate).pack(side="right")

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # IMPORTANT : On attend que l'utilisateur interagisse
        self.wait_window(self)

    def _on_validate(self):
        if self.combo_var.get():
            self.result = {
                "action": "map",
                "value": self.combo_var.get(),
                "apply_to_all": self.apply_to_all.get()
            }
            self.destroy()

    def _on_create(self):
        self.result = {
            "action": "create",
            "apply_to_all": self.apply_to_all.get()
        }
        self.destroy()

    def _on_cancel(self):
        # On définit explicitement un résultat d'annulation
        self.result = {"action": "cancel", "apply_to_all": False}
        self.destroy()
