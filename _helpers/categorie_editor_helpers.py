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
        self.services = services or {}
        self.cat_trackers = self.services.get('categorie')
        self.ops_trackers = self.services.get("operation")

    def initialise(self):
        self.cat_trackers.clear_cache()

    def fetch_row_complet(self) -> List[dict]:

        """ Récupère et formate les catégories pour le TreeView. """
        self.cat_trackers.clear_cache()
        categorie = self.cat_trackers.get_categories()
        ss_categorie = self.cat_trackers.get_ss_categories()
        ui_rows = []

        # 1. Formatage des categorie (Noeuds parents)
        for arm in categorie:
            ui_rows.append({
                "iid_key": f"a_{arm.id_categorie}",
                "id_categorie": arm.id_categorie,
                "value": (arm.designation or "").upper(),
                "parent_id": None,
                "display_name":arm.display_name,
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
                "display_name": cls.display_name,
                "actif": True
            })

        return ui_rows

    def fetch_row_categorie(self) -> List[dict]:
        """Pour remplir la combobox des parents."""
        categorie = self.cat_trackers.get_categories()
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
        obj = self.cat_trackers.get_by_id(cat_id)
        return obj.to_dict() if obj else None

    def save_category(self, data: dict) -> bool:
        """ Sauvegarde via le tiers_trackers après transformation. """
        # Le from_dict du tiers_trackers utilise get_by_id pour résoudre l'categorie
        obj = self.cat_trackers.from_dict(data)
        # On utilise la méthode save héritée de GenericTracker
        return self.cat_trackers.save(obj)

    def delete_category(self, data: dict) -> bool:
        """ Supprime la catégorie via le tiers_trackers après transformation. """
        # Reconstitution de l'objet à partir du dictionnaire de l'UI
        obj = self.cat_trackers.from_dict(data)

        if not obj:
            print("[ERREUR] Impossible de reconstituer l'objet Catégorie pour la suppression.")
            return False

        # Appel du tiers_trackers et retour explicite du résultat (True/False)
        try:
            return self.cat_trackers.delete(obj)
        except Exception as e:
            print(f"[ERREUR] Échec de la suppression dans le tiers_trackers : {e}")
            return False

    def fetch_row_operations(self, selected_id, limit=250):
        if not selected_id:
            return []

        # 1. On récupère les opérations (assurez-vous que self.operations() filtre déjà par tiers si possible)
        all_ops = self.operations(limit)
        # Filtrage par tiers
        ops = [op for op in all_ops if getattr(op, 'categorie_id', None) == selected_id]
        rows = []
        soldes_courants = {}

        # 2. On trie les opérations par date (souvent nécessaire pour un calcul de solde cohérent)
        # Si ops est déjà trié, vous pouvez retirer cette ligne.
        ops.sort(key=lambda x: x.date_operation)

        for op in ops:
            compte_label = op.display_name
            montant = (op.credit or 0.0) - (op.debit or 0.0)

            # Mise à jour du solde courant pour ce compte spécifique
            nouveau_solde = soldes_courants.get(compte_label, 0.0) + montant
            soldes_courants[compte_label] = nouveau_solde

            rows.append({
                "iid_key": op.id_import_ligne,
                "date_operation": op.date_operation,
                "libelle": op.libelle,
                "categorie": op.categorie_label,
                "tiers": op.tiers_label,
                "debit": self.money(op.debit) if hasattr(op, 'debit') and op.debit else "",
                "credit": self.money(op.credit) if hasattr(op, 'credit') and op.credit else "",
                "solde": self.money(nouveau_solde),
                "montant": op.montant,
                "source": getattr(op, 'source', 'saisie'),
                "objet": op,
            })

        return rows

    def operations(self, limit=250):
        if not self.ops_trackers:
            return []
        ops = self.ops_trackers.get_recent(limit)
        return ops

