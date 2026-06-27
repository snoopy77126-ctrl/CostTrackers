import inspect
from typing import Optional

from _manager.compte_manager import CompteManager
from _trackers._generic_tracker import GenericTracker
from models.banques import CompteCourant, ComptePlacement, CompteCredit, CompteCreditConso, Banque


class CompteTracker(GenericTracker):
    COMPTE_CLASSES = {
        "generale": CompteCourant,
        "compte courant": CompteCourant,
        "courant": CompteCourant,
        "placement": ComptePlacement,
        "epargne": ComptePlacement,
        "credit": CompteCredit,
        "emprunt": CompteCredit,
        "credit_conso": CompteCreditConso,
        "pret": CompteCreditConso,
    }

    COMPTE_CLASSES_BY_ID = {
        1: CompteCourant,
        2: ComptePlacement,
        3: CompteCredit,
        4: CompteCreditConso,
    }

    def __init__(self):
        super().__init__(CompteManager(), "id_compte")
        # Seront injectés depuis l'extérieur (ex: comptes_editor_helpers)
        # pour permettre la résolution des objets liés Banque / TypeCompte.
        self.banque_tracker = None
        self.type_compte_tracker = None

    def from_dict(self, data: dict):
        if not data: return None
        raw_data = self._clean_data(data.copy())

        # Résolutions
        type_val = raw_data.pop("type_compte", None) or raw_data.get("type_compte_id", "generale")
        compte_class = self._resolve_compte_class(type_val)

        raw_data["banque"] = self._resolve_banque(raw_data.get("banque") or raw_data.get("banque_id"))
        raw_data["type_compte"] = self._resolve_type_compte(type_val, compte_class)

        # Filtrage automatique via signature (la méthode la plus propre)
        valid_keys = inspect.signature(compte_class).parameters.keys()
        return compte_class(**{k: v for k, v in raw_data.items() if k in valid_keys})

    def _clean_data(self, raw_data: dict):
        """Standardise les clés et types avant instantiation."""
        mapping = {
            "label": "nom_du_compte",
            "numero": "identifiant",
            "solde_mini": "solde_min"
        }
        for old, new in mapping.items():
            if old in raw_data and new not in raw_data:
                raw_data[new] = raw_data.pop(old)

        # Nettoyage types numériques
        numeric_fields = ["solde_init", "solde_min", "solde_max", "decouvert_autorise",
                          "taux_interet", "duree_value", "montant", "montant_max", "remboursement_mini"]
        for field in numeric_fields:
            if field in raw_data:
                raw_data[field] = float(raw_data[field] or 0.0)

        # Nettoyage booléens
        for field in ("compte_favori", "cache_le_compte", "object_epargne"):
            if field in raw_data:
                raw_data[field] = bool(raw_data[field])

        return raw_data

    def _resolve_compte_class(self, type_compte):
        if isinstance(type_compte, dict):
            type_compte = (
                    type_compte.get("id")
                    or type_compte.get("iid_key")
                    or type_compte.get("value")
                    or type_compte.get("designation")
                    or type_compte.get("type_compte_id")
            )

        # Si c'est un identifiant d'interface (ex: 'cmpt_1' ou 'type_2')
        if isinstance(type_compte, str) and "_" in type_compte:
            # Sécurité : Si c'est une chaîne comme 'credit_conso', rsplit renverrait 'conso' (inconnu).
            # On ne prend le dernier élément que si c'est un chiffre (ex: cmpt_1 -> 1)
            parts = type_compte.rsplit("_", 1)
            if parts[-1].isdigit():
                type_compte = parts[-1]

        # Tentative de résolution par ID direct (1, 2, 3, 4)
        try:
            return self.COMPTE_CLASSES_BY_ID[int(type_compte)]
        except (KeyError, TypeError, ValueError):
            pass

        # Résolution par chaîne textuelle normalisée
        normalized_type = str(type_compte or "generale").strip().lower()
        return self.COMPTE_CLASSES.get(normalized_type, CompteCourant)

    def _resolve_type_compte(self, type_compte, compte_class):
        """Retourne l'objet TypeCompte associé (via le type_compte_tracker si possible).

        Cet objet est utilisé par CompteManager._to_dict / to_sql_dict pour
        déduire la colonne type_compte_id. Si la résolution complète échoue
        (tiers_trackers absent ou id introuvable), retourne None : le manager
        appliquera alors un repli basé sur la classe Python de l'objet.
        """
        type_id = self._extract_type_compte_id(type_compte)

        # Repli : ID basé sur la classe Python résolue (CompteCourant -> 1, etc.)
        if type_id is None:
            for tid, cls in self.COMPTE_CLASSES_BY_ID.items():
                if cls is compte_class:
                    type_id = tid
                    break

        if type_id is None:
            return None

        # Tentative de récupération de l'objet complet via le TypeCompteTracker
        if getattr(self, "type_compte_tracker", None):
            obj = self.type_compte_tracker.get_by_id(type_id)
            if obj:
                return obj

        # Pas de tiers_trackers ou type introuvable en cache : on laisse type_compte=None.
        # CompteManager._to_dict déduira type_compte_id depuis la classe Python.
        return None

    @staticmethod
    def _extract_type_compte_id(type_compte):
        """Extrait un identifiant numérique de type_compte (dict, str 'type_X', int...)."""
        if isinstance(type_compte, dict):
            raw_id = (
                    type_compte.get("id")
                    or type_compte.get("iid_key")
                    or type_compte.get("id_type_de_compte")
            )
        else:
            raw_id = type_compte

        if isinstance(raw_id, str) and "_" in raw_id:
            parts = raw_id.rsplit("_", 1)
            raw_id = parts[-1] if parts[-1].isdigit() else None

        try:
            return int(raw_id)
        except (TypeError, ValueError):
            return None

    def _resolve_banque(self, banque_info):
        if not banque_info:
            return None
        if isinstance(banque_info, Banque):
            return banque_info

        banque_id = None
        label = None

        # Cas 1 : banque_info est juste un ID (int ou str)
        if isinstance(banque_info, (int, str)):
            banque_id = banque_info

        # Cas 2 : banque_info est un dictionnaire complet d'interface
        elif isinstance(banque_info, dict):
            banque_id = (
                    banque_info.get("id")
                    or banque_info.get("iid_key")
                    or banque_info.get("id_banque")
            )
            label = banque_info.get("value") or banque_info.get("label")

        # Nettoyage de l'ID si c'est une clé d'interface (ex: 'bnq_3' -> 3)
        if isinstance(banque_id, str) and "_" in banque_id:
            parts = banque_id.rsplit("_", 1)
            if parts[-1].isdigit():
                banque_id = parts[-1]

        try:
            banque_id = int(banque_id)
        except (TypeError, ValueError):
            banque_id = None

        # Tentative de récupération de l'objet complet via le BanqueTracker (s'il est lié)
        if banque_id and getattr(self, "banque_tracker", None):
            # Utilise 'load_by_id' ou la méthode de recherche de votre GenericTracker
            banque = self.banque_tracker.get_by_id(banque_id)
            if banque:
                return banque

        # Fallback : On crée l'objet avec ce qu'on a sous la main
        return Banque(id_banque=banque_id, label=label)

    def get_by_name_and_num(self, name: str, num: str) -> Optional[dict]:
        """Recherche un compte par son nom (nom_du_compte) AND son numéro (identifiant)."""
        # On parcourt le cache local des objets géré par le GenericTracker (ex: self.all_objects ou self.get_all())
        for compte in self.get_all():
            # Selon vos modèles, adaptez .nom_du_compte et .identifiant
            if compte.nom_du_compte == name and compte.identifiant == num:
                return compte
        return None

    def get_by_display_string(self, display_string: str) -> Optional[dict]:
        """Retrouve un compte à partir de la chaîne "Nom [Numéro]" du Combobox."""
        for compte in self.get_all():
            if f"{compte.nom_du_compte} [{compte.identifiant}]" == display_string:
                return compte
        return None

    def get_affected_paiement(self):
        """Retourne la liste des comptes affectés au paiement."""
        return self.get_all()

    def get_all_filtered(self, actif: bool = True) -> list:
        """Retourne la liste des tiers filtrée ou l'intégralité de la liste."""
        tous_les_comptes = self.get_all()

        # Si actif est True, on filtre. Si actif est False, on retourne tout.
        if actif:
            return [compte for compte in tous_les_comptes if compte.est_actif]

        return tous_les_comptes

    def create(self, name: str, number: str):
        """Crée un nouveau compte en base de données via le manager et l'ajoute au tiers_trackers."""
        # On prépare le dictionnaire attendu par from_dict / le manager
        data = {
            "nom_du_compte": name,
            "identifiant": number,
            "type_compte": "courant"  # Valeur par défaut
        }
        # Utilise la logique de votre GenericTracker pour sauvegarder (ex: self.save ou self.manager.insert)
        new_obj = self.from_dict(data)
        return self.save(new_obj)  # Adaptez 'self.save' selon la méthode de votre GenericTracker