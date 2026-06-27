import inspect
from typing import Optional
from typing import List

from _manager.tiers_manager import TiersManager
from _trackers._generic_tracker import GenericTracker

class TiersTracker(GenericTracker):
    def __init__(self):
        # On définit bien l'id_field pour que le parent travaille correctement
        super().__init__(TiersManager(), "id_tiers")
        self._tiers = {}

    def load_all(self) -> List[object]:
        items = self.manager.load_all()

        # Tri alphabétique si SORT_KEY est défini sur le cat_trackers ou le manager
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
        return list(self._tiers.values())

    def get_by_id(self, tiers_id: int):
        if not self._is_initialized:
            self.load_all()
        return self._tiers.get(tiers_id)

    def get_by_name(self, name: str) -> Optional[dict]:
        """Recherche un tier par son nom (nom_du_compte) """
        # On parcourt le cache local des objets géré par le GenericTracker (ex: self.all_objects ou self.get_all())
        for tier in self.get_all():
            # Selon vos modèles, adaptez .nom_du_compte et .identifiant
            if tier.display_short == name :
                return tier
        return None

    def add(self, obj):
        # Appel via l'instance pour la cohérence avec GenericManager
        new_id = self.manager.insert(obj)
        if new_id:
            obj.id_tiers = new_id
            self._tiers[new_id] = obj
            return obj
        return None

    def create(self, name: str):
        """ Crée un nouveau Tier à partir d'un nom. """
        from models.tiers import Tier
        # Création d'un objet Tier avec le nom
        new_obj = Tier(nom=name)
        # Enregistrement en BDD + mise en cache via la méthode add() du parent
        # add() retourne l'objet si succès, None sinon
        return super().add(new_obj)

    def update(self, obj):
        # Utilisation de l'instance self.manager
        success = self.manager.update(obj)
        if success:
            self._tiers[obj.id_tiers] = obj
        return success

    def delete(self, tiers_id: int):
        # Utilisation de l'instance self.manager
        obj = self.get_by_id(tiers_id)
        if obj and self.manager.delete(obj):
            self._tiers.pop(tiers_id, None)
            return True
        return False

    def clear_cache(self):
        self._tiers.clear()
        self._is_initialized = False

