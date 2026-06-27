# -*- coding: utf-8 -*-
####################################
# Projet : CostTracker
# Fichier : interfaces_tabs/tabs_budget_data.py
# Description : Formulaire d'édition d'une ligne budgétaire
# Date : 24/06/2026     Etat : Stable
####################################

from interfaces_tabs._tabs_generique_data import BaseFormFrame


class BudgetData(BaseFormFrame):
    def __init__(self, parent, callbacks=None):
        super().__init__(parent, title="Ligne budgétaire", callbacks=callbacks)

        self.add_combobox("categorie_id",  "Catégorie :")
        self.add_combobox("type_flux",     "Type :")
        self.add_entry(   "montant_prevu", "Montant prévu (€) :")
        self.add_entry(   "commentaire",   "Commentaire :")

    def get_submit_data(self) -> dict:
        data = self.get_values()
        try:
            data["montant_prevu"] = float(
                str(data.get("montant_prevu") or "0").replace(",", ".").replace(" ", "")
            )
        except ValueError:
            data["montant_prevu"] = 0.0
        return data

    def _clear(self):
        super()._clear()
