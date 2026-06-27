# -*- coding: utf-8 -*-
####################################
# Projet : CostTracker
# Fichier : interfaces_mod/mod_budget_editor.py
# Description : Fenêtre modale d'édition d'une ligne budgétaire
# Date : 24/06/2026     Etat : Stable
####################################

import tkinter as tk
from tkinter import ttk, messagebox

from _helpers.budget_helpers import BudgetHelpers
from interfaces_tabs.tabs_budget_button import BudgetButton
from interfaces_tabs.tabs_budget_data import BudgetData
from interfaces_tabs.tabs_budget_tree import BudgetTree


class BudgetEditor(tk.Toplevel):
    def __init__(self, parent, services: dict, mois: int, annee: int):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.title(f"Gestion du budget — {mois:02d}/{annee}")
        self.geometry("900x480")

        self.services = services
        self.helpers  = BudgetHelpers(services)
        self.helpers.set_periode(mois, annee)

        self.callbacks = self._build_callbacks()
        self._build_widgets()
        self.initialise()

    # ── UI ────────────────────────────────────────────────────────────

    def _build_widgets(self):
        self.container = ttk.Frame(self, padding=10)
        self.container.pack(fill="both", expand=True)

        pw = ttk.PanedWindow(self.container, orient="horizontal")
        pw.pack(fill="both", expand=True)

        # Gauche : liste
        self.tree = BudgetTree(pw, callbacks=self.callbacks)
        pw.add(self.tree, weight=3)

        # Droite : formulaire + boutons
        right = ttk.Frame(pw)
        pw.add(right, weight=1)

        self.form = BudgetData(right, callbacks=self.callbacks)
        self.form.pack(fill="both", expand=True, pady=5)

        self.buttons = BudgetButton(right, callbacks=self.callbacks)
        self.buttons.pack(fill="x")

    def _build_callbacks(self) -> dict:
        return {
            "on_budget_selected": self._on_select,
            "on_budget_opened":   self._on_select,
            "action_add":                self._on_add_new,
            "action_save":               self._on_save,
            "action_delete":             self._on_delete,
            "action_init_periodiques":   self._on_init_periodiques,
        }

    # ── Chargement ────────────────────────────────────────────────────

    def initialise(self):
        self.helpers.initialise()
        self._fill_combos()
        self.refresh_tree()
        self.form._clear()

    def _fill_combos(self):
        self.form.set_values({
            "categorie_id": self.helpers.fetch_categories(),
            "type_flux":    self.helpers.fetch_types_flux(),
        })

    def refresh_tree(self):
        self.tree.insert_rows(self.helpers.fetch_rows())

    # ── Callbacks ─────────────────────────────────────────────────────

    def _on_select(self, row):
        if not row:
            return
        data = self.helpers.fetch_data(row.get("id"))
        self._fill_combos()
        self.form.set_values(data)
        self.form.select_combobox_by_key(
            "categorie_id",
            data.get("categorie_id", {}).get("iid_key") if isinstance(data.get("categorie_id"), dict) else None
        )
        self.form.select_combobox_by_key(
            "type_flux",
            data.get("type_flux")
        )

    def _on_add_new(self):
        self.helpers.current_id = None
        self.form._clear()
        self._fill_combos()

    def _on_save(self):
        data = self.form.get_submit_data()
        if not data.get("categorie_id"):
            messagebox.showwarning("Saisie", "Veuillez sélectionner une catégorie.")
            return
        if self.helpers.save(data):
            self.helpers.initialise()
            self.refresh_tree()
            self.form._clear()
            self._fill_combos()

    def _on_delete(self):
        if not self.helpers.current_id:
            return
        if messagebox.askyesno("Supprimer", "Supprimer cette ligne budgétaire ?"):
            if self.helpers.delete():
                self.helpers.initialise()
                self.refresh_tree()
                self.form._clear()
                self._fill_combos()

    def _on_init_periodiques(self):
        n = self.helpers.init_from_periodiques(self.helpers._mois, self.helpers._annee)
        if n:
            messagebox.showinfo("Initialisation", f"{n} ligne(s) créée(s) depuis les périodiques.")
            self.helpers.initialise()
            self.refresh_tree()
        else:
            messagebox.showinfo("Initialisation", "Aucune nouvelle ligne à créer.")
