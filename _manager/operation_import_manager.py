# -*- coding: utf-8 -*-
from _manager._generique_manager import GenericManager
from models.operations import OperationImport, ImportBancaire


class FileImportManager(GenericManager):
    """Gère la table imports_bancaires (métadonnées fichier)."""

    SQL_TABLE = "imports_bancaires"
    SQL_ID    = "id_import"
    SQL_FIELDS = [
        "id_import", "fichier", "chemin", "format_fichier",
        "checksum", "nb_lignes", "statut", "message",
    ]
    MODEL_CLASS = ImportBancaire

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
    SQL_ID    = "id_import_ligne"
    SQL_FIELDS = [
        "id_import_ligne",
        "id_import",
        "numero_ligne",
        "date_operation",
        "date_valeur",
        "libelle",
        "montant",
        "type_operation",
        "commentaire",
        "source",
        # Textes bruts issus du fichier
        "compte_num",
        "compte_label",
        "solde_compte",
        "tiers",
        "categorie",
        "categorie_parent",
        # OFX
        "fitid",
        "trntype",
        # Divers
        "raw_json",
        "import_key",
        "created_at",
        # IDs résolus
        "compte_id",
        "tiers_id",
        "categorie_id",
    ]
    MODEL_CLASS = OperationImport

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