from interfaces_tabs._tabs_generique_data import BaseFormFrame
from tkinter import ttk


class OperationImportData(BaseFormFrame):
    def __init__(self, parent, callbacks=None, target_columns=None):
        super().__init__(parent, title="Affectation des colonnes", callbacks=callbacks)
        self.target_columns = target_columns or {}
        # Dictionnaire pour stocker les références aux widgets Combobox
        self.combo_widgets = {}
        self._build_fields()


    def _build_fields(self):
        # 1. On crée les deux frames
        left_frame = ttk.Frame(self.form)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        right_frame = ttk.Frame(self.form)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # 2. Découpage
        items = list(self.target_columns.items())
        midpoint = (len(items) + 1) // 2

        # 3. Remplissage gauche
        # On force le compteur à 0 avant de commencer
        self._row_counter = 0
        for target, label in items[:midpoint]:
            # On utilise votre méthode existante, mais on doit ruser
            # pour que le widget s'ajoute dans 'left_frame' au lieu de 'self.form'.
            # Comme vous ne voulez pas modifier add_combobox,
            # on change temporairement la cible de création :
            original_form = self.form
            self.form = left_frame
            self.add_combobox(target, f"{label} :")
            self.form = original_form

        # 4. Remplissage droite
        # On remet le compteur à 0 pour que la colonne de droite commence en haut
        self._row_counter = 0
        for target, label in items[midpoint:]:
            original_form = self.form
            self.form = right_frame
            self.add_combobox(target, f"{label} :")
            self.form = original_form

    def get_mapping(self):
        """Récupère l'état actuel du mapping pour le parent."""
        return {k: v.get() for k, v in self.vars.items()}

    def _clear(self):
        """Réinitialisation propre."""
        self.set_values({k: "" for k in self.vars.keys()})
