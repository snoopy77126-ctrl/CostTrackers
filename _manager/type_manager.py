import inspect
from typing import Optional

from _manager._generique_manager import GenericManager
from models.banques import TypeCompte


class TypeCompteManager(GenericManager):
    SQL_TABLE = "type_de_compte"
    SQL_FIELDS = ["id_type_de_compte", "designation"]
    SQL_ID = "id_type_de_compte"

    def _from_row(self, row) -> Optional[TypeCompte]:
        if row is None:
            return None
        row_dict = dict(row)
        valid_keys = inspect.signature(TypeCompte).parameters.keys()
        return TypeCompte(**{k: v for k, v in row_dict.items() if k in valid_keys})
