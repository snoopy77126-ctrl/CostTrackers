
# Fichier : _trackers\operation_tracker.py

from _manager.operation_manager import OperationManager
from _trackers._generic_tracker import GenericTracker


class OperationTracker(GenericTracker):
    def __init__(self, manager, id_field="id_import_ligne"):
        super().__init__(manager, id_field)

    def get_recent(self, limit=250):
        if not self._is_initialized:
            self.load_all()
        return self.get_all()[:limit]

    def migrer_liaisons_compte(self, ids_doublons: list, id_maitre: int) -> int:
        """Délègue la migration des compte_id au manager et vide le cache."""
        nb = self.manager.migrer_liaisons_compte(ids_doublons, id_maitre)
        self.clear_cache()
        print(f"[DEBUG] OperationTracker.migrer_liaisons_compte : {nb} ligne(s) migrée(s)")
        return nb

    def migrer_liaisons_compte(self, ids_doublons: list, id_maitre: int) -> int:
        """Délègue la migration des compte_id au manager et vide le cache."""
        nb = self.manager.migrer_liaisons_tiers(ids_doublons, id_maitre)
        self.clear_cache()
        print(f"[DEBUG] OperationTracker.migrer_liaisons_compte : {nb} ligne(s) migrée(s)")
        return nb


class OperationImportTracker(GenericTracker):
    def __init__(self, manager, id_field="id_import_ligne"):
        super().__init__(manager, id_field)

    def get_recent(self, limit=250):
        if not self._is_initialized:
            self.load_all()
        return self.get_all()[:limit]

class FileImportTracker(GenericTracker):
    def __init__(self, manager, id_field="id_import"):
        super().__init__(manager, id_field)

