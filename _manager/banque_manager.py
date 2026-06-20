import inspect
from typing import Optional

from _manager._generique_manager import GenericManager
from models.banques import Banque


class BanqueManager(GenericManager):
    SQL_TABLE = "banques"
    SQL_FIELDS = ["id_banque", "label", "identifiant", "description"]
    SQL_ID = "id_banque"
    MODEL_CLASS = Banque

    def _from_row(self, row) -> Optional[Banque]:
        if row is None:
            return None
        row_dict = dict(row)
        valid_keys = inspect.signature(Banque).parameters.keys()
        filtered_dict = {k: v for k, v in row_dict.items() if k in valid_keys}
        return Banque(**filtered_dict)

