import inspect
from typing import Optional
from typing import List

from _manager.mode_de_paiement_manager import MoyenDePaiementManager
from _trackers._generic_tracker import GenericTracker

class ModeDePaiementTracker(GenericTracker):
    def __init__(self):
        # On définit bien l'id_field pour que le parent travaille correctement
        super().__init__(MoyenDePaiementManager(), "id_mode_paiement")

    def get_all(self):
        return super().get_all()

    def get_by_id(self, mode_id: int):
        return super().get_by_id(mode_id)

    def get_affected_paiement(self, obj_id: int):
        return self.manager.load_by_compte(obj_id)

    def get_by_code(self, code: str) -> Optional[object]:
        """Recherche un mode de paiement par son code."""
        for mode in self.get_all():
            if mode.code.upper() == code.upper():
                return mode
        return None

    def create(self, code: str, designation: str = ""):
        """ Crée un nouveau ModeDePaiement à partir d'un code. """
        from models.mode_de_paiement import ModeDePaiement
        new_obj = ModeDePaiement(code=code, designation=designation)
        return super().add(new_obj)

    def add_liaison(self, compte_id: int, moyen_paiement_id: int) -> bool:
        return self.manager.add_liaison(compte_id, moyen_paiement_id)

    def remove_liaison(self, compte_id: int, moyen_paiement_id: int) -> bool:
        return self.manager.remove_liaison(compte_id, moyen_paiement_id)

    def remove_all_liaisons(self, compte_id: int) -> bool:
        return self.manager.remove_all_liaisons(compte_id)

    def get_all_modes(self):
        return self.manager.load_all_modes()
