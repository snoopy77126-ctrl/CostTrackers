from interfaces_tabs._tabs_generique_data import BaseFormFrame


class ModePaiementData(BaseFormFrame):
    def __init__(self, parent, callbacks=None):
        super().__init__(parent, title="Fiche Mode de Paiement", callbacks=callbacks)

        # Section Identité
        self.add_entry("code", "Code (ex: CB, ESP, VIR) :", row=0)
        self.add_entry("designation", "Désignation :", row=1)
        self.add_entry("description", "Description :", row=2)
        self.add_checkbox("actif", "Actif", row=3)

    def get_submit_data(self):
        """Récupère les données pour le manager."""
        data = {}
        for k, v in self.vars.items():
            if k == "actif":
                data[k] = v.get()
            else:
                data[k] = v.get().strip()
        return data

    def _clear(self):
        """Réinitialise tous les champs du formulaire."""
        reset_values = {
            "code": "",
            "designation": "",
            "description": "",
            "actif": True
        }
        self.set_values(reset_values)
