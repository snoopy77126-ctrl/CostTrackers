import inspect
from typing import Optional, Union
from datetime import datetime

from _manager._generique_manager import GenericManager
from models.prevision import Prevision, PrevisionDetail
from databases.database import db

class PrevisionManager(GenericManager):
    """Manager unique pour gérer les Catégories (Racines) et les Sous-Catégories."""

    SQL_TABLE = "previsions"
    SQL_FIELDS = ["id_prevision", "libelle", "date_debut", "date_fin", "type_periode"]
    SQL_ID = "id_prevision"
    MODEL_CLASS = Prevision

    def _from_row(self, row) -> Optional[Prevision]:
        if row is None:
            return None
        row_dict = dict(row)

        # --- NOUVEAU : Conversion des dates ---
        for date_field in ["date_debut", "date_fin"]:
            val = row_dict.get(date_field)
            if isinstance(val, str):
                try:
                    # Conversion ISO vers objet date Python
                    row_dict[date_field] = datetime.strptime(val.split(" ")[0], "%Y-%m-%d").date()
                except ValueError:
                    row_dict[date_field] = None
        valid_params = inspect.signature(Prevision).parameters.keys()
        final_kwargs = {k: v for k, v in row_dict.items() if k in valid_params}

        return Prevision(**final_kwargs)


class PrevisionDetailManager(GenericManager):
    """Manager unique pour gérer les Catégories (Racines) et les Sous-Catégories."""

    SQL_TABLE = "prevision_details"
    SQL_FIELDS = ["id_detail", "prevision_id", "libelle", "montant", "categorie_id"]
    SQL_ID = "id_detail"
    MODEL_CLASS = PrevisionDetail

    def _from_row(self, row) -> Optional[Prevision]:
        if row is None:
            return None
        row_dict = dict(row)
        valid_keys = inspect.signature(PrevisionDetail).parameters.keys()
        filtered_dict = {k: v for k, v in row_dict.items() if k in valid_keys}
        return PrevisionDetail(**filtered_dict)
