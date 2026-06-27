# -*- coding: utf-8 -*-
from tkinter import ttk
from interfaces_tabs._tabs_generique_data import BaseFormFrame


class PeriodiqueData_Old(BaseFormFrame):
    def __init__(self, parent, callbacks=None):
        super().__init__(parent, title="Charge périodique", callbacks=callbacks)

        self.add_entry(   "libelle",        "Libellé :")
        self.add_combobox("tiers_id",       "Tiers :")
        self.add_combobox("categorie_id",   "Catégorie :")
        self.add_combobox("compte_id",      "Compte :")
        self.add_entry(   "montant",        "Montant (€) :")
        self.add_combobox("frequence",      "Fréquence :")
        self.add_combobox("type_flux",      "Type :")
        self.add_date(    "date_prochaine", "Prochaine échéance :")
        self.add_checkbox("actif",          "Actif :", text="")
        self.add_entry(   "commentaire",    "Commentaire :")

    def get_submit_data(self) -> dict:
        data = self.get_values()
        # Convertir le montant en float
        try:
            data["montant"] = float(str(data.get("montant") or "0").replace(",", "."))
        except ValueError:
            data["montant"] = 0.0
        return data

    def _clear(self):
        super()._clear()
        # Cocher actif par défaut sur un nouveau formulaire
        if "actif" in self.vars:
            self.vars["actif"].set(True)

class PeriodiqueData(BaseFormFrame):
    def __init__(self, parent, callbacks=None):
        super().__init__(parent, title="Charge périodique", callbacks=callbacks)

        # Configuration : on donne du poids aux colonnes de saisie (1 et 3)
        self.form.columnconfigure(1, weight=1)
        self.form.columnconfigure(3, weight=1)

        # --- Ligne 0 ---
        # Label auto en col 0, champ en col 1
        self.add_combobox("compte_id", "À partir du compte :*", row=0,
                          grid_options={"column": 1})
        # Label manuel en col 2, champ en col 3
        ttk.Label(self.form, text="Prochaine échéance :*").grid(row=0, column=2, sticky="w", padx=5)
        self.add_date("date_prochaine", "", row=0,
                      grid_options={"column": 3})

        # --- Ligne 1 ---
        self.add_combobox("type_paiement", "Méthode de pmt :*", row=1,
                          grid_options={"column": 1})
        ttk.Label(self.form, text="Fréquence :*").grid(row=1, column=2, sticky="w", padx=5)
        self.add_combobox("frequence", "", row=1,
                          grid_options={"column": 3})

        # --- Ligne 2 ---
        self.add_numeric_calc("montant", "Montant :*", row=2,
                       grid_options={"column": 1})
        # Petit champ "montant fixe"
        self.add_entry("est_fixe", "Il s'agit d'un montant fixe", row=2,
                       grid_options={"column": 3})

        # --- Ligne 3 ---
        # Catégorie sur 2 colonnes (1 et 2)
        self.add_combobox("categorie_id", "Catégorie :", row=3,
                          grid_options={"column": 1, "columnspan": 2})
        # Bouton à ajouter via une méthode personnalisée ou un widget direct
        ttk.Button(self.form, text="Ventiler").grid(row=3, column=3, sticky="ew", padx=5)

        # --- Ligne 4 ---
        # Notes sur toute la largeur
        self.add_entry("notes", "Notes :", row=4,
                       grid_options={"column": 1, "columnspan": 3})

        # --- Ligne 5 & 6 (Automatisation) ---
        self.add_checkbox("auto_entry", "Entrer automatiquement l'opération...", row=5)
        self.add_entry("delai_jours", "Jours avant échéance :", row=6)

    def get_submit_data(self) -> dict:
        data = self.get_values()
        try:
            data["montant"] = float(str(data.get("montant") or "0").replace(",", "."))
        except ValueError:
            data["montant"] = 0.0
        return data

    def _clear(self):
        super()._clear()
        if "actif" in self.vars:
            self.vars["actif"].set(True)
