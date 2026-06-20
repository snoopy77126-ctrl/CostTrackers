import tkinter as tk
from tkinter import ttk


class FusionEditor(tk.Toplevel):
    def __init__(self, parent, helper):
        super().__init__(parent)
        self.helper = helper

        self.title("Fusionner les éléments")
        self.geometry("900x450")
        self.transient(parent)
        self.grab_set()

        self.build_widgets()
        self._populate_data()

    def build_widgets(self):
        # Configuration identique à ce que vous aviez
        main_frame = ttk.Frame(self, padding=10)
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Treeview utilisant self.helper.get_columns_config()
        cols, headings = self.helper.get_columns_config()
        self.tree = ttk.Treeview(main_frame, columns=cols, show="headings")
        # ... (config colonnes, scrollbar, etc.)

        # Bouton OK qui appelle self.helper.executer_fusion(resultats)
        ttk.Button(self, text="OK", command=self._action_ok).pack()

    def _populate_data(self):
        for row_data in self.helper.prepare_rows():
            # row_data contient les valeurs et le tag 'conflit'
            self.tree.insert("", "end", values=row_data["values"], tags=("conflit",) if row_data["conflit"] else ())

    def _on_cell_click(self, event):
        # Logique générique de copie de colonne
        # (identique à celle que vous avez déjà)
        pass

    def _action_ok(self):
        # Collecte des données depuis le Treeview
        # ...
        self.helper.executer_fusion(resultats)
        self.destroy()