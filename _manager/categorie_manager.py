from typing import Optional, Union

from _manager._generique_manager import GenericManager
from models.categories import CategorieParent, Categorie
from databases.database import db


class CategorieManager(GenericManager):
    """Manager unique pour gérer les Catégories (Racines) et les Sous-Catégories."""

    SQL_TABLE = "categories"
    SQL_FIELDS = ["id_categorie", "designation", "parent_id"]
    SQL_ID = "id_categorie"
    MODEL_CLASS = Categorie

    def _from_row(self, row, model_class) -> Optional[Union[CategorieParent, Categorie]]:
        """Transforme une ligne SQL en objet métier selon la classe spécifiée."""
        if row is None:
            return None

        row_dict = dict(row)
        data = {
            "id_categorie": row_dict.get("id_categorie"),
            "designation": row_dict.get("designation"),
        }
        return model_class(**data)

    def load_all_sorted(self):
        """Charge tout via la Vue SQL et construit l'arborescence en un seul passage."""

        # 1. On interroge la vue que vous avez créée dans la base (DBeaver)
        sql = "SELECT cat_id, cat_nom, sscat_id, sscat_nom FROM vue_categories_hierarchie"

        # 2. On utilise le même gestionnaire de connexion que le GenericManager
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()

        categories = []
        ss_categories = []
        temp_map = {}

        # 3. Un seul passage de boucle pour tout assembler
        for row in rows:
            # Conversion en dict pour garantir l'accès par nom de colonne
            row_dict = dict(row)
            cat_id = row_dict["cat_id"]

            # --- Gestion du Parent ---
            if cat_id not in temp_map:
                cat_obj = CategorieParent(id_categorie=cat_id, designation=row_dict["cat_nom"])
                cat_obj.ss_categories = []

                categories.append(cat_obj)
                temp_map[cat_id] = cat_obj
            else:
                cat_obj = temp_map[cat_id]

            # --- Gestion de l'Enfant ---
            if row_dict["sscat_id"] is not None:
                sscat_obj = Categorie(
                    id_categorie=row_dict["sscat_id"],
                    designation=row_dict["sscat_nom"]
                )

                # Double liaison (Parent -> Enfant ET Enfant -> Parent)
                sscat_obj.categorie = cat_obj
                cat_obj.ss_categories.append(sscat_obj)

                ss_categories.append(sscat_obj)

        return categories, ss_categories

    def load_all(self):
        """Retourne une liste plate de toutes les catégories unifiées."""
        categories, ss_categories = self.load_all_sorted()
        return categories + ss_categories

    def load_by_id(self, selected_id: int) -> Optional[Union[CategorieParent, Categorie]]:
        """Charge une catégorie par son ID et détermine dynamiquement son type."""
        if not selected_id:
            return None

        # Exemple de requête personnalisée utilisant GenericManager concept
        rows = self._load_all_rows()  # Ou une méthode de recherche par ID de votre GenericManager
        row = next((r for r in rows if r[self.SQL_ID] == selected_id), None)

        if not row:
            return None

        is_root = row["parent_id"] in (None, "", 0)
        model_class = CategorieParent if is_root else Categorie
        return self._from_row(row, model_class)

    def insert(self, obj: Union[CategorieParent, Categorie]) -> Union[int, bool]:
        """Insère un objet CategorieParent ou Categorie en base de données."""
        # Préparation des données communes
        designation = obj.designation.strip().upper() if obj.designation else ""

        # Détermination du parent_id
        parent_id = None
        if isinstance(obj, Categorie):
            # On récupère l'ID depuis l'objet CategorieParent lié
            if hasattr(obj, 'categorie') and obj.categorie:
                parent_id = obj.categorie.id_categorie

        data = {
            "designation": designation,
            "parent_id": parent_id
        }

        try:
            # Utilisation de la méthode d'insertion du GenericManager
            new_id = self._insert(data)
            if new_id:
                obj.id_categorie = new_id
                return new_id
            return False
        except Exception as e:
            print(f"[ERROR] Erreur lors de l'insertion de la catégorie : {e}")
            return False

    def update(self, obj: Union[CategorieParent, Categorie]) -> bool:
        """Met à jour une catégorie ou sous-catégorie existante."""
        if not getattr(obj, self.SQL_ID, None):
            return False

        designation = obj.designation.strip().upper() if obj.designation else ""

        parent_id = None
        if isinstance(obj, Categorie) and hasattr(obj, 'categorie') and obj.categorie:
            parent_id = obj.categorie.id_categorie

        data = {
            "designation": designation,
            "parent_id": parent_id
        }

        # Appel du _update de GenericManager
        return self._update(getattr(obj, self.SQL_ID), data)

    def delete_categorie(self, categorie_id: int) -> bool:
        """Supprime un enregistrement via son ID."""
        # Si votre GenericManager possède une méthode générique de suppression :
        if hasattr(self, '_delete'):
            return self._delete(categorie_id)
        # Sinon, implémentation brute ou via exécuteur du GenericManager
        return False

    def migrer_liaisons_categorie(self, ids_doublons: list, id_maitre: int) -> int:
        """Réaffecte toutes les opérations des catégories doublons vers la catégorie maître."""
        if not ids_doublons:
            return 0
        placeholders = ",".join("?" * len(ids_doublons))
        sql = f"""
            UPDATE {self.SQL_TABLE}
            SET parent_id = ?
            WHERE parent_id IN ({placeholders})
        """
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, [id_maitre] + ids_doublons)
            conn.commit()
            return cur.rowcount

