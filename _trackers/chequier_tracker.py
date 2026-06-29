from typing import List, Optional

from _manager.chequier_manager import ChequierEditionManager
from _trackers._generic_tracker import GenericTracker
from models.mode_de_paiement import ChequierEdition


class ChequierTracker(GenericTracker):
    def __init__(self):
        super().__init__(ChequierEditionManager(), "id_carnet_cheque")

    def get_by_compte(self, compte_id: int) -> List[ChequierEdition]:
        """Retourne les chéquiers du compte (depuis DB, pas le cache global)."""
        return self.manager.load_by_compte(compte_id)

    def save(self, obj: ChequierEdition) -> bool:
        ok = self.manager.save(obj)
        if ok:
            # Mise à jour du cache
            self._cache_set(obj.id_carnet_cheque, obj)
        return ok

    def delete(self, obj: ChequierEdition) -> bool:
        ok = self.manager.delete(obj)
        if ok:
            self._cache_pop(obj.id_carnet_cheque)
        return ok
