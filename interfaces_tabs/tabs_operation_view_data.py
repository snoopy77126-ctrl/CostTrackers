from interfaces_tabs._tabs_generique_data import BaseFormFrame


class CompteFiltreData(BaseFormFrame):
    def __init__(self, parent, callbacks=None):
        super().__init__(parent, callbacks=callbacks)
        self._snapshot = {}
        self.show_selected_file = ""

        # Construction de l'interface
        self.build_widgets()

    def build_widgets(self):
        """Orchestrateur de la vue."""
        self.add_combobox("compte", "Compte :", on_select=self._on_compte_change)
        self.add_combobox('periode','Période', on_select=self._on_periode_change)

    def _on_compte_change(self, row):
        if "on_compte_change" in self.callbacks:
            # On récupère l'objet row complet (ex: {'key': 1, 'value': 'ARCHIVES'})
            self.callbacks["on_compte_change"](row)

    def _on_periode_change(self, row):
        if "on_periode_change" in self.callbacks:
            # On récupère l'objet row complet (ex: {'key': 1, 'value': 'ARCHIVES'})
            self.callbacks["on_periode_change"](row)

