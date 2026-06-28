from typing import List

class ChequierEditorHelpers:
    def __init__(self, services=None):
        self.services = services or {}
        self.mode_paiement_tracker = self.services.get('mode_de_paiement')
        self.compte_tracker = self.services.get('compte')

    def get_first_compte_id(self):
        id_mode_paiement = self.mode_paiement_tracker.get_by_code("CHQ")
        if id_mode_paiement:
            compte_list = self.compte_tracker.manager.load_by_mode_paiement(id_mode_paiement.id_mode_paiement)
            if compte_list:
                return compte_list[0]['id_compte']
        return None