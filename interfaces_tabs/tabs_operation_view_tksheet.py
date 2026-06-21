from tksheet import Sheet
import tkinter as tk
from typing import List


class OperationTree(tk.Frame):
    def __init__(self, parent, callbacks=None, columns=None, headings=None):
        super().__init__(parent)
        self.callbacks_ui = callbacks or {}

        # Initialisation du Sheet
        self.sheet = Sheet(
            self,
            headers=headings or ("Date", "Catégorie", "Tiers", "Débit", "Crédit", "Solde")
        )
        self.sheet.pack(fill="both", expand=True)
        print(f"Widget Sheet créé : {self.sheet}")
        # Cela affichera dans la console si le widget est bien initialisé
        # et s'il reçoit des événements.
        # ACTIVER TOUTES LES OPTIONS D'INTERACTION
        self.sheet.enable_bindings((
            "all"  # Active absolument tout (tri, clic, menu contextuel)
        ))

        self.sheet.extra_bindings([
            ("cell_select", self._handle_row_selection),
            ("row_double_click", self._handle_row_double_click)
        ])

    def insert_rows(self, rows: List[dict]):
        keys = ["date_operation", "categorie", "tiers", "debit", "credit", "solde"]
        data = [[row.get(k, "") for k in keys] for row in rows]
        self.sheet.set_sheet_data(data)
        self.sheet.refresh()

    def _handle_row_selection(self, event):
        row_data = self.sheet.get_row_data(event[0])
        cb = self.callbacks_ui.get("on_operation_selected")
        if cb: cb(row_data)

    def _handle_row_double_click(self, event):
        row_data = self.sheet.get_row_data(event[0])
        cb = self.callbacks_ui.get("on_operation_opened")
        if cb: cb(row_data)