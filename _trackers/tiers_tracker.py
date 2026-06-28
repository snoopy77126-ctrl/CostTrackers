import inspect
from typing import Optional
from typing import List

from _manager.tiers_manager import TiersManager
from _trackers._generic_tracker import GenericTracker

class TiersTracker(GenericTracker):
    def __init__(self):
        # On définit bien l'id_field pour que le parent travaille correctement
        super().__init__(TiersManager(), "id_tiers")

    def get_all(self):
        result = super().get_all()
        return result

    def get_by_id(self, tiers_id: int):
        return super().get_by_id(tiers_id)

    def get_by_name(self, name: str) -> Optional[dict]:
        """Recherche un tier par son nom (nom_du_compte) """
        # On parcourt le cache local des objets géré par le GenericTracker (ex: self.all_objects ou self.get_all())
        for tier in self.get_all():
            # Selon vos modèles, adaptez .nom_du_compte et .identifiant
            if tier.display_short == name :
                return tier
        return None

    def create(self, name: str):
        """ Crée un nouveau Tier à partir d'un nom. """
        from models.tiers import Tier
        # Création d'un objet Tier avec le nom
        new_obj = Tier(nom=name)
        # Enregistrement en BDD + mise en cache via la méthode add() du parent
        # add() retourne l'objet si succès, None sinon
        return super().add(new_obj)

