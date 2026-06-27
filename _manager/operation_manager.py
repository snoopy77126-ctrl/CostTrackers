import inspect
from typing import Optional
from datetime import datetime

from _manager._generique_manager import GenericManager
from databases.database import db
from models.operations import OperationSaisie


class OperationManager(GenericManager):

    SQL_TABLE = "operations_bancaires_lignes"
    SQL_ID = "id_import_ligne"
    SQL_FIELDS = OperationSaisie.SQL_FIELDS
    MODEL_CLASS = OperationSaisie

    def __init__(self, CategoryTracker, TiersTracker, CompteTracker):
        super().__init__()

        self.cat_tracker = CategoryTracker
        self.tiers_tracker = TiersTracker
        self.compte_tracker = CompteTracker

    def _from_row(self, row) -> Optional[OperationSaisie]:
        if row is None:
            return None
        row_dict = dict(row)

        # --- NOUVEAU : Conversion des dates ---
        for date_field in ["date_operation", "date_valeur"]:
            val = row_dict.get(date_field)
            if isinstance(val, str):
                try:
                    # Conversion ISO vers objet date Python
                    row_dict[date_field] = datetime.strptime(val.split(" ")[0], "%Y-%m-%d").date()
                except ValueError:
                    row_dict[date_field] = None

        # Résolution des objets liés via trackers
        categorie_obj = None
        if row_dict.get("categorie_id"):
            categorie_obj = self.cat_tracker.get_by_id(row_dict["categorie_id"])

        compte_obj = None
        if row_dict.get("compte_id"):
            compte_obj = self.compte_tracker.get_by_id(row_dict["compte_id"])

        tiers_obj = None
        if row_dict.get("tiers_id"):
            tiers_obj = self.tiers_tracker.get_by_id(row_dict["tiers_id"])

        # On injecte les objets résolus sous les bons noms de champs du dataclass
        row_dict["compte_obj"]    = compte_obj
        row_dict["tiers_obj"]     = tiers_obj
        row_dict["categorie_obj"] = categorie_obj

        valid_params = inspect.signature(OperationSaisie).parameters.keys()
        final_kwargs = {k: v for k, v in row_dict.items() if k in valid_params}

        return OperationSaisie(**final_kwargs)

    def get_filtered(self, compte_id=None, date_debut=None, date_fin=None):
        sql = f"SELECT * FROM {self.SQL_TABLE} WHERE 1=1"
        params = []

        if compte_id and compte_id != "tlc":
            sql += " AND (compte_id = ? OR compte_dest_id = ?)"
            params.extend([compte_id, compte_id])

        if date_debut and date_fin:
            sql += " AND date_operation BETWEEN ? AND ?"
            params.extend([date_debut, date_fin])

        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return [self._from_row(row) for row in cursor.fetchall()]
    def migrer_liaisons_compte(self, ids_doublons: list, id_maitre: int) -> int:
        """Réaffecte toutes les opérations des comptes doublons vers le compte maître.
        Retourne le nombre de lignes mises à jour."""
        if not ids_doublons:
            return 0
        placeholders = ",".join("?" * len(ids_doublons))
        sql = f"""
            UPDATE {self.SQL_TABLE}
            SET compte_id = ?
            WHERE compte_id IN ({placeholders})
        """
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, [id_maitre] + ids_doublons)
            conn.commit()
            return cur.rowcount

    def migrer_liaisons_tiers(self, ids_doublons: list, id_maitre: int) -> int:
        """Réaffecte toutes les opérations des comptes doublons vers le compte maître.
        Retourne le nombre de lignes mises à jour."""
        if not ids_doublons:
            return 0
        placeholders = ",".join("?" * len(ids_doublons))
        sql = f"""
            UPDATE {self.SQL_TABLE}
            SET tiers_id = ?
            WHERE tiers_id IN ({placeholders})
        """
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, [id_maitre] + ids_doublons)
            conn.commit()
            return cur.rowcount

    def migrer_liaisons_categorie(self, ids_doublons: list, id_maitre: int) -> int:
        """Réaffecte toutes les opérations des catégories doublons vers la catégorie maître."""
        if not ids_doublons:
            return 0
        placeholders = ",".join("?" * len(ids_doublons))
        sql = f"""
            UPDATE {self.SQL_TABLE}
            SET categorie_id = ?
            WHERE categorie_id IN ({placeholders})
        """
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, [id_maitre] + ids_doublons)
            conn.commit()
            return cur.rowcount

