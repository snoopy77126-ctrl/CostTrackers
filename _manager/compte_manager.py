import inspect
from typing import Optional

from _manager._generique_manager import GenericManager
from databases.database import db
from models.banques import (
    Banque,
    CompteBase,
    CompteCourant,
    ComptePlacement,
    CompteCredit,
    CompteCreditConso,
)


class CompteManager(GenericManager):
    COMPTE_TYPES = {1: CompteCourant, 2: ComptePlacement, 3: CompteCredit, 4: CompteCreditConso}
    SQL_TABLE = "comptes"
    SQL_ID = "id_compte"
    MODEL_CLASS = CompteBase

    def _load_all_rows(self, actif_only=False):
        """Factorisation des requêtes de lecture."""
        where = "WHERE c.date_cloture = ''" if actif_only else ""
        sql = f"""
            SELECT c.*, b.label AS banque_label, b.identifiant AS banque_identifiant, b.description AS banque_desc
            FROM comptes c
            LEFT JOIN banques b ON c.banque_id = b.id_banque
            {where}
        """
        return self._execute_custom_select(sql)

    def _from_row(self, row) -> Optional[CompteBase]:
        if not row: return None

        # 1. Conversion propre des données (incluant les dates via le parent)
        data = self._convert_dates_in_row(dict(row))

        # 2. Gestion du polymorphisme
        compte_class = self.COMPTE_TYPES.get(data.get("type_compte_id"), CompteCourant)

        # 3. Construction de l'objet Banque
        banque_obj = None
        if data.get("banque_id"):
            banque_obj = Banque(
                id_banque=data.get("banque_id"),
                label=data.get("banque_label"),
                identifiant=data.get("banque_identifiant"),
                description=data.get("banque_desc")
            )

        # 4. Mapping final
        mapped_data = {
            "id_compte": data.get("id_compte"),
            "nom_du_compte": data.get("label"),
            "identifiant": data.get("numero"),
            "banque": banque_obj,
            # ... mapper le reste des champs en utilisant .get()
        }

        return compte_class(**{k: v for k, v in mapped_data.items() if v is not None})

    def _to_dict(self, obj):
        """Surcharge pour garantir le type_compte_id en écriture."""
        data = super()._to_dict(obj)
        if "type_compte_id" not in data:
            for tid, cls in self.COMPTE_TYPES.items():
                if isinstance(obj, cls):
                    data["type_compte_id"] = tid
                    break
        return data