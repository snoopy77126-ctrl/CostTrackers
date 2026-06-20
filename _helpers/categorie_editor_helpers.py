from typing import List, Optional

from ._generique_helpers import BaseHelper


class CategorieEditorHelpers(BaseHelper):
    """
    Helper pour l'éditeur de catégories.
    Hérite de BaseHelper pour la résolution des clés étrangères.
    """

    def __init__(self, services):
        # On passe le dictionnaire de tiers_trackers au BaseHelper
        super().__init__(services)
        self.tracker = services.get('categorie')

    def initialise(self):
        self.tracker.clear_cache()

    def fetch_row_complet(self) -> List[dict]:
        """ Récupère et formate les catégories pour le TreeView. """
        self.tracker.clear_cache()
        categorie = self.tracker.get_categories()
        ss_categorie = self.tracker.get_ss_categories()
        ui_rows = []

        # 1. Formatage des categorie (Noeuds parents)
        for arm in categorie:
            ui_rows.append({
                "iid_key": f"a_{arm.id_categorie}",
                "id_categorie": arm.id_categorie,
                "value": (arm.designation or "").upper(),
                "parent_id": None,
                "actif": True
            })

        # 2. Formatage des ss_categorie (Noeuds enfants)
        for cls in ss_categorie:
            # On utilise la relation objet pour le parent_id
            p_id = cls.parent_id
            ui_rows.append({
                "iid_key": f"c_{cls.id_categorie}",
                "id_ss_categorie": cls.id_categorie,
                "value": cls.designation or "",
                "parent_id": f"a_{p_id}" if p_id else None,
                "actif": True
            })
        return ui_rows

    def fetch_row_categorie(self) -> List[dict]:
        """Pour remplir la combobox des parents."""
        categorie = self.tracker.get_categories()
        return [{
            "iid_key": f"a_{arm.id_categorie}",
            "id_categorie": arm.id_categorie,
            "value": (arm.designation or "").upper()
        } for arm in categorie]

    def fetch_data_by_iid(self, iid_key: str) -> Optional[dict]:
        """ Récupère les données selon le préfixe de l'iid_key. """
        if not iid_key or "_" not in iid_key:
            return None

        # Extraction du type et de l'id (ex: 'a', '1')
        prefix, raw_id = iid_key.split("_")
        cat_id = int(raw_id)

        # On peut soit utiliser get_by_id (cache global)
        # soit être plus spécifique si besoin
        obj = self.tracker.get_by_id(cat_id)
        return obj.to_dict() if obj else None

    def save_category(self, data: dict) -> bool:
        """ Sauvegarde via le tiers_trackers après transformation. """
        # Le from_dict du tiers_trackers utilise get_by_id pour résoudre l'categorie
        obj = self.tracker.from_dict(data)
        # On utilise la méthode save héritée de GenericTracker
        return self.tracker.save(obj)

    def delete_category(self, data: dict) -> bool:
        """ Supprime la catégorie via le tiers_trackers après transformation. """
        # Reconstitution de l'objet à partir du dictionnaire de l'UI
        obj = self.tracker.from_dict(data)

        if not obj:
            print("[ERREUR] Impossible de reconstituer l'objet Catégorie pour la suppression.")
            return False

        # Appel du tiers_trackers et retour explicite du résultat (True/False)
        try:
            return self.tracker.delete(obj)
        except Exception as e:
            print(f"[ERREUR] Échec de la suppression dans le tiers_trackers : {e}")
            return False

