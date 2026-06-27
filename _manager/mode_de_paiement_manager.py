import inspect
from typing import List, Optional

from _manager._generique_manager import GenericManager
from databases.database import db
from models.mode_de_paiement import ModeDePaiement


class MoyenDePaiementManager(GenericManager):
    MODEL_CLASS  = ModeDePaiement
    SQL_TABLE = "mode_de_paiement"
    SQL_ID = "id_mode_paiement"  # Défini pour GenericManager

    SQL_CHAMPS = [
        "id_mode_paiement", "code", "designation", "description"
    ]

    def __init__(self, mode_paiement_tracker=None):
        # On appelle le parent sans argument
        super().__init__()
        # On stocke l'argument localement dans la classe enfant
        self.mode_paiement_tracker = mode_paiement_tracker
        # Indispensable pour que GenericManager fonctionne
        self.SQL_FIELDS = self.SQL_CHAMPS
        self.SQL_ID = "id_mode_paiement"

    def _from_row(self, row) -> Optional[ModeDePaiement]:
        if row is None:
            return None
        row_dict = dict(row)
        valid_keys = inspect.signature(ModeDePaiement).parameters.keys()
        filtered_dict = {k: v for k, v in row_dict.items() if k in valid_keys}
        return ModeDePaiement(**filtered_dict)

    def load_by_id(self, mode_id: int) -> Optional[ModeDePaiement]:
        """Utilise le nom de colonne correct : id_mode_paiement"""
        with db.get_connection() as conn:
            cur = conn.cursor()
            query = f"SELECT {', '.join(self.SQL_CHAMPS)} FROM {self.SQL_TABLE} WHERE id_mode_paiement = ?"
            cur.execute(query, (mode_id,))
            return self._from_row(cur.fetchone())

    def load_actifs(self) -> List[ModeDePaiement]:
        """Charge uniquement les modes de paiement actifs."""
        with db.get_connection() as conn:
            cur = conn.cursor()
            query = f"SELECT {', '.join(self.SQL_CHAMPS)} FROM {self.SQL_TABLE} WHERE actif = 1 ORDER BY code"
            cur.execute(query)
            rows = cur.fetchall()
            return [self._from_row(row) for row in rows]

    def load_by_code(self, code: str) -> Optional[ModeDePaiement]:
        """Recherche un mode de paiement par son code."""
        with db.get_connection() as conn:
            cur = conn.cursor()
            query = f"SELECT {', '.join(self.SQL_CHAMPS)} FROM {self.SQL_TABLE} WHERE code = ?"
            cur.execute(query, (code,))
            return self._from_row(cur.fetchone())

    def load_by_compte(self, compte_id: int) -> List[ModeDePaiement]:
        """Charge les modes de paiement associés à un compte spécifique."""
        with db.get_connection() as conn:
            cur = conn.cursor()
            # On joint les deux tables pour filtrer par compte_id
            query = f"""
                SELECT m.{', m.'.join(self.SQL_CHAMPS)} 
                FROM {self.SQL_TABLE} m
                JOIN liason_moyen_paiement l ON m.id_mode_paiement = l.moyen_paiement_id
                WHERE l.compte_id = ?
                ORDER BY m.code
            """
            cur.execute(query, (compte_id,))
            rows = cur.fetchall()
            return [self._from_row(row) for row in rows]
