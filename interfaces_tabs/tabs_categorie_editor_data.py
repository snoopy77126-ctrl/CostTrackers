from interfaces_tabs._tabs_generique_data import BaseFormFrame


class CategorieData(BaseFormFrame):
    def __init__(self, parent, callbacks=None):
        super().__init__(parent, title="Classement", callbacks=callbacks)

        self.add_combobox("categorie", "Se référe à :", row=0, on_select=self._on_categorie_change)
        self.add_entry("designation", "Libellé :", row=1)

    def _clear(self):
        """Réinitialise tous les champs du formulaire."""
        # On passe un dictionnaire de reset à set_values
        self.set_values({
            "categorie": None,
            "designation": ""
        })

    def _on_categorie_change(self, val):
        if "on_categorie_change" in self.callbacks:
            # On récupère l'objet row complet (ex: {'key': 1, 'value': 'ARCHIVES'})
            selected_row = self.get_selected_row("categorie")
            self.callbacks["on_categorie_change"](selected_row)

