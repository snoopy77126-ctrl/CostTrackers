# -*- coding: utf-8 -*-
from _manager._generique_manager import GenericManager
from models.operations import OperationImport, ImportBancaire


class FileImportManager(GenericManager):
    """Gère la table imports_bancaires (métadonnées fichier)."""

    SQL_TABLE = "imports_bancaires"
    MODEL_CLASS = ImportBancaire
    SQL_ID     = MODEL_CLASS.SQL_ID
    SQL_FIELDS = MODEL_CLASS.SQL_FIELDS

    def __init__(self):
        super().__init__()

    def _from_row(self, row):
        if not row:
            return None
        data = dict(row)
        return ImportBancaire.from_dict(data)


class OperationImportManager(GenericManager):
    """
    Gère la table imports_bancaires_lignes.
    Sert pour les imports bancaires ET les saisies manuelles (distingués par 'source').
    """

    SQL_TABLE = "operations_bancaires_lignes"
    MODEL_CLASS = OperationImport
    SQL_ID     = MODEL_CLASS.SQL_ID
    SQL_FIELDS = MODEL_CLASS.SQL_FIELDS

    def __init__(self):
        super().__init__()

    def _from_row(self, row):
        if not row:
            return None
        return OperationImport.from_dict(dict(row))

    def insertpourtest(self, obj):
        print("[DEBUG] OperationImportManager.insert")
        print(f"[DEBUG] obj={obj}")

        result = super().insert(obj)

        print(f"[DEBUG] result={result}")
        data = self._to_dict(obj)
        print(f"[DEBUG] import_key={data.get('import_key')}")
        return result