from typing import List, Optional

from ._generique_helpers import BaseHelper


class ModeDePaiementEditorHelpers(BaseHelper):
    """
    Helper pour l'éditeur de modes de paiement.
    Hérite de BaseHelper pour la résolution des clés étrangères.
    """

    def __init__(self, services):
        super().__init__(services)
        self.services = services or {}
        self.mode_trackers = self.services.get('mode_de_paiement')

    def initialise(self):
        if self.mode_trackers:
            self.mode_trackers.clear_cache()

    def fetch_row_complet(self) -> List[dict]:
        """ Récupère et formate les modes de paiement pour le TreeView. """
        if not self.mode_trackers:
            return []
        
        self.mode_trackers.clear_cache()
        modes = self.mode_trackers.get_all()
        ui_rows = []

        for mode in modes:
            ui_rows.append({
                "iid_key": mode.id_mode_paiement,
                "id_mode_paiement": mode.id_mode_paiement,
                "code": mode.code.upper(),
                "designation": mode.designation,
                "description": mode.description,
                "actif": mode.actif,
                "display_name": mode.display_name,
                "value": mode.display_name
            })

        return ui_rows

    def fetch_row_actifs(self) -> List[dict]:
        """Pour remplir les combobox avec uniquement les modes actifs."""
        if not self.mode_trackers:
            return []
        
        modes = self.mode_trackers.get_actifs()
        return [{
            "iid_key": mode.id_mode_paiement,
            "id_mode_paiement": mode.id_mode_paiement,
            "code": mode.code.upper(),
            "value": mode.display_name
        } for mode in modes]

    def fetch_data_by_iid(self, iid_key: str) -> Optional[dict]:
        """ Récupère les données selon l'iid_key. """
        if not iid_key:
            return None

        try:
            mode_id = int(iid_key)
        except (ValueError, TypeError):
            return None

        obj = self.mode_trackers.get_by_id(mode_id)
        return obj.to_dict() if obj else None

    def save_mode_paiement(self, data: dict) -> bool:
        """ Sauvegarde via le tracker après transformation. """
        from models.mode_de_paiement import ModeDePaiement
        
        # Reconstitution de l'objet
        mode_id = data.get("id_mode_paiement")
        if mode_id:
            # Mise à jour d'un existant
            obj = self.mode_trackers.get_by_id(mode_id)
            if not obj:
                return False
        else:
            # Création d'un nouveau
            obj = ModeDePaiement()
        
        # Mise à jour des champs
        obj.code = data.get("code", "")
        obj.designation = data.get("designation", "")
        obj.description = data.get("description", "")
        obj.actif = data.get("actif", True)
        
        # Sauvegarde
        return self.mode_trackers.save(obj)

    def delete_mode_paiement(self, data: dict) -> bool:
        """ Supprime le mode de paiement via le tracker. """
        mode_id = data.get("id_mode_paiement")
        if not mode_id:
            return False

        obj = self.mode_trackers.get_by_id(mode_id)
        if not obj:
            print("[ERREUR] Impossible de trouver le mode de paiement pour la suppression.")
            return False

        try:
            return self.mode_trackers.delete(obj)
        except Exception as e:
            print(f"[ERREUR] Échec de la suppression : {e}")
            return False
