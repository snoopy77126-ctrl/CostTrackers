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
    MODEL_CLASS = CompteBase
    SQL_ID     = MODEL_CLASS.SQL_ID
    SQL_FIELDS = MODEL_CLASS.SQL_FIELDS



    def _load_all_rows(self, actif_only=False):
        """Factorisation des requêtes de lecture."""
        where = "WHERE c.date_cloture = ''" if actif_only else ""
        sql = f"""
            SELECT c.*,
                   b.label AS banque_label, b.identifiant AS banque_identifiant, b.description AS banque_desc,
                   t.designation AS type_designation
            FROM comptes c
            LEFT JOIN banques b ON c.banque_id = b.id_banque
            LEFT JOIN type_de_compte t ON c.type_compte_id = t.id_type_de_compte
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

        # 3b. Construction de l'objet TypeCompte
        from models.banques import TypeCompte
        type_compte_obj = None
        if data.get("type_compte_id"):
            type_compte_obj = TypeCompte(
                id_type_de_compte=data.get("type_compte_id"),
                designation=data.get("type_designation") or "",
            )

        # 4. Mapping final — tous les champs de la table comptes
        mapped_data = {
            "id_compte":              data.get("id_compte"),
            "nom_du_compte":          data.get("label"),
            "identifiant":            data.get("numero"),
            "description":            data.get("description"),
            "date_ouverture":         data.get("date_ouverture"),
            "date_cloture":           data.get("date_cloture"),
            "date_der_rapprochement": data.get("date_der_rapprochement"),
            "solde_init":             data.get("solde_init"),
            "solde_min":              data.get("solde_min"),
            "solde_max":              data.get("solde_max"),
            "compte_favori":          bool(data.get("compte_favori", False)),
            "cache_le_compte":        bool(data.get("cache_le_compte", False)),
            "banque":                 banque_obj,
            "type_compte":            type_compte_obj,
            # Champs CompteCourant
            "object_epargne":         bool(data.get("object_epargne", False)),
            "decouvert_autorise":     data.get("decouvert_autorise"),
            # Champs CompteCredit / ComptePlacement
            "taux_interet":           data.get("taux_interet"),
            "montant":                data.get("montant"),
            "montant_max":            data.get("montant_max"),
            "remboursement_mini":     data.get("remboursement_mini"),
            "periode_type":           data.get("periode_type"),
            "periode_value":          data.get("periode_value"),
            "remboursement_periode":  data.get("remboursement_periode"),
            "duree_periode":          data.get("duree_periode"),
            "duree_value":            data.get("duree_value"),
        }

        valid_keys = inspect.signature(compte_class).parameters.keys()
        return compte_class(**{k: v for k, v in mapped_data.items() if k in valid_keys})

    def _to_dict(self, obj):
        """Surcharge pour garantir le type_compte_id en écriture."""
        data = super()._to_dict(obj)
        if "type_compte_id" not in data:
            for tid, cls in self.COMPTE_TYPES.items():
                if isinstance(obj, cls):
                    data["type_compte_id"] = tid
                    break
        return data

    def load_by_mode_paiement(self, mode_paiement_id: int):
        """Charge les comptes associés à un mode de paiement spécifique."""
        sql = f"""
            SELECT c.*,
                   b.label AS banque_label, b.identifiant AS banque_identifiant, b.description AS banque_desc,
                   t.designation AS type_designation
            FROM comptes c
            LEFT JOIN banques b ON c.banque_id = b.id_banque
            LEFT JOIN type_de_compte t ON c.type_compte_id = t.id_type_de_compte
            JOIN liason_moyen_paiement l ON c.id_compte = l.compte_id
            WHERE l.moyen_paiement_id = ?
        """
        return self._execute_custom_select(sql, (mode_paiement_id,))