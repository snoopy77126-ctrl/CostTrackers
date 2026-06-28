# -*- coding: utf-8 -*-
####################################
# Projet : CostTracker
# Fichier : _manager/periodique_manager.py
# Description : Manager CRUD pour les périodiques
# Date : 23/06/2026     Etat : Stable
####################################

import inspect
from datetime import date, timedelta, datetime
from typing import List, Optional

from _manager._generique_manager import GenericManager
from databases.database import db
from models.periodiques import Periodique


# ── Calcul de la prochaine échéance ──────────────────────────────────

def _prochaine_echeance(depuis: date, frequence: str) -> date:
    """Calcule la date suivante selon la fréquence."""
    if frequence == "mensuel":
        month = depuis.month + 1
        year  = depuis.year + month // 13
        month = month if month <= 12 else month - 12
        try:
            return depuis.replace(year=year, month=month)
        except ValueError:
            # Fin de mois (ex: 31 janv → 28 fév)
            import calendar
            last_day = calendar.monthrange(year, month)[1]
            return depuis.replace(year=year, month=month, day=last_day)
    elif frequence == "trimestriel":
        month = depuis.month + 3
        year  = depuis.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        try:
            return depuis.replace(year=year, month=month)
        except ValueError:
            import calendar
            last_day = calendar.monthrange(year, month)[1]
            return depuis.replace(year=year, month=month, day=last_day)
    elif frequence == "semestriel":
        month = depuis.month + 6
        year  = depuis.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        try:
            return depuis.replace(year=year, month=month)
        except ValueError:
            import calendar
            last_day = calendar.monthrange(year, month)[1]
            return depuis.replace(year=year, month=month, day=last_day)
    elif frequence == "annuel":
        try:
            return depuis.replace(year=depuis.year + 1)
        except ValueError:
            return depuis.replace(year=depuis.year + 1, day=28)
    return depuis


class PeriodiqueManager(GenericManager):
    MODEL_CLASS = Periodique
    SQL_FIELDS = Periodique.SQL_FIELDS
    SQL_ID     = MODEL_CLASS.SQL_ID
    SQL_FIELDS = MODEL_CLASS.SQL_FIELDS

    def __init__(self):
        super().__init__()
        self.SQL_FIELDS = Periodique.SQL_FIELDS
        self.SQL_ID     = "id_periodique"

    # ── Constructeur depuis ligne BDD ─────────────────────────────────

    def _from_row(self, row) -> Optional[Periodique]:
        if row is None:
            return None
        row_dict = dict(row)

        for date_field in ["date_prochaine"]:
            val = row_dict.get(date_field)
            if isinstance(val, str):
                try:
                    # Conversion ISO vers objet date Python
                    row_dict[date_field] = datetime.strptime(val.split(" ")[0], "%Y-%m-%d").date()
                except ValueError:
                    row_dict[date_field] = None

        valid = set(inspect.signature(Periodique).parameters.keys())
        return Periodique(**{k: v for k, v in row_dict.items() if k in valid})

    # ── Lecture ───────────────────────────────────────────────────────

    def load_all(self) -> List[Periodique]:
        sql = f"SELECT {', '.join(self.SQL_FIELDS)} FROM {self.SQL_TABLE} ORDER BY libelle"
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            return [self._from_row(r) for r in cur.fetchall()]

    def load_actifs(self) -> List[Periodique]:
        sql = f"SELECT {', '.join(self.SQL_FIELDS)} FROM {self.SQL_TABLE} WHERE actif = 1 ORDER BY libelle"
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            return [self._from_row(r) for r in cur.fetchall()]

    def load_by_id(self, pid: int) -> Optional[Periodique]:
        sql = f"SELECT {', '.join(self.SQL_FIELDS)} FROM {self.SQL_TABLE} WHERE id_periodique = ?"
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (pid,))
            return self._from_row(cur.fetchone())

    def load_echeances_dues(self, jusqu_au: date = None) -> List[Periodique]:
        """Retourne les périodiques actifs dont la date_prochaine est <= jusqu_au."""
        if jusqu_au is None:
            jusqu_au = date.today()
        sql = (
            f"SELECT {', '.join(self.SQL_FIELDS)} FROM {self.SQL_TABLE} "
            f"WHERE actif = 1 AND date_prochaine <= ? ORDER BY date_prochaine"
        )
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (jusqu_au.isoformat(),))
            return [self._from_row(r) for r in cur.fetchall()]

    # ── Écriture ──────────────────────────────────────────────────────

    def insert(self, obj: Periodique) -> Optional[int]:
        d = obj.to_sql_dict()
        d.pop("id_periodique", None)
        cols   = ", ".join(d.keys())
        marks  = ", ".join(["?"] * len(d))
        sql    = f"INSERT INTO {self.SQL_TABLE} ({cols}) VALUES ({marks})"
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, list(d.values()))
            conn.commit()
            return cur.lastrowid

    def update(self, obj: Periodique) -> bool:
        d = obj.to_sql_dict()
        d.pop("id_periodique", None)
        sets = ", ".join(f"{k} = ?" for k in d)
        sql  = f"UPDATE {self.SQL_TABLE} SET {sets} WHERE id_periodique = ?"
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, [*d.values(), obj.id_periodique])
            conn.commit()
            return cur.rowcount > 0

    def delete(self, pid: int) -> bool:
        sql = f"DELETE FROM {self.SQL_TABLE} WHERE id_periodique = ?"
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (pid,))
            conn.commit()
            return cur.rowcount > 0

    # ── Avancement de la date_prochaine ───────────────────────────────

    def avancer_echeance(self, obj: Periodique) -> bool:
        """Calcule la prochaine date et l'enregistre."""
        if not obj.date_prochaine:
            return False
        nouvelle = _prochaine_echeance(obj.date_prochaine, obj.frequence)
        obj.date_prochaine = nouvelle
        return self.update(obj)

    # ── Création d'un objet vide ──────────────────────────────────────

    def create(self) -> Periodique:
        return Periodique(date_prochaine=date.today())
