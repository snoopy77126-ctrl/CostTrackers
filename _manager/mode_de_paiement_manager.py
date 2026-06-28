import inspect
from typing import List, Optional

from _manager._generique_manager import GenericManager
from databases.database import db
from models.mode_de_paiement import ModeDePaiement


class MoyenDePaiementManager(GenericManager):
    MODEL_CLASS  = ModeDePaiement
    SQL_TABLE = MODEL_CLASS.SQL_TABLE
    SQL_ID     = MODEL_CLASS.SQL_ID
    SQL_FIELDS = MODEL_CLASS.SQL_FIELDS

    def __init__(self):
        # On appelle le parent sans argument
        super().__init__()


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
            query = f"SELECT {', '.join(self.SQL_FIELDS)} FROM {self.SQL_TABLE} WHERE id_mode_paiement = ?"
            cur.execute(query, (mode_id,))
            return self._from_row(cur.fetchone())

    def load_actifs(self) -> List[ModeDePaiement]:
        """Charge uniquement les modes de paiement actifs."""
        with db.get_connection() as conn:
            cur = conn.cursor()
            query = f"SELECT {', '.join(self.SQL_FIELDS)} FROM {self.SQL_TABLE} WHERE actif = 1 ORDER BY code"
            cur.execute(query)
            rows = cur.fetchall()
            return [self._from_row(row) for row in rows]

    def load_by_code(self, code: str) -> Optional[ModeDePaiement]:
        """Recherche un mode de paiement par son code."""
        with db.get_connection() as conn:
            cur = conn.cursor()
            query = f"SELECT {', '.join(self.SQL_FIELDS)} FROM {self.SQL_TABLE} WHERE code = ?"
            cur.execute(query, (code,))
            return self._from_row(cur.fetchone())

    def load_by_compte(self, compte_id: int) -> List[ModeDePaiement]:
        """Charge les modes de paiement associés à un compte spécifique."""
        with db.get_connection() as conn:
            cur = conn.cursor()
            # On joint les deux tables pour filtrer par compte_id
            query = f"""
                SELECT m.{', m.'.join(self.SQL_FIELDS)} 
                FROM {self.SQL_TABLE} m
                JOIN liason_moyen_paiement l ON m.id_mode_paiement = l.moyen_paiement_id
                WHERE l.compte_id = ?
                ORDER BY m.code
            """
            cur.execute(query, (compte_id,))
            rows = cur.fetchall()
            return [self._from_row(row) for row in rows]


    def add_liaison(self, compte_id: int, moyen_paiement_id: int) -> bool:
        """Ajoute une liaison compte ↔ moyen de paiement si elle n'existe pas déjà."""
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT 1 FROM liason_moyen_paiement WHERE compte_id=? AND moyen_paiement_id=?",
                (compte_id, moyen_paiement_id)
            )
            if cur.fetchone():
                return True  # déjà liée
            cur.execute(
                "INSERT INTO liason_moyen_paiement (compte_id, moyen_paiement_id) VALUES (?,?)",
                (compte_id, moyen_paiement_id)
            )
            conn.commit()
            return True

    def remove_liaison(self, compte_id: int, moyen_paiement_id: int) -> bool:
        """Retire la liaison compte ↔ moyen de paiement."""
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM liason_moyen_paiement WHERE compte_id=? AND moyen_paiement_id=?",
                (compte_id, moyen_paiement_id)
            )
            conn.commit()
            return True

    def remove_all_liaisons(self, compte_id: int) -> bool:
        """Retire toutes les liaisons d'un compte."""
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM liason_moyen_paiement WHERE compte_id=?",
                (compte_id,)
            )
            conn.commit()
            return True

    def load_all_modes(self) -> List[ModeDePaiement]:
        """Charge tous les modes de paiement."""
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT {', '.join(self.SQL_FIELDS)} FROM {self.SQL_TABLE} ORDER BY code")
            return [self._from_row(r) for r in cur.fetchall()]
