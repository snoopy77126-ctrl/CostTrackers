
# Fichier : _trackers\ops_trackers.py

from _trackers._generic_tracker import GenericTracker
from _services.dates_services import DatesManager

class OperationTracker(GenericTracker):
    def __init__(self, manager, id_field="id_import_ligne"):
        super().__init__(manager, id_field)

    def get_recent(self, limit=250):
        """Lecture directe en base, sans cache."""
        return self.manager.get_filtered(compte_id=None, date_debut=None, date_fin=None)[:limit]

    def get_filtered(self, compte_id, periode_key):
        """Lecture directe en base selon compte et période."""
        d_debut, d_fin = DatesManager.get_date_bounds(periode_key)
        return self.manager.get_filtered(compte_id=compte_id, date_debut=d_debut, date_fin=d_fin)

    def migrer_liaisons_compte(self, ids_doublons: list, id_maitre: int) -> int:
        """Délègue la migration des compte_id au manager et vide le cache."""
        nb = self.manager.migrer_liaisons_compte(ids_doublons, id_maitre)
        self.clear_cache()
        print(f"[DEBUG] OperationTracker.migrer_liaisons_compte : {nb} ligne(s) migrée(s)")
        return nb

    def migrer_liaisons_tiers(self, ids_doublons: list, id_maitre: int) -> int:
        """Délègue la migration des compte_id au manager et vide le cache."""
        nb = self.manager.migrer_liaisons_tiers(ids_doublons, id_maitre)
        self.clear_cache()
        print(f"[DEBUG] OperationTracker.migrer_liaisons_compte : {nb} ligne(s) migrée(s)")
        return nb

    def migrer_liaisons_categorie(self, ids_doublons: list, id_maitre: int) -> int:
        """Délègue la migration des categorie_id au manager et vide le cache."""
        nb = self.manager.migrer_liaisons_categorie(ids_doublons, id_maitre)
        self.clear_cache()
        print(f"[DEBUG] OperationTracker.migrer_liaisons_categorie : {nb} ligne(s) migrée(s)")
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

