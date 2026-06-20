import tkinter as tk
from tkinter import ttk

from _helpers.acceuil_helpers import AcceuilHelpers
from interfaces_tabs._tabs_generique_tree import FlatTree


class EcheancesView(tk.Frame):
    def __init__(self, parent, services=None):
        super().__init__(parent)
        fenetre_principale = parent.winfo_toplevel()
        fenetre_principale.title("EcheancesView - Gestion Financière")

        self.services = services or {}
        self.helpers = AcceuilHelpers(self.services)
        self.helpers.initialise()
        self.build_widgets()
        self.refresh()

    def build_widgets(self):
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        header = ttk.Frame(self, padding=(10, 8))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)
        ttk.Label(header, text="Synthese des echeances", font=("Arial", 16, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Button(header, text="Actualiser", command=self.refresh).grid(row=0, column=2, sticky="e")

        columns = ("tiers", "montant", "prochaine", "periodicite", "compte", "paye_le")
        headings = ("Tiers", "Montant", "Prochaine echeance", "Periodicite", "Compte", "Paye le")
        self.tree = FlatTree(self, columns=columns, headings=headings)
        self.tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 8))
        for col in columns:
            self.tree.tree.column(col, width=140, stretch=True)

        footer = ttk.Frame(self, padding=(10, 0, 10, 10))
        footer.grid(row=2, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        self.summary_label = ttk.Label(footer, text="")
        self.summary_label.grid(row=0, column=0, sticky="w")
        ttk.Button(footer, text="Integrer au livre de comptes", state="disabled").grid(row=0, column=1, padx=4)
        ttk.Button(footer, text="Nouveau", state="disabled").grid(row=0, column=2, padx=4)
        ttk.Button(footer, text="Modifier", state="disabled").grid(row=0, column=3, padx=4)

    def refresh(self):
        rows = self.helpers.echeance_rows(days_window=90)
        for row in rows:
            row["values"] = [row.get(col, "") for col in self.tree.tree["columns"]]
            row["actif"] = row.get("retard", 0) <= 0
        self.tree.insert_rows(rows)
        overdue = len([row for row in rows if row.get("retard", 0) > 0])
        upcoming = len(rows) - overdue
        self.summary_label.config(text=f"{overdue} en retard - {upcoming} a venir")
