from interfaces_tabs._tabs_generique_data import BaseFormFrame


class BanqueData(BaseFormFrame):
    def __init__(self, parent, callbacks=None):
        super().__init__(parent, title="Fiche Contact", callbacks=callbacks)

        # Section Identité
        self.add_entry("label", "Organisation :", row=1)
        self.add_entry("identifiant", "Identifiant :", row=4)

        # Section Coordonnées (Le carnet d'adresse)
        self.add_entry("description", "Description :", row=5)

    def get_submit_data(self):
        """Récupère les données pour le manager."""
        # On extrait l'ID de la combobox 'parent_id'
        parent_row = self.get_selected_row("parent_selection") or None

        data = {k: v.get().strip() for k, v in self.vars.items() if k != "parent_selection"}
        data["parent_id"] = parent_row["id"] if parent_row else None
        return data

    def _clear(self):
        """Réinitialise tous les champs du formulaire."""
        # On crée un dictionnaire avec des valeurs vides pour chaque clé de self.vars
        reset_values = {k: "" for k in self.vars.keys()}
        # Cas particulier pour la combobox
        if "parent_id" in reset_values:
            reset_values["parent_id"] = None

        self.set_values(reset_values)

