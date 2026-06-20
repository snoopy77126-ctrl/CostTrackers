from typing import List

from _manager.categorie_manager import CategorieManager
from _trackers._generic_tracker import GenericTracker
from models.categories import SSCategorie, Categorie


class CategoryTracker(GenericTracker):
    def __init__(self):
        # On définit bien l'id_field pour que le parent travaille correctement
        super().__init__(CategorieManager(), "id_categorie")
        self._categories = []
        self._ss_categories = []

    def load_all(self):
        """
        On indexe simplement les objets complets fournis par le manager.
        """
        # 1. On vide tout proprement
        self._categories.clear()
        self._ss_categories.clear()
        self._cache.clear()

        # 2. On recupere explicitement les deux familles reconstruites par le manager.
        categories_list, ss_categories_list = self.manager.load_all_sorted()

        # 3. Rangement immédiat de toutes les Catégories
        for item in categories_list:
            # On remplit le cache principal (clé = ID entier)
            self._cache_set(item.id_categorie, item)
            # On remplit l'index spécifique
            self._categories.append({"id": f"a_{item.id_categorie}", "objet": item})

        # 3.bis Rangement immédiat de toutes les Sous-Catégories
        for item in ss_categories_list:
            # On remplit le cache principal (clé = ID entier)
            self._cache_set(item.id_categorie, item)
            # On remplit l'index spécifique
            self._ss_categories.append({"id": f"c_{item.id_categorie}", "objet": item})

        # 4. On valide l'initialisation pour GenericTracker
        self._is_initialized = True

        return self._cache_values()

    def _register(self, obj):
        """Surcharge interne pour maintenir les dictionnaires spécialisés."""
        # On laisse le parent gérer le cache principal (_cache)
        # En utilisant getattr(obj, self.id_field) si nécessaire, ou plus simplement :
        self._cache_set(obj.id_categorie, obj)

        if isinstance(obj, Categorie):
            self._set_special_cache(self._categories, f"a_{obj.id_categorie}", obj)
        elif isinstance(obj, SSCategorie):
            self._set_special_cache(self._ss_categories, f"c_{obj.id_categorie}", obj)

    @staticmethod
    def _set_special_cache(cache, row_id, obj):
        for row in cache:
            if row["id"] == row_id:
                row["objet"] = obj
                return
        cache.append({"id": row_id, "objet": obj})

    @staticmethod
    def _special_values(cache):
        return [row["objet"] for row in cache]

    @staticmethod
    def _special_get(cache, row_id):
        for row in cache:
            if row["id"] == row_id:
                return row["objet"]
        return None

    def from_dict(self, data):
        """ Transforme les données UI en Objet Métier. """
        id_cat = data.get("id_categorie")
        designation = data.get("designation")
        categorie_info = data.get("categorie")
        if not categorie_info:
            return Categorie(designation=designation, id_categorie=id_cat)

        # On récupère l'ID (numérique ou iid_key)
        p_id = categorie_info.get("id_categorie") or categorie_info.get("iid_key")
        if isinstance(p_id, str) and "_" in p_id:
            p_id = int(p_id.split("_")[1])

        # RÉSOLUTION : On transforme l'ID en objet categorie via le cache du parent
        obj_categorie = self.get_by_id(p_id)

        return SSCategorie(
            id_categorie=id_cat,
            designation=designation,
            categorie=obj_categorie  # On passe l'objet, pas l'ID
        )

    def get_categories(self) -> List[Categorie]:
        # Si le parent dit que ce n'est pas initialisé, on lance le chargement
        if not self._is_initialized:
            self.load_all()
        return self._special_values(self._categories)

    def get_ss_categories(self) -> List[SSCategorie]:
        if not self._is_initialized:
            self.load_all()
        return self._special_values(self._ss_categories)

    def get_by_iid(self, iid_key: str):
        """Accès direct via l'index spécialisé."""
        if iid_key.startswith("a_"):
            return self._special_get(self._categories, iid_key)
        if iid_key.startswith("c_"):
            return self._special_get(self._ss_categories, iid_key)
        return None

    def delete(self, obj_categorie) -> bool:
        # 1. Appel au parent pour suppression DB et Cache principal
        if super().delete(obj_categorie):
            # 2. Nettoyage spécifique aux dictionnaires de CategoryTracker
            category_id = getattr(obj_categorie, "id_categorie", None) or getattr(obj_categorie, "id", None)
            self._categories = [row for row in self._categories if row["id"] != f"a_{category_id}"]
            self._ss_categories = [row for row in self._ss_categories if row["id"] != f"c_{category_id}"]
            # Nettoyage des enfants orphelins (logique métier)
            self._ss_categories = [
                row for row in self._ss_categories
                if row["objet"].categorie and row["objet"].categorie.id_categorie != category_id
            ]
            return True
        return False

    def get_by_name_and_parent(self, name: str, parent_name: str):
        """
        Recherche une catégorie (ou sous-catégorie) par sa désignation et le nom de son parent.
        """
        # --- SÉCURITÉ : Si c'est la catégorie automatique pour les lignes vides ---
        if name.strip().lower() == "À catégoriser" and not parent_name:
            # On cherche si elle existe déjà dans le cache
            for item in self.get_categories():
                if item.designation.strip().lower() == "À catégoriser":
                    return item
            # Si elle n'existe pas encore en BDD, on la crée silencieusement ici
            print("[INFO] Création automatique de la catégorie par défaut 'À catégoriser'")
            return self.create(name="À catégoriser", parent_name="")

        # --- Code de recherche normal (inchangé) ---
        if parent_name:
            for item in self.get_ss_categories():
                if (item.designation.strip().lower() == name.strip().lower() and
                        item.categorie and
                        item.categorie.designation.strip().lower() == parent_name.strip().lower()):
                    return item
        else:
            for item in self.get_categories():
                if item.designation.strip().lower() == name.strip().lower():
                    return item
        return None

    def get_by_display_string(self, display_string: str):
        """
        Retrouve l'objet Categorie ou SSCategorie à partir de la chaîne affichée dans le Combobox.
        Formats gérés : "Nom" ou "Nom de la Catégorie Mère: Sous-Catégorie"
        """
        # 1. On cherche d'abord dans les sous-catégories en comparant avec votre propriété .display_name
        for item in self.get_ss_categories():
            # item.display_name renvoie déjà "NomParent: NomEnfant" d'après votre modèle categories.py
            if item.display_name == display_string:
                return item

        # 2. Si non trouvé, on cherche dans les catégories principales
        for item in self.get_categories():
            if item.display_name == display_string:
                return item

        return None

    def create(self, name: str, parent_name: str):
        """ Crée une nouvelle Catégorie ou SSCategorie en fonction de la présence d'un parent. """

        if parent_name:
            # On cherche si le parent existe déjà pour lier la sous-catégorie
            parent_obj = None
            for p in self.get_categories():
                if p.designation.strip().lower() == parent_name.strip().lower():
                    parent_obj = p
                    break

            # Si le parent n'existe pas encore, on le crée d'abord !
            if not parent_obj:
                parent_obj = self.create(name=parent_name, parent_name="")

            # Préparation des données d'interface attendues par from_dict()
            data = {
                "designation": name,
                "categorie": {
                    "id_categorie": parent_obj.id_categorie,
                    "designation": parent_obj.designation
                }
            }
        else:
            # Création d'une catégorie racine standard
            data = {
                "designation": name,
                "categorie": None
            }

        # Conversion d'un dictionnaire UI brut en objet Dataclass métier
        new_obj = self.from_dict(data)

        # Enregistrement en BDD + mise en cache via la méthode add() de GenericTracker
        # add() retourne l'objet si succès, None sinon (contrairement à save() qui retourne un booléen)
        return self.add(new_obj)

