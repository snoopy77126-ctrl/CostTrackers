import inspect
from typing import Optional

from _manager._generique_manager import GenericManager
from models.banques import TypeCompte


class TypeCompteManager(GenericManager):
    SQL_TABLE = "type_de_compte"
    MODEL_CLASS = TypeCompte
    SQL_ID     = MODEL_CLASS.SQL_ID
    SQL_FIELDS = MODEL_CLASS.SQL_FIELDS

    def _from_row(self, row) -> Optional[TypeCompte]:
        if row is None:
            return None
        row_dict = dict(row)
        valid_keys = inspect.signature(TypeCompte).parameters.keys()
        return TypeCompte(**{k: v for k, v in row_dict.items() if k in valid_keys})
