import inspect
from typing import Optional, List, TypeVar

from _manager._generique_manager import GenericManager
from models.mode_de_paiement import ChequierEdition


class ChequierEditionManager(GenericManager):
    MODEL_CLASS = ChequierEdition
    SQL_TABLE   = MODEL_CLASS.SQL_TABLE    # "carnet_cheque"
    SQL_ID      = MODEL_CLASS.SQL_ID       # "id_carnet_cheque"
    SQL_FIELDS  = MODEL_CLASS.SQL_FIELDS

    T = TypeVar("T", bound=ChequierEdition)

    def _from_row(self, row) -> Optional[ChequierEdition]:
        if row is None:
            return None
        row_dict = dict(row)
        row_dict = self._convert_dates_in_row(row_dict)
        valid_keys = inspect.signature(self.MODEL_CLASS).parameters.keys()
        filtered = {k: v for k, v in row_dict.items() if k in valid_keys}
        return self.MODEL_CLASS(**filtered)

    # --- Requêtes métier ---

    def load_by_compte(self, compte_id: int) -> List[ChequierEdition]:
        """Retourne tous les chéquiers d'un compte donné."""
        fields = ", ".join(self.SQL_FIELDS)
        sql = f"SELECT {fields} FROM {self.SQL_TABLE} WHERE compte_id = ? ORDER BY chequier_num"
        rows = self._execute_custom_select(sql, (compte_id,))
        return [self._from_row(r) for r in rows]

    def save(self, obj: ChequierEdition) -> bool:
        """Insert ou update selon la présence de l'id."""
        if obj.id_carnet_cheque:
            return self.update(obj)
        else:
            new_id = self.insert(obj)
            return new_id is not None
