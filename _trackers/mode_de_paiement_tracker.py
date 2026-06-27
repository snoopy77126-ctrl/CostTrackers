import inspect
from typing import Optional
from typing import List

from _manager.mode_de_paiement_manager import MoyenDePaiementManager
from _trackers._generic_tracker import GenericTracker

class ModeDePaiementTracker(GenericTracker):
    def __init__(self):
        # On définit bien l'id_field pour que le parent travaille correctement
        super().__init__(MoyenDePaiementManager(), "id_mode_paiement")
        self._modes = {}

    def load_all(self) -> List[object]:
        items = self.manager.load_all()

        # Tri alphabétique si SORT_KEY est défini sur le tracker ou le manager
        sort_key = getattr(self, 'SORT_KEY', None) or getattr(self.manager, 'SORT_KEY', None)
        if sort_key:
            items.sort(key=lambda obj: (getattr(obj, sort_key, None) or "").lower())

        self._cache = [
            {"id": self._cache_key(item), "objet": item}
            for item in items
        ]
        self._is_initialized = True
        return self._cache_values()

    def get_all(self):
        if not self._is_initialized:
            return self.load_all()
        return list(self._modes.values())

    def get_by_id(self, mode_id: int):
        if not self._is_initialized:
            self.load_all()
        return self._modes.get(mode_id)

    def get_affected_paiement(self, obj_id: int):
        return self.manager.load_by_compte(obj_id)

    def get_by_code(self, code: str) -> Optional[object]:
        """Recherche un mode de paiement par son code."""
        for mode in self.get_all():
            if mode.code.upper() == code.upper():
                return mode
        return None

    def add(self, obj):
        # Appel via l'instance pour la cohérence avec GenericManager
        new_id = self.manager.insert(obj)
        if new_id:
            obj.id_mode_paiement = new_id
            self._modes[new_id] = obj
            return obj
        return None

    def create(self, code: str, designation: str = ""):
        """ Crée un nouveau ModeDePaiement à partir d'un code. """
        from models.mode_de_paiement import ModeDePaiement
        new_obj = ModeDePaiement(code=code, designation=designation)
        return super().add(new_obj)

    def update(self, obj):
        # Utilisation de l'instance self.manager
        success = self.manager.update(obj)
        if success:
            self._modes[obj.id_mode_paiement] = obj
        return success

    def delete(self, mode_id: int):
        # Utilisation de l'instance self.manager
        obj = self.get_by_id(mode_id)
        if obj and self.manager.delete(obj):
            self._modes.pop(mode_id, None)
            return True
        return False

    def clear_cache(self):
        self._modes.clear()
        self._is_initialized = False