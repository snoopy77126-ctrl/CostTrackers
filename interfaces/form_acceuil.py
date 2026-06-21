import tkinter as tk
from tkinter import ttk

from _helpers.acceuil_helpers import AcceuilHelpers
from interfaces_tabs._tabs_graf import TabsGraf
from interfaces_tabs.tabs_operation_view_tree import OperationTree


class Dashboard(tk.Frame):
    def __init__(self, parent, services=None):
        super().__init__(parent)
        fenetre_principale = parent.winfo_toplevel()
        fenetre_principale.title("Dashboard - Gestion Financière")

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

        ttk.Label(header, text="Ma page d'accueil Money", font=("Arial", 16, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Button(header, text="Actualiser", command=self.refresh).grid(row=0, column=2, sticky="e")

        body = ttk.PanedWindow(self, orient="horizontal")
        body.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        left = ttk.Frame(body)
        right = ttk.Frame(body)
        body.add(left, weight=3)
        body.add(right, weight=2)

        left.rowconfigure(0, weight=3)
        left.rowconfigure(1, weight=2)
        left.columnconfigure(0, weight=1)

        self.tresorerie_graph = TabsGraf(left, title="Prevision de tresorerie")
        self.tresorerie_graph.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))

        self.operation_tree = OperationTree(left)
        self.operation_tree.grid(row=1, column=0, sticky="nsew", padx=(0, 8))

        right.rowconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        right.rowconfigure(2, weight=1)
        right.columnconfigure(0, weight=1)

        self.budget_frame = ttk.LabelFrame(right, text="Categories favorites : mois en cours", padding=8)
        self.budget_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 8))

        self.compte_frame = ttk.LabelFrame(right, text="Comptes favoris", padding=8)
        self.compte_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 8))

        self.echeance_frame = ttk.LabelFrame(right, text="Echeancier", padding=8)
        self.echeance_frame.grid(row=2, column=0, sticky="nsew")

    def refresh(self):
        self.tresorerie_graph.set_points(self.helpers.tresorerie_points())
        self.operation_tree.insert_rows(self.helpers.operation_rows(limit=80))
        self._fill_budgets()
        self._fill_comptes()
        self._fill_echeances()

    def _clear_frame(self, frame):
        for child in frame.winfo_children():
            child.destroy()

    def _fill_budgets(self):
        self._clear_frame(self.budget_frame)
        for row_index, row in enumerate(self.helpers.categorie_budget_rows()):
            ttk.Label(self.budget_frame, text=row["categorie"]).grid(row=row_index * 2, column=0, sticky="w")
            ttk.Label(self.budget_frame, text=row["montant"]).grid(row=row_index * 2, column=1, sticky="e")
            progress = ttk.Progressbar(self.budget_frame, value=row["ratio"] * 100, maximum=100)
            progress.grid(row=row_index * 2 + 1, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        self.budget_frame.columnconfigure(0, weight=1)

    def _fill_comptes(self):
        self._clear_frame(self.compte_frame)
        ttk.Label(self.compte_frame, text="Compte").grid(row=0, column=0, sticky="w")
        ttk.Label(self.compte_frame, text="Solde").grid(row=0, column=1, sticky="e")
        for index, row in enumerate(self.helpers.compte_rows(), start=1):
            ttk.Label(self.compte_frame, text=row["compte"]).grid(row=index, column=0, sticky="w")
            ttk.Label(self.compte_frame, text=row["solde"]).grid(row=index, column=1, sticky="e")
        self.compte_frame.columnconfigure(0, weight=1)

    def _fill_echeances(self):
        self._clear_frame(self.echeance_frame)
        rows = self.helpers.echeance_rows(days_window=30)[:5]
        for index, row in enumerate(rows):
            text = f"{row['prochaine']}  {row['tiers']}"
            ttk.Label(self.echeance_frame, text=text).grid(row=index, column=0, sticky="w")
            ttk.Label(self.echeance_frame, text=row["montant"]).grid(row=index, column=1, sticky="e")
        self.echeance_frame.columnconfigure(0, weight=1)
