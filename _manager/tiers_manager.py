import inspect
from typing import List, Optional

from _manager._generique_manager import GenericManager
from databases.database import db
from models.tiers import Tier, Organisation


class TiersManager(GenericManager):
    MODEL_CLASS  = Tier
    SQL_TABLE = "tiers"
    SQL_ID = "id_tiers"  # Défini pour GenericManager

    SQL_CHAMPS = [
        "id_tiers", "titre", "nom", "prenom", "organisation",
        "description", "montant_max", "montant_min"
    ]

    def __init__(self, tiers_tracker=None):
        # On appelle le parent sans argument
        super().__init__()
        # On stocke l'argument localement dans la classe enfant
        self.tiers_tracker = tiers_tracker
        # Indispensable pour que GenericManager fonctionne
        self.SQL_FIELDS = self.SQL_CHAMPS
        self.SQL_ID = "id_tiers"

    def _from_row(self, row) -> Optional[Tier]:
        if row is None:
            return None
        row_dict = dict(row)
        valid_keys = inspect.signature(Tier).parameters.keys()
        filtered_dict = {k: v for k, v in row_dict.items() if k in valid_keys}
        return Tier(**filtered_dict)

    def load_by_id(self, tiers_id: int) -> Optional[Tier]:
        """Utilise le nom de colonne correct : id_tiers"""
        with db.get_connection() as conn:
            cur = conn.cursor()
            query = f"SELECT {', '.join(self.SQL_CHAMPS)} FROM {self.SQL_TABLE} WHERE id_tiers = ?"
            cur.execute(query, (tiers_id,))
            return self._from_row(cur.fetchone())

    def load_all_organisation(self) -> List[Organisation]:
        """ Correction du filtre : organisation au lieu de entreprise. """
        with db.get_connection() as conn:
            cur = conn.cursor()
            query = f"SELECT {', '.join(self.SQL_CHAMPS)} FROM {self.SQL_TABLE} WHERE organisation IS NOT NULL ORDER BY organisation, nom"
            cur.execute(query)
            rows = cur.fetchall()
            return [self._from_row(row) for row in rows]

