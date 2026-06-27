# -*- coding: utf-8 -*-
####################################
# Projet : CostTracker
# Fichier : _trackers/budget_tracker.py
# Description : Cache mémoire pour les lignes budgétaires
# Date : 24/06/2026     Etat : Stable
####################################

from typing import List, Optional
from datetime import date

from _manager.budget_manager import BudgetManager
from _trackers._generic_tracker import GenericTracker
from models.budget import BudgetLigne


class BudgetTracker(GenericTracker):
    def __init__(self, cat_tracker=None):
        super().__init__(BudgetManager(), "id_budget")
        self._cat_tracker = cat_tracker
        self._cache_list: List[BudgetLigne] = []

    # ── Hydratation ───────────────────────────────────────────────────

    def _hydrate(self, obj: BudgetLigne) -> BudgetLigne:
        if self._cat_tracker and obj.categorie_id:
            obj.categorie_obj = self._cat_tracker.get_by_id(obj.categorie_id)
        return obj

    # ── Cache ─────────────────────────────────────────────────────────

    def load_all(self) -> List[BudgetLigne]:
        items = self.manager.load_all()
        for obj in items:
            self._hydrate(obj)
        self._cache_list = [o for o in items if o]
        self._is_initialized = True
        return self._cache_list

    def get_all(self) -> List[BudgetLigne]:
        if not self._is_initialized:
            return self.load_all()
        return self._cache_list

    def get_by_id(self, id_budget: int) -> Optional[BudgetLigne]:
        if not self._is_initialized:
            self.load_all()
        return next((b for b in self._cache_list if b.id_budget == id_budget), None)

    def get_by_periode(self, mois: int, annee: int) -> List[BudgetLigne]:
        if not self._is_initialized:
            self.load_all()
        return [b for b in self._cache_list if b.mois == mois and b.annee == annee]

    def clear_cache(self):
        self._cache_list.clear()
        self._is_initialized = False

    # ── CRUD ──────────────────────────────────────────────────────────

    def add(self, obj: BudgetLigne) -> Optional[BudgetLigne]:
        new_id = self.manager.insert(obj)
        if new_id:
            obj.id_budget = new_id
            self._hydrate(obj)
            self._cache_list.append(obj)
            return obj
        return None

    def update(self, obj: BudgetLigne) -> bool:
        success = self.manager.update(obj)
        if success:
            self._hydrate(obj)
            for i, b in enumerate(self._cache_list):
                if b.id_budget == obj.id_budget:
                    self._cache_list[i] = obj
                    break
        return success

    def delete(self, id_budget: int) -> bool:
        if self.manager.delete(id_budget):
            self._cache_list = [b for b in self._cache_list if b.id_budget != id_budget]
            return True
        return False

    def save(self, obj: BudgetLigne) -> bool:
        if obj.id_budget:
            return self.update(obj)
        result = self.add(obj)
        return result is not None

    def create(self) -> BudgetLigne:
        return self.manager.create()

    def get_or_create(self, categorie_id: int, mois: int, annee: int,
                      type_flux: str = "depense") -> BudgetLigne:
        existing = next(
            (b for b in self.get_all()
             if b.categorie_id == categorie_id and b.mois == mois and b.annee == annee),
            None
        )
        return existing or self.manager.get_or_create(categorie_id, mois, annee, type_flux)
