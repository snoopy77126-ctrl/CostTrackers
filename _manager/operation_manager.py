import inspect
from typing import Optional

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
