# -*- coding: utf-8 -*-
####################################
# Projet : CostTracker
# Fichier : _trackers/periodique_tracker.py
# Description : Cache mémoire pour les périodiques
# Date : 23/06/2026     Etat : Stable
####################################

from datetime import date
from typing import List, Optional

from _manager.periodique_manager import PeriodiqueManager
from _trackers._generic_tracker import GenericTracker
from models.periodiques import Periodique


class PeriodiqueTracker(GenericTracker):
    def __init__(self, cat_tracker=None, tiers_tracker=None, compte_tracker=None):
        super().__init__(PeriodiqueManager(), "id_periodique")
        self._cache_dict: dict[int, Periodique] = {}
        self._cat_tracker    = cat_tracker
        self._tiers_tracker  = tiers_tracker
        self._compte_tracker = compte_tracker

    # ── Cache ─────────────────────────────────────────────────────────

    def _hydrate(self, obj: Periodique) -> Periodique:
        """Rattache les objets liés (catégorie, tiers, compte)."""
        if self._cat_tracker and obj.categorie_id:
            obj.categorie_obj = self._cat_tracker.get_by_id(obj.categorie_id)
        if self._tiers_tracker and obj.tiers_id:
            obj.tiers_obj = self._tiers_tracker.get_by_id(obj.tiers_id)
        if self._compte_tracker and obj.compte_id:
            obj.compte_obj = self._compte_tracker.get_by_id(obj.compte_id)
        return obj

    def load_all(self) -> List[Periodique]:
        items = self.manager.load_all()
        for obj in items:
            self._hydrate(obj)
        self._cache_dict = {obj.id_periodique: obj for obj in items if obj}
        self._is_initialized = True
        return list(self._cache_dict.values())

    def get_all(self) -> List[Periodique]:
        if not self._is_initialized:
            return self.load_all()
        return list(self._cache_dict.values())

    def get_by_id(self, pid: int) -> Optional[Periodique]:
        if not self._is_initialized:
            self.load_all()
        return self._cache_dict.get(pid)

    def clear_cache(self):
        self._cache_dict.clear()
        self._is_initialized = False

    # ── CRUD ──────────────────────────────────────────────────────────

    def add(self, obj: Periodique) -> Optional[Periodique]:
        new_id = self.manager.insert(obj)
        if new_id:
            obj.id_periodique = new_id
            self._hydrate(obj)
            self._cache_dict[new_id] = obj
            return obj
        return None

    def update(self, obj: Periodique) -> bool:
        success = self.manager.update(obj)
        if success:
            self._hydrate(obj)
            self._cache_dict[obj.id_periodique] = obj
        return success

    def delete(self, pid: int) -> bool:
        if self.manager.delete(pid):
            self._cache_dict.pop(pid, None)
            return True
        return False

    def create(self) -> Periodique:
        return self.manager.create()

    # ── Génération des échéances ──────────────────────────────────────

    def get_echeances_dues(self, jusqu_au: date = None) -> List[Periodique]:
        """Retourne les périodiques actifs dont l'échéance est passée ou aujourd'hui."""
        if until := jusqu_au or date.today():
            return [p for p in self.get_all() if p.actif and p.date_prochaine and p.date_prochaine <= until]
        return []

    def avancer_echeance(self, obj: Periodique) -> bool:
        """Avance la date_prochaine et met à jour le cache."""
        success = self.manager.avancer_echeance(obj)
        if success:
            self._cache_dict[obj.id_periodique] = obj
        return success
