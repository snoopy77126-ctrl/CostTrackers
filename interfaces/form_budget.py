####################################
# Projet : CostTracker
# Fichier : interfaces/form_budget.py
# Description : Vue principale Budget — tableau de bord mensuel
# Date : 24/06/2026     Etat : Stable
####################################

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from _helpers.budget_helpers import BudgetHelpers
from interfaces_tabs.tabs_budget_tree import BudgetTree
from interfaces_tabs.tabs_budget_button import BudgetButton


class BudgetView(tk.Frame):
    def __init__(self, parent, services: dict = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.services = services or {}
        self.helpers  = BudgetHelpers(self.services)
        today = date.today()
        self._mois  = today.month
        self._annee = today.year
        self.helpers.set_periode(self._mois, self._annee)

        self._build_widgets()
        self.initialise()

    # ── Construction UI ───────────────────────────────────────────────

    def _build_widgets(self):
        # En-tête : sélecteur de période + résumé
        header = ttk.Frame(self, padding=(10, 6))
        header.pack(fill="x")

        ttk.Label(header, text="Période :").pack(side="left", padx=(0, 4))
        self._periode_var = tk.StringVar()
        self._combo_periode = ttk.Combobox(
            header, textvariable=self._periode_var, state="readonly", width=10
        )
        self._combo_periode.pack(side="left")
        self._combo_periode.bind("<<ComboboxSelected>>", self._on_periode_changed)

        # Résumé rapide
        self._lbl_depenses = ttk.Label(header, text="", foreground="#cc2222")
        self._lbl_depenses.pack(side="left", padx=(20, 0))
        self._lbl_revenus  = ttk.Label(header, text="", foreground="#1a5fa8")
        self._lbl_revenus.pack(side="left", padx=(10, 0))
        self._lbl_solde    = ttk.Label(header, text="", font=("", 9, "bold"))
        self._lbl_solde.pack(side="left", padx=(10, 0))

        ttk.Separator(self, orient="horizontal").pack(fill="x")

        # Treeview
        callbacks = {
            "on_budget_selected": self._on_select,
        }
        self.tree = BudgetTree(self, callbacks=callbacks)
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        # Boutons
        btn_cbs = {
            "action_add":              self._on_add,
            "action_delete":           self._on_delete,
            "action_init_periodiques": self._on_init_periodiques,
            "action_save":             self._on_edit,
        }
        buttons = BudgetButton(self, callbacks=btn_cbs)
        buttons.pack(fill="x", padx=10, pady=(0, 6))

    # ── Init ──────────────────────────────────────────────────────────

    def initialise(self):
        self.helpers.initialise()
        self._load_periodes()
        self.refresh()

    def _load_periodes(self):
        periodes = self.helpers.fetch_periodes()
        self._periodes_data = periodes
        self._combo_periode["values"] = [p["value"] for p in periodes]
        current = f"{self._mois:02d}/{self._annee}"
        vals = [p["value"] for p in periodes]
        if current in vals:
            self._combo_periode.current(vals.index(current))
        elif vals:
            self._combo_periode.current(0)

    def refresh(self):
        rows = self.helpers.fetch_rows()
        self.tree.insert_rows(rows)
        self._update_resume()

    def _update_resume(self):
        r = self.helpers.fetch_resume()
        self._lbl_depenses.config(
            text=f"Dépenses : {r['depenses_reel']:,.0f} / {r['depenses_prevu']:,.0f} €"
        )
        self._lbl_revenus.config(
            text=f"Revenus : {r['revenus_reel']:,.0f} / {r['revenus_prevu']:,.0f} €"
        )
        solde = r["solde_prevu"]
        self._lbl_solde.config(
            text=f"Solde prévu : {solde:+,.0f} €",
            foreground="#2a7a2a" if solde >= 0 else "#cc2222"
        )

    # ── Callbacks ─────────────────────────────────────────────────────

    def _on_periode_changed(self, _event=None):
        idx = self._combo_periode.current()
        if 0 <= idx < len(self._periodes_data):
            p = self._periodes_data[idx]
            self._mois  = p["mois"]
            self._annee = p["annee"]
            self.helpers.set_periode(self._mois, self._annee)
            self.refresh()

    def _on_select(self, row):
        self._selected_row = row

    def _on_add(self):
        from interfaces_mod.mod_budget_editor import BudgetEditor
        BudgetEditor(self.winfo_toplevel(), self.services, self._mois, self._annee)
        self.helpers.initialise()
        self.refresh()

    def _on_edit(self):
        self._on_add()   # Ouvre l'éditeur complet

    def _on_delete(self):
        row = getattr(self, "_selected_row", None)
        if not row:
            return
        if messagebox.askyesno("Supprimer", "Supprimer cette ligne budgétaire ?"):
            self.helpers.current_id = row.get("id")
            if self.helpers.delete():
                self.helpers.initialise()
                self.refresh()

    def _on_init_periodiques(self):
        n = self.helpers.init_from_periodiques(self._mois, self._annee)
        if n:
            messagebox.showinfo("Initialisation", f"{n} ligne(s) créée(s) depuis les périodiques.")
            self.helpers.initialise()
            self.refresh()
        else:
            messagebox.showinfo("Initialisation", "Aucune nouvelle ligne à créer.")

# ------------------ Main test ------------------
if __name__ == '__main__':
    from _services._bootstrap_services import build_app_services

    root = tk.Tk()
    root.title("formulaire Budget")

    services = build_app_services()

    app = BudgetView(root, services)
    app.pack(fill='both', expand=True)

    root.geometry('900x400')
    root.mainloop()