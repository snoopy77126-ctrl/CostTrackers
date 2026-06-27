# models/ui/tabs_prevision_data.py
import tkinter as tk
from tkinter import ttk

class PrevisionData(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Champs de saisie
        ttk.Label(self, text="Libellé :").grid(row=0, column=0)
        self.entry_libelle = ttk.Entry(self)
        self.entry_libelle.grid(row=0, column=1)
        
        ttk.Label(self, text="Type :").grid(row=1, column=0)
        self.combo_type = ttk.Combobox(self, values=["travail", "repos", "vacances"])
        self.combo_type.grid(row=1, column=1)
        
        # Sous-formulaire (Détails)
        self.tree_details = ttk.Treeview(self, columns=("libelle", "montant"), show="headings")
        self.tree_details.heading("libelle", text="Dépense")
        self.tree_details.heading("montant", text="Montant")
        self.tree_details.grid(row=2, column=0, columnspan=2)