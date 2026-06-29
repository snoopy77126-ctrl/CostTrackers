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
        self.moyen_paiement_tracker = self.trackers.get('mode_de_paiement')
        self.chequier_tracker = self.trackers.get('chequier')

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
        list_compte = self.compte_tracker.get_all_filtered()
        print(f'list_compte : {list_compte[0]}')
        return [
            {
                "iid_key": compte.id_compte,
                "id": compte.id_compte,
                "value": compte.display_name,  # Affiche le nom du compte
                "actif": compte.est_actif,
            } for compte in self.compte_tracker.get_all_filtered()
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

    def fetch_row_source_paiement(self):
        """Retourne la liste des moyens de paiement NON affectés au compte courant."""
        if not self.moyen_paiement_tracker:
            return []
        
        compte_id = self._current_compte_id()
        affected_modes = self.moyen_paiement_tracker.get_affected_paiement(compte_id) if compte_id else []
        affected_ids = {m.id_mode_paiement for m in affected_modes} if affected_modes else set()
        
        return [
            {"iid_key": f"_mode_paiement_{b.id_mode_paiement}", "id": b.id_mode_paiement, "values": b.designation}
            for b in self.moyen_paiement_tracker.get_all()
            if b.id_mode_paiement not in affected_ids
        ]

    def fetch_row_affected_paiement(self, compte_id):
        """Retourne la liste des banques pour remplir la Combobox de l'UI."""
        if not self.moyen_paiement_tracker:
            return []
        return [
            {"iid_key": f"_mode_paiement_{b.id_mode_paiement}", "id": b.id_mode_paiement, "values": b.designation}
            for b in self.moyen_paiement_tracker.get_affected_paiement(compte_id)
        ]
    def _current_compte_id(self):
        return self.current_compte.id_compte if self.current_compte else None

    def action_select(self, rows: list) -> bool:
        """Affecte les modes de paiement sélectionnés au compte courant."""
        compte_id = self._current_compte_id()
        if not compte_id or not self.moyen_paiement_tracker:
            return False
        for row in rows:
            self.moyen_paiement_tracker.add_liaison(compte_id, row["id"])
        return True

    def action_unselect(self, rows: list) -> bool:
        """Retire les modes de paiement sélectionnés du compte courant."""
        compte_id = self._current_compte_id()
        if not compte_id or not self.moyen_paiement_tracker:
            return False
        for row in rows:
            self.moyen_paiement_tracker.remove_liaison(compte_id, row["id"])
        return True

    def action_select_all(self) -> bool:
        """Affecte tous les modes de paiement au compte courant."""
        compte_id = self._current_compte_id()
        if not compte_id or not self.moyen_paiement_tracker:
            return False
        for mode in self.moyen_paiement_tracker.get_all():
            self.moyen_paiement_tracker.add_liaison(compte_id, mode.id_mode_paiement)
        return True

    def action_unselect_all(self) -> bool:
        """Retire tous les modes de paiement du compte courant."""
        compte_id = self._current_compte_id()
        if not compte_id or not self.moyen_paiement_tracker:
            return False
        return self.moyen_paiement_tracker.remove_all_liaisons(compte_id)

    def fetch_chequiers(self):
        """Retourne la liste des chéquiers du compte courant sous forme de dicts pour l'UI."""
        compte_id = self._current_compte_id()
        if not compte_id or not self.chequier_tracker:
            return [{}]
        chequiers = self.chequier_tracker.get_by_compte(compte_id)
        if not chequiers:
            return [{}]
        return [
            {
                "id_carnet_cheque": c.id_carnet_cheque,
                "chequier_num":     c.chequier_num,
                "nbr_cheque":       c.nbr_cheque,
                "premier_cheque":   c.premier_cheque,
                "date_reception":   c.date_reception,
                "dernier_emis":     c.dernier_emis,
            }
            for c in chequiers
        ]

    def save_chequier(self, data: dict) -> bool:
        """Sauvegarde (insert ou update) un chéquier."""
        if not self.chequier_tracker:
            return False
        from models.mode_de_paiement import ChequierEdition
        compte_id = self._current_compte_id()
        if not compte_id:
            return False
        obj = ChequierEdition(
            id_carnet_cheque=data.get("id_carnet_cheque"),
            compte_id=compte_id,
            chequier_num=data.get("chequier_num"),
            nbr_cheque=data.get("nbr_cheque"),
            premier_cheque=data.get("premier_cheque"),
            date_reception=data.get("date_reception"),
            dernier_emis=data.get("dernier_emis"),
        )
        return self.chequier_tracker.save(obj)

    def delete_chequier(self, chequier_id: int) -> bool:
        """Supprime un chéquier par son id."""
        if not self.chequier_tracker or not chequier_id:
            return False
        from models.mode_de_paiement import ChequierEdition
        obj = ChequierEdition(id_carnet_cheque=chequier_id)
        return self.chequier_tracker.delete(obj)
