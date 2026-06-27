# -*- coding: utf-8 -*-
####################################
# Projet : CostTracker
# Fichier : interfaces_mod/mod_periodique_editor.py
# Description : Fenêtre modale d'édition d'un périodique
# Date : 23/06/2026     Etat : Stable
####################################

import tkinter as tk
from tkinter import ttk

from _helpers.periodique_helpers import PeriodiqueHelpers
from interfaces_tabs.tabs_periodique_button import PeriodiqueButton
from interfaces_tabs.tabs_periodique_data import PeriodiqueData
from interfaces_tabs.tabs_periodique_tree import PeriodiqueTree


class PeriodiqueEditor_Old(tk.Toplevel):
    def __init__(self, parent, services: dict):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.title("Gestion des charges périodiques")
        self.geometry("1000x520")

        self.services = services
        self.helpers  = PeriodiqueHelpers(services)
        self.callbacks = self._build_callbacks()

        self._build_widgets()
        self.initialise()

    # ── Construction UI ───────────────────────────────────────────────

    def _build_widgets(self):
        self.container = ttk.Frame(self, padding=10)
        self.container.pack(fill="both", expand=True)

        pw = ttk.PanedWindow(self.container, orient="horizontal")
        pw.pack(fill="both", expand=True)

        # Gauche : liste
        self.tree = PeriodiqueTree(pw, callbacks=self.callbacks)
        pw.add(self.tree, weight=2)

        # Droite : formulaire + boutons
        right = ttk.Frame(pw)
        pw.add(right, weight=1)

        self.form = PeriodiqueData(right, callbacks=self.callbacks)
        self.form.pack(fill="both", expand=True, pady=5)

        self.buttons = PeriodiqueButton(right, callbacks=self.callbacks)
        self.buttons.pack(fill="x")

    def _build_callbacks(self) -> dict:
        return {
            "on_periodique_selected": self._on_select,
            "on_periodique_opened":   self._on_select,
            "action_add":             self._on_add_new,
            "action_save":            self._on_save,
            "action_delete":          self._on_delete,
        }

    # ── Chargement ───────────────────────────────────────────────────

    def initialise(self):
        self.helpers.initialise()
        self._fill_combos()
        self.refresh_tree()
        self.form._clear()
        # Actif coché par défaut
        if "actif" in self.form.vars:
            self.form.vars["actif"].set(True)

    def _fill_combos(self):
        cats     = self.helpers.fetch_categories()
        tiers    = self.helpers.fetch_tiers()
        comptes  = self.helpers.fetch_comptes()
        freqs    = self.helpers.fetch_frequences()
        types    = self.helpers.fetch_types_flux()
        self.form.set_values({
            "categorie_id": cats,
            "tiers_id":     tiers,
            "compte_id":    comptes,
            "frequence":    freqs,
            "type_flux":    types,
        })

    def refresh_tree(self):
        self.tree.insert_rows(self.helpers.fetch_rows())

    # ── Callbacks UI ─────────────────────────────────────────────────

    def _on_select(self, row):
        if not row:
            return
        pid  = row.get("id")
        data = self.helpers.fetch_data(pid)
        self.form.set_values(data)
        # Réhydrater les comboboxes avec leurs listes ET la sélection
        cats    = self.helpers.fetch_categories()
        tiers   = self.helpers.fetch_tiers()
        comptes = self.helpers.fetch_comptes()
        freqs   = self.helpers.fetch_frequences()
        types   = self.helpers.fetch_types_flux()
        self.form.set_values({
            "categorie_id": cats,
            "tiers_id":     tiers,
            "compte_id":    comptes,
            "frequence":    freqs,
            "type_flux":    types,
        })
        self.form.set_values(data)
        # Sélectionner les bons éléments
        self.form.select_combobox_by_key("categorie_id", data.get("categorie_id", {}).get("iid_key") if isinstance(data.get("categorie_id"), dict) else None)
        self.form.select_combobox_by_key("tiers_id",     data.get("tiers_id",     {}).get("iid_key") if isinstance(data.get("tiers_id"), dict) else None)
        self.form.select_combobox_by_key("compte_id",    data.get("compte_id",    {}).get("iid_key") if isinstance(data.get("compte_id"), dict) else None)
        self.form.select_combobox_by_key("frequence",    data.get("frequence"))
        self.form.select_combobox_by_key("type_flux",    data.get("type_flux"))

    def _on_add_new(self):
        self.helpers.current_id = None
        self.form._clear()
        self._fill_combos()
        if "actif" in self.form.vars:
            self.form.vars["actif"].set(True)

    def _on_save(self):
        data = self.form.get_submit_data()
        if self.helpers.save(data):
            self.helpers.initialise()
            self.refresh_tree()

    def _on_delete(self):
        if self.helpers.delete():
            self.helpers.initialise()
            self.refresh_tree()
            self.form._clear()
            self._fill_combos()

class PeriodiqueEditor(tk.Toplevel):
    def __init__(self, parent, services: dict):
        super().__init__(parent)

        # 2. Comportement de la fenêtre (Toplevel)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        self.title("Gestion des charges périodiques")
        self.geometry("700x300")

        # 1. Initialisation (Logique métier & Variables Tkinter de contrôle)
        self.services = services
        self.helpers = PeriodiqueHelpers(services)
        self.callbacks = self._build_callbacks()

        # 3. Construction de l'interface & Chargement initial
        self._build_widgets()
        if hasattr(self, 'initialise'):
            self.initialise()

            # Centrage automatique au moment de l'initialisation
            self.after(50, lambda: self._center_on_parent(parent))


    def _center_on_parent(self, parent):
        # Force le calcul de la taille réelle de la fenêtre
        self.update_idletasks()

        # Dimensions de la modale
        w = self.winfo_width()
        h = self.winfo_height()

        # Position du parent
        px = parent.winfo_x()
        py = parent.winfo_y()
        pw = parent.winfo_width()
        ph = parent.winfo_height()

        # Calcul du centre
        x = px + (pw // 2) - (w // 2)
        y = py + (ph // 2) - (h // 2)

        self.geometry(f"+{x}+{y}")

    # ── Construction UI ───────────────────────────────────────────────

    def _build_widgets(self):
        self.container = ttk.Frame(self, padding=10)
        self.container.pack(fill="both", expand=True)

        pw = ttk.PanedWindow(self.container, orient="horizontal")
        pw.pack(fill="both", expand=True)

        # Droite : formulaire + boutons
        right = ttk.Frame(pw)
        pw.add(right, weight=1)

        self.form = PeriodiqueData(right, callbacks=self.callbacks)
        self.form.pack(fill="both", expand=True, pady=5)

        self.buttons = PeriodiqueButton(right, callbacks=self.callbacks)
        self.buttons.pack(fill="x")

    def _build_callbacks(self) -> dict:
        return {
            "on_periodique_selected": self._on_select,
            "on_periodique_opened":   self._on_select,
            "action_add":             self._on_add_new,
            "action_save":            self._on_save,
            "action_delete":          self._on_delete,
        }

    # ── Chargement ───────────────────────────────────────────────────

    def initialise(self):
        self.helpers.initialise()
        self._fill_combos()
        self.form._clear()
        # Actif coché par défaut
        if "actif" in self.form.vars:
            self.form.vars["actif"].set(True)

    def _fill_combos(self):
        cats     = self.helpers.fetch_categories()
        tiers    = self.helpers.fetch_tiers()
        comptes  = self.helpers.fetch_comptes()
        freqs    = self.helpers.fetch_frequences()
        types    = self.helpers.fetch_types_flux()
        self.form.set_values({
            "categorie_id": cats,
            "tiers_id":     tiers,
            "compte_id":    comptes,
            "frequence":    freqs,
            "type_flux":    types,
        })

    def refresh_tree(self):
        self.tree.insert_rows(self.helpers.fetch_rows())

    # ── Callbacks UI ─────────────────────────────────────────────────

    def _on_select(self, row):
        if not row:
            return
        pid  = row.get("id")
        data = self.helpers.fetch_data(pid)
        self.form.set_values(data)
        # Réhydrater les comboboxes avec leurs listes ET la sélection
        cats    = self.helpers.fetch_categories()
        tiers   = self.helpers.fetch_tiers()
        comptes = self.helpers.fetch_comptes()
        freqs   = self.helpers.fetch_frequences()
        types   = self.helpers.fetch_types_flux()
        self.form.set_values({
            "categorie_id": cats,
            "tiers_id":     tiers,
            "compte_id":    comptes,
            "frequence":    freqs,
            "type_flux":    types,
        })
        self.form.set_values(data)
        # Sélectionner les bons éléments
        self.form.select_combobox_by_key("categorie_id", data.get("categorie_id", {}).get("iid_key") if isinstance(data.get("categorie_id"), dict) else None)
        self.form.select_combobox_by_key("tiers_id",     data.get("tiers_id",     {}).get("iid_key") if isinstance(data.get("tiers_id"), dict) else None)
        self.form.select_combobox_by_key("compte_id",    data.get("compte_id",    {}).get("iid_key") if isinstance(data.get("compte_id"), dict) else None)
        self.form.select_combobox_by_key("frequence",    data.get("frequence"))
        self.form.select_combobox_by_key("type_flux",    data.get("type_flux"))

    def _on_add_new(self):
        self.helpers.current_id = None
        self.form._clear()
        self._fill_combos()
        if "actif" in self.form.vars:
            self.form.vars["actif"].set(True)

    def _on_save(self):
        data = self.form.get_submit_data()
        if self.helpers.save(data):
            self.helpers.initialise()

    def _on_delete(self):
        if self.helpers.delete():
            self.helpers.initialise()
            self.form._clear()
            self._fill_combos()

# ------------------ Main test ------------------
if __name__ == '__main__':
    # Initialisation du parent (root)
    root = tk.Tk()
    root.title("Application Principale")
    # Taille fixe pour le parent
    w, h = 200, 200
    # 2. Calcul du centre de l'écran
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (w // 2)
    y = (screen_height // 2) - (h // 2)

    # 3. Application de la géométrie au centre
    root.geometry(f'{w}x{h}+{x}+{y}')

    # Simulation des services
    try:
        from _services._bootstrap_services import build_app_services

        services = build_app_services()
    except ImportError:
        services = None

    # Lancement de la modale liée au parent
    # On utilise root.after pour garantir que root est bien positionné
    app = PeriodiqueEditor(root, services=services)
    # Force la fermeture de root quand on ferme la fenêtre
    app.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()