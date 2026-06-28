# -*- coding: utf-8 -*-
####################################
# Projet : CostTracker
# Fichier : _manager/budget_manager.py
# Description : Manager CRUD pour les lignes budgétaires
# Date : 24/06/2026     Etat : Stable
####################################

import inspect
from typing import List, Optional
from datetime import date

from _manager._generique_manager import GenericManager
from databases.database import db
from models.budget import BudgetLigne


class BudgetManager(GenericManager):

    SQL_TABLE  = "budget_lignes"
    MODEL_CLASS = BudgetLigne
    SQL_ID     = MODEL_CLASS.SQL_ID
    SQL_FIELDS = MODEL_CLASS.SQL_FIELDS

    def __init__(self):
        super().__init__()

    def _from_row(self, row) -> Optional[BudgetLigne]:
        if row is None:
            return None
        row_dict = dict(row)
        valid = set(inspect.signature(BudgetLigne).parameters.keys())
        return BudgetLigne(**{k: v for k, v in row_dict.items() if k in valid})

    def load_all(self) -> List[BudgetLigne]:
        sql = (f"SELECT {', '.join(self.SQL_FIELDS)} FROM {self.SQL_TABLE} "
               f"ORDER BY annee, mois, categorie_id")
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            return [self._from_row(r) for r in cur.fetchall()]

    def load_by_periode(self, mois: int, annee: int) -> List[BudgetLigne]:
        sql = (f"SELECT {', '.join(self.SQL_FIELDS)} FROM {self.SQL_TABLE} "
               f"WHERE mois = ? AND annee = ? ORDER BY categorie_id")
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (mois, annee))
            return [self._from_row(r) for r in cur.fetchall()]

    def load_by_categorie(self, categorie_id: int) -> List[BudgetLigne]:
        sql = (f"SELECT {', '.join(self.SQL_FIELDS)} FROM {self.SQL_TABLE} "
               f"WHERE categorie_id = ? ORDER BY annee, mois")
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (categorie_id,))
            return [self._from_row(r) for r in cur.fetchall()]

    def get_or_create(self, categorie_id: int, mois: int, annee: int,
                      type_flux: str = "depense") -> BudgetLigne:
        """Retourne la ligne existante ou crée une vide (non persistée)."""
        sql = (f"SELECT {', '.join(self.SQL_FIELDS)} FROM {self.SQL_TABLE} "
               f"WHERE categorie_id = ? AND mois = ? AND annee = ?")
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (categorie_id, mois, annee))
            row = cur.fetchone()
            if row:
                return self._from_row(row)
        return BudgetLigne(
            categorie_id=categorie_id, mois=mois, annee=annee, type_flux=type_flux
        )

    def insert(self, obj: BudgetLigne) -> Optional[int]:
        d = obj.to_sql_dict()
        d.pop("id_budget", None)
        cols  = ", ".join(d.keys())
        marks = ", ".join(["?"] * len(d))
        sql   = f"INSERT INTO {self.SQL_TABLE} ({cols}) VALUES ({marks})"
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, list(d.values()))
            conn.commit()
            return cur.lastrowid

    def update(self, obj: BudgetLigne) -> bool:
        d = obj.to_sql_dict()
        d.pop("id_budget", None)
        sets = ", ".join(f"{k} = ?" for k in d)
        sql  = f"UPDATE {self.SQL_TABLE} SET {sets} WHERE id_budget = ?"
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, [*d.values(), obj.id_budget])
            conn.commit()
            return cur.rowcount > 0

    def delete(self, id_budget: int) -> bool:
        sql = f"DELETE FROM {self.SQL_TABLE} WHERE id_budget = ?"
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (id_budget,))
            conn.commit()
            return cur.rowcount > 0

    def create(self) -> BudgetLigne:
        today = date.today()
        return BudgetLigne(mois=today.month, annee=today.year)
