from interfaces_tabs._tabs_generique_data import BaseFormFrame
from tkinter import ttk
import tkinter as tk


class OperationSaisieData(BaseFormFrame):
    """ Formulaire de saisie/édition d'une opération optimisé. """

    def __init__(self, parent, callbacks=None):
        super().__init__(parent, title="Saisie Opération", callbacks=callbacks)
        self.build_widgets()

    def build_widgets(self):
        # Utilisation des méthodes de BaseFormFrame pour construire le formulaire
        # Cela remplace tout votre code manuel avec grid()

        self.add_combobox("libelle", "OperationBase")

        # Exemple de ligne avec deux colonnes (si vous voulez personnaliser, 
        # utilisez un conteneur comme défini dans add_combobox)
        self.add_combobox("tiers_id", "Tiers")
        self.add_combobox("compte_id", "Account")

        self.add_entry("commentaire", "Note")
        self.add_combobox("categorie_id", "Categories")

        self.add_entry("montant", "Débit/Crédit")
        self.add_entry("solde", "Solde")
        self.add_date("date_operation", "Date")

        self.add_checkbox("periodique", "OperationBase Periodique")

    def load_combobox_data(self, tiers_data, comptes_data, categories_data):
        """
        Adaptation : On injecte les données dans le format attendu par BaseFormFrame
        BaseFormFrame s'attend à une structure {key: [dict_values]}
        """
        # On définit les données brutes sur l'instance pour que _on_combobox_selected les trouve
        self._raw_data_tiers_id = tiers_data
        self._raw_data_compte_id = comptes_data
        self._raw_data_categorie_id = categories_data

        # On met à jour les widgets
        self.entries["tiers_id"]["values"] = [t['value'] for t in tiers_data]
        self.entries["compte_id"]["values"] = [c['value'] for c in comptes_data]
        self.entries["categorie_id"]["values"] = [c['value'] for c in categories_data]

    def set_values_from_operation(self, data: dict):
        """Utilise simplement la méthode native de BaseFormFrame."""
        self.set_values(data)

    def get_form_values(self):
        """Utilise simplement la méthode native de BaseFormFrame."""
        return self.get_values()