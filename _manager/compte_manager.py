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
    COMPTE_TYPES = {
        1: CompteCourant,
        2: ComptePlacement,
        3: CompteCredit,
        4: CompteCreditConso,
    }

    SQL_TABLE = "comptes"

    # SQL_FIELDS contient les vraies colonnes physiques de votre table 'comptes'
    SQL_FIELDS = [
        "id_compte",
        "label",
        "numero",
        "description",
        "date_ouverture",
        "date_cloture",
        "solde_init",
        "solde_min",
        "solde_max",
        "compte_favori",
        "cache_le_compte",
        "decouvert_autorise",
        "type_compte_id",  # ID direct du type (1, 2, 3, 4)
        "banque_id",       # ID direct de la banque
        "date_der_rapprochement",
        "object_epargne",
    ]

    SQL_ID = "id_compte"
    MODEL_CLASS = CompteBase

    # ----------------------------------------------------------------------
    # Surcharges de lecture : Jointure directe pour obtenir un objet complet
    # ----------------------------------------------------------------------

    def _load_all_rows(self):
        """Sélectionne les comptes et intercepte les infos de la banque associée."""
        sql = """
            SELECT c.*, 
                   b.label AS banque_label, 
                   b.identifiant AS banque_identifiant, 
                   b.description AS banque_desc
            FROM comptes c
            LEFT JOIN banques b ON c.banque_id = b.id_banque
        """
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            return cur.fetchall()

    def _load_by_id(self, entity_id: int):
        """Sélectionne un compte unique avec les infos de sa banque."""
        sql = """
            SELECT c.*, 
                   b.label AS banque_label, 
                   b.identifiant AS banque_identifiant, 
                   b.description AS banque_desc
            FROM comptes c
            LEFT JOIN banques b ON c.banque_id = b.id_banque
            WHERE c.id_compte = ?
        """
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (entity_id,))
            return cur.fetchone()

    # ----------------------------------------------------------------------
    # Mapping SQL -> Objet Métier (Instanciation)
    # ----------------------------------------------------------------------

    def _from_row(self, row) -> Optional[CompteBase]:
        if row is None:
            return None

        row_dict = dict(row)

        # 1. Le type_compte_id est désormais direct (plus de table intermédiaire)
        type_compte_id = row_dict.get("type_compte_id")
        compte_class = self.COMPTE_TYPES.get(type_compte_id, CompteCourant)

        # 2. Construction de l'objet Banque complet grâce aux alias du LEFT JOIN
        banque_obj = None
        if row_dict.get("banque_id"):
            banque_obj = Banque(
                id_banque=row_dict.get("banque_id"),
                label=row_dict.get("banque_label"),
                identifiant=row_dict.get("banque_identifiant"),
                description=row_dict.get("banque_desc")
            )

        # 3. Préparation des arguments pour la Dataclass
        mapped_data = {
            "id_compte": row_dict.get("id_compte"),
            "nom_du_compte": row_dict.get("label"),
            "identifiant": row_dict.get("numero"),
            "description": row_dict.get("description"),
            "date_ouverture": row_dict.get("date_ouverture"),
            "date_cloture": row_dict.get("date_cloture"),
            "solde_init": row_dict.get("solde_init") or 0.0,
            "solde_min": row_dict.get("solde_min") or 0.0,
            "solde_max": row_dict.get("solde_max") or 0.0,
            "compte_favori": bool(row_dict.get("compte_favori")),
            "cache_le_compte": bool(row_dict.get("cache_le_compte")),
            "date_der_rapprochement": row_dict.get("date_der_rapprochement"),
            "banque": banque_obj,  # Injection de la banque complète
            # Attributs spécifiques aux classes filles
            "object_epargne": bool(row_dict.get("object_epargne")),
            "decouvert_autorise": row_dict.get("decouvert_autorise") or 0.0,
        }

        # Filtrage strict selon la signature de la dataclass ciblée
        valid_keys = inspect.signature(compte_class).parameters.keys()
        filtered_data = {k: v for k, v in mapped_data.items() if k in valid_keys}

        return compte_class(**filtered_data)

    # ----------------------------------------------------------------------
    # Mapping Objet -> SQL (Écritures / Mises à jour)
    # ----------------------------------------------------------------------

    def _to_dict(self, obj):
        data = super()._to_dict(obj)
        # type_compte_id : repli sur la classe Python si l'objet TypeCompte n'est pas peuplé
        if data.get("type_compte_id") is None:
            for type_id, cls in self.COMPTE_TYPES.items():
                if type(obj) is cls:
                    data["type_compte_id"] = type_id
                    break
        return data