# _helpers/_generique_helpers.py

class BaseHelper:
    def __init__(self, trackers: dict):
        """
        Initialise le helper générique avec un dictionnaire de trackers.
        Exemple pour un fichier : {"emetteur": em_track, "classeur": cat_track}
        Exemple pour une catégorie : {"armoire": arm_track}
        """
        self.trackers = trackers

    def resolve_fk(self, key: str, value):
        """
        Transforme une valeur issue de l'UI (ID ou dictionnaire contenant un ID)
        en un sous-objet métier complet en utilisant le tiers_trackers approprié.
        """
        if not value:
            return None

        # Si la valeur est un dictionnaire d'UI (ex: {"iid_key": 5, "value": "..."})
        # on extrait l'identifiant technique réel.
        if isinstance(value, dict):
            value = value.get("iid_key") or value.get("id")

        # Si après extraction la valeur est vide (ex: l'utilisateur a vidé son choix)
        if value is None or value == "":
            return None

        # Récupération du tiers_trackers associé à ce champ de clé étrangère
        tracker = self.trackers.get(key)
        if not tracker:
            # Si aucun tiers_trackers n'est enregistré pour cette clé, on renvoie l'ID brut
            return value

        # Renvoie le véritable sous-objet métier configuré (Entity / Model)
        return tracker.get_by_id(value)

    def apply_form_to_object(self, obj, data: dict, fk_fields: list = None):
        """
        Injecte dynamiquement les données d'un formulaire dans n'importe quel 
        objet métier (Fichier, Emetteur, Categorie, etc.).

        fk_fields : liste des clés à résoudre en sous-objets via les trackers.
        """
        fk_fields = fk_fields or []

        # Liste de sécurité des champs d'UI globaux à ne jamais injecter dans les objets
        ui_exclusion_list = ["selected_file", "id_fichier", "iid_key"]

        for key, value in data.items():
            if key in ui_exclusion_list:
                continue

            # Si le champ est identifié comme une clé étrangère, on résout le sous-objet
            if key in fk_fields:
                value = self.resolve_fk(key, value)

            # Assignation dynamique si l'objet possède cet attribut
            if hasattr(obj, key):
                setattr(obj, key, value)
            else:
                print(f"[WARN] Champ d'UI '{key}' absent de l'objet métier {obj.__class__.__name__}")

        return obj

    def fetch_all(self, tracker_name: str):
        tracker = self.trackers.get(tracker_name)
        if not tracker:
            return []
        return tracker.get_all()