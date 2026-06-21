# _helpers/comptes_editor_helpers.py
from typing import Optional
from _helpers._generique_helpers import BaseHelper
from models.banques import CompteCourant, Banque  # On cible le Compte courant


class CompteEditorHelpers(BaseHelper):
    def __init__(self, services=None):
        services_dict = services or {}
        super().__init__(trackers=services_dict)

        # Le compte est notre ressource principale, la banque est secondaire
        self.compte_tracker = self.trackers.get('compte')
        self.banque_tracker = self.trackers.get('banque')
        self.type_compte_tracker = self.trackers.get('type_compte')

        # Injection des dépendances croisées nécessaires au CompteTracker
        # pour résoudre les objets Banque / TypeCompte complets lors du from_dict.
        if self.compte_tracker is not None:
            self.compte_tracker.banque_tracker = self.banque_tracker
            self.compte_tracker.type_compte_tracker = self.type_compte_tracker

        self.current_compte: Optional[CompteCourant] = None

    def initialise(self):
        """Recharge les comptes et les banques depuis la base de données."""
        if self.compte_tracker:
            self.compte_tracker.load_all()
        if self.banque_tracker:
            self.banque_tracker.load_all()
        if self.type_compte_tracker:
            self.type_compte_tracker.load_all()

    def fetch_row_compte(self):
        """Formatage des lignes de COMPTES pour l'arbre visuel."""
        if not self.compte_tracker:
            return []
        return [
            {
                "iid_key": compte.id_compte,
                "id": compte.id_compte,
                "value": compte.display_name,  # Affiche le nom du compte
                "actif": True,
            } for compte in self.compte_tracker.load_all()
        ]

    def fetch_liste_banques(self):
        """Retourne la liste des banques pour remplir la Combobox de l'UI."""
        if not self.banque_tracker:
            return []
        return [
            {"iid_key": f"bank_{b.id_banque}","id": b.id_banque, "value": b.display_name}
            for b in self.banque_tracker.get_all()
        ]

    def fetch_liste_compte(self):
        """Retourne la liste des banques pour remplir la Combobox de l'UI."""
        if not self.compte_tracker:
            return []
        return [
            {"iid_key": f"cmpt_{b.id_compte}","id": b.id_compte, "value": b.display_name}
            for b in self.compte_tracker.get_all()
        ]

    def fetch_data_compte(self, compte_id) -> Optional[dict]:
        """Sélectionne un compte et extrait son dictionnaire pour l'UI."""
        if not self.compte_tracker or not compte_id:
            return None
        obj = self.compte_tracker.get_by_id(compte_id)
        self.current_compte = obj
        return obj.to_dict() if obj else None

    def new_compte(self):
        self.current_compte = None

    def save_compte(self, data: dict) -> bool:
        if not self.compte_tracker:
            return False

        # 1. Le tiers_trackers fait tout le travail de résolution d'objets (Banque, TypeCompte)
        # Il renvoie un objet métier complet et prêt à l'emploi.
        obj = self.compte_tracker.from_dict(data)

        if not obj:
            return False

        # 2. Suppression de l'intervention manuelle invasive.
        # On ne touche pas aux attributs de l'objet.
        # Le CompteManager saura extraire les ID depuis l'objet via to_sql_dict().

        # DEBUG : vérifiez que l'objet a bien ses attributs avant sauvegarde
        print(f"[DEBUG] Banque attachée : {obj.banque}")

        # 3. Sauvegarde directe
        return self.compte_tracker.save(obj)
    def delete_compte(self) -> bool:
        if self.compte_tracker and self.current_compte and self.current_compte.id_compte:
            return self.compte_tracker.delete(self.current_compte.id_compte)
        return False

    def fetch_liste_type_compte(self):
        """Retourne la liste des Types de Compte pour remplir la Combobox."""
        if not self.type_compte_tracker:
            return []
        return [
            {"iid_key": f"type_{b.id_type_de_compte}", "id": b.id_type_de_compte, "value": b.display_name}
            for b in self.type_compte_tracker.get_all()
        ]