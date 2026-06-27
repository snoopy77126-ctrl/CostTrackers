from typing import List, Optional


class GenericTracker:
    def __init__(self, manager, id_field: str):
        self.manager = manager
        self.id_field = id_field

        self._cache: List[dict] = []
        self._is_initialized: bool = False

    # ------------------- CACHE LIST [{id, objet}] -------------------

    def _cache_key(self, obj):
        return getattr(obj, self.id_field, None)

    def _cache_values(self) -> List[object]:
        return [row["objet"] for row in self._cache]

    def _cache_get(self, obj_id):
        for row in self._cache:
            if row["id"] == obj_id:
                return row["objet"]
        return None

    def _cache_set(self, obj_id, obj):
        for row in self._cache:
            if row["id"] == obj_id:
                row["objet"] = obj
                return
        self._cache.append({"id": obj_id, "objet": obj})

    def _cache_pop(self, obj_id):
        self._cache = [row for row in self._cache if row["id"] != obj_id]

    # ------------------- LOAD -------------------

    def load_all(self) -> List[object]:
        items = self.manager.load_all()

        # Lecture du SORT_KEY depuis MODEL_CLASS du manager
        model_class = getattr(self.manager, 'MODEL_CLASS', None)
        sort_key = getattr(model_class, 'SORT_KEY', None)
        if sort_key:
            items.sort(key=lambda obj: (getattr(obj, sort_key, None) or "").lower())

        self._cache = [
            {"id": self._cache_key(item), "objet": item}
            for item in items
        ]
        self._is_initialized = True
        return self._cache_values()

    # ------------------- GET -------------------
    def get_new(self) -> Optional[object]:
        return self.manager.create()

    def get_all(self) -> List[object]:
        if not self._is_initialized:
            return self.load_all()

        # Réappliquer le tri si nécessaire avant de retourner la liste
        items = self._cache_values()
        model_class = getattr(self.manager, 'MODEL_CLASS', None)
        sort_key = getattr(model_class, 'SORT_KEY', None)
        if sort_key:
            items.sort(key=lambda obj: (getattr(obj, sort_key, None) or "").lower())
        return items

    def get_by_id(self, obj_id: any) -> Optional[object]:
        if not self._is_initialized:
            self.load_all()

        if isinstance(obj_id, dict):
            # On extrait la clé 'iid_key' ou toute clé contenant 'id'
            if 'iid_key' in obj_id:
                obj_id = obj_id['iid_key']
            else:
                # Sécurité si la clé change ('id', 'id_emetteur', etc.)
                id_key = next((k for k in obj_id.keys() if 'id' in k.lower()), None)
                obj_id = obj_id.get(id_key) if id_key else None

        # Si obj_id est un objet métier (juste au cas où)
        elif hasattr(obj_id, '__dict__') or hasattr(obj_id, 'SQL_ID'):
            sql_id_attr = getattr(obj_id, 'SQL_ID', 'id')
            obj_id = getattr(obj_id, sql_id_attr, None)

        # Si l'ID est introuvable ou non valide, on s'arrête proprement
        if obj_id is None or obj_id == "":
            return None

        # Conversion en entier au cas où l'ID extrait soit resté sous forme de chaîne
        try:
            obj_id = int(obj_id)
        except (ValueError, TypeError):
            pass

        return self._cache_get(obj_id)

    def save(self, obj):
        if not obj:
            return False

        key = getattr(obj, self.id_field, None)
        if key in (None, "", 0):
            new_id = self.manager.insert(obj)

            if new_id:
                setattr(obj, self.id_field, new_id)
                self._cache_set(new_id, obj)
                return True
            return False

        success = self.manager.update(obj)
        if success:
            self._cache_set(key, obj)
        return success

    def add(self, obj):
        return obj if self.save(obj) else None

    def update(self, obj):
        if not obj:
            return False

        key = getattr(obj, self.id_field, None)
        if key in (None, "", 0):
            return False

        success = self.manager.update(obj)
        if success:
            self._cache_set(key, obj)
        return success

    # ------------------- DELETE -------------------

    def delete(self, obj) -> bool:
        if not hasattr(obj, self.id_field):
            obj = self.get_by_id(obj)
            if not obj:
                return False

        # On récupère l'ID de l'objet pour nettoyer le cache
        obj_id = getattr(obj, self.id_field, None)
        if obj_id and self.manager.delete(obj):
            self._cache_pop(obj_id)
            return True
        return False

    # ------------------- BULK SAVE -------------------

    def save_all(self, operations: list) -> dict:
        """Insère ou met à jour une liste d'objets et retourne un bilan."""
        inserted, errors = 0, 0
        for op in operations:
            if self.save(op):
                inserted += 1
            else:
                errors += 1
        return {"inserted": inserted, "errors": errors}

    # ------------------- CLEAR -------------------

    def clear_cache(self):
        self._cache.clear()
        self._is_initialized = False


