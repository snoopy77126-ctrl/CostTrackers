import inspect
from typing import Optional, Type, TypeVar

from _manager._generique_manager import GenericManager
from models.mode_de_paiement import ChequierEdition


class ChequierEditionManager(GenericManager):
    SQL_TABLE = "type_de_compte"
    MODEL_CLASS = ChequierEdition
    SQL_ID     = MODEL_CLASS.SQL_ID
    SQL_FIELDS = MODEL_CLASS.SQL_FIELDS

    # Optionnel : pour aider l'autocomplétion (Type Hinting)
    T = TypeVar("T", bound=ChequierEdition)

    def _from_row(self, row) -> Optional[ChequierEdition]:
        if row is None:
            return None

        row_dict = dict(row)

        # On utilise directement la classe importée pour la signature
        valid_keys = inspect.signature(self.MODEL_CLASS).parameters.keys()

        # On filtre les données
        filtered_data = {k: v for k, v in row_dict.items() if k in valid_keys}

        # On instancie
        return self.MODEL_CLASS(**filtered_data)