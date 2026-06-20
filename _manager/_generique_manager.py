from typing import Dict

from databases.database import db


class GenericManager:
    SQL_TABLE = ""
    SQL_FIELDS = []
    SQL_ID = "id"

    def __init__(self):
        self.connection = db.get_connection()

    # -------------------
    # SQL BASE
    # -------------------

    def _load_all_rows(self):
        sql = f"SELECT {', '.join(self.SQL_FIELDS)} FROM {self.SQL_TABLE}"
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            return cur.fetchall()

    def _load_by_id(self, entity_id: int):
        sql = f"""
        SELECT {', '.join(self.SQL_FIELDS)}
        FROM {self.SQL_TABLE}
        WHERE {self.SQL_ID} = ?
        """
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (entity_id,))
            return cur.fetchone()

    def _insert(self, data: Dict):
        cols = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))

        sql = f"""
        INSERT INTO {self.SQL_TABLE} ({cols})
        VALUES ({placeholders})
        """
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, list(data.values()))
            conn.commit()
            return cur.lastrowid if cur.lastrowid else None

    def _update(self, entity_id: int, data: Dict):
        fields = ", ".join([f"{k} = ?" for k in data.keys()])
        sql = f"""
        UPDATE {self.SQL_TABLE}
        SET {fields}
        WHERE {self.SQL_ID} = ?
        """

        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, list(data.values()) + [entity_id])
            conn.commit()
            return cur.rowcount > 0

    def _delete(self, entity_id: int):
        sql = f"""
        DELETE FROM {self.SQL_TABLE}
        WHERE {self.SQL_ID} = ?
        """

        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (entity_id,))
            conn.commit()
            return cur.rowcount > 0

    # -------------------
    # HOOKS (à surcharger)
    # -------------------

    def _from_row(self, row):
        """Override dans chaque manager"""
        raise NotImplementedError

    def _to_dict(self, obj):
        """Override si besoin"""
        if hasattr(obj, "to_sql_dict"):
            return obj.to_sql_dict()
        return obj.to_dict()

    # -------------------
    # API publique
    # -------------------

    def load_all(self):
        return [self._from_row(r) for r in self._load_all_rows()]

    def load_by_id(self, entity_id: int):
        row = self._load_by_id(entity_id)
        return self._from_row(row)

    def delete(self, obj):
        if getattr(obj, self.SQL_ID, None):
            self._delete(getattr(obj, self.SQL_ID))
            return True
        return False

    def insert(self, obj):
        data = self._to_dict(obj)
        data.pop(self.SQL_ID, None)
        new_id = self._insert(data)

        if new_id:
            setattr(obj, self.SQL_ID, new_id)
            return new_id
        return None

    def update(self, obj):
        entity_id = getattr(obj, self.SQL_ID, None)
        if not entity_id:
            return False

        data = self._to_dict(obj)
        data.pop(self.SQL_ID, None)
        self._update(entity_id, data)
        return True

    def create(self, **kwargs):
        """
        Crée une nouvelle instance de l'objet géré par ce manager.
        Si MODEL_CLASS est absent, crée un objet générique pour éviter le None.
        """
        model_class = getattr(self, 'MODEL_CLASS', None)

        if model_class is not None:
            return model_class(**kwargs)

        # SECRITÉ : Si MODEL_CLASS n'existe pas, on crée une classe à la volée
        # pour que get_target_columns puisse quand même fonctionner.
        class GenericPlaceholder:
            def __init__(self, **entries):
                self.__dict__.update(entries)

        # On initialise avec les champs connus si vous en avez,
        # sinon on retourne un objet vide mais instancié
        return GenericPlaceholder(**kwargs)
