# Description : Banques, TypeCompte, CompteBase et sous-types
# Date : 13/06/2026     Etat : Stable
####################################

from dataclasses import dataclass
from datetime import date
from typing import Optional, ClassVar

from models._model_base import ModelBase


def _to_int_bool(val) -> int:
    """Convertit proprement un booléen, un entier ou une string vers 0/1."""
    if isinstance(val, str):
        return 1 if val.strip().lower() in ('true', '1', 'yes', 'oui') else 0
    return int(bool(val))


# ══════════════════════════════════════════════════════════════════════ #
#  BANQUE
# ══════════════════════════════════════════════════════════════════════ #

@dataclass
class Banque(ModelBase):
    """Représente une institution bancaire."""

    SQL_ID:     ClassVar[str]       = "id_banque"
    SQL_FIELDS: ClassVar[list[str]] = ["id_banque", "label", "identifiant", "description"]

    id_banque:   Optional[int] = None
    label:       Optional[str] = None
    identifiant: Optional[str] = None
    description: Optional[str] = None

    @property
    def display_name(self) -> str:
        return (self.label or "Banque Sans Nom").strip()


# ══════════════════════════════════════════════════════════════════════ #
#  TYPE DE COMPTE
# ══════════════════════════════════════════════════════════════════════ #

@dataclass(kw_only=True)
class TypeCompte(ModelBase):
    """Référentiel des types de comptes (courant, épargne, crédit…)."""

    SQL_ID:     ClassVar[str]       = "id_type_de_compte"
    SQL_FIELDS: ClassVar[list[str]] = ["id_type_de_compte", "designation"]

    designation:        str           = ""
    id_type_de_compte:  Optional[int] = None

    @property
    def display_name(self) -> str:
        return self.designation


# ══════════════════════════════════════════════════════════════════════ #
#  COMPTE — classe de base
# ══════════════════════════════════════════════════════════════════════ #

@dataclass
class CompteBase(ModelBase):
    """
    Classe de base regroupant les attributs, propriétés et sérialisation
    communs à tous les types de comptes.

    SQL_FIELDS correspond aux colonnes physiques de la table `comptes`.
    Les sous-classes ajoutent leurs propres champs via to_sql_dict().
    """

    SQL_ID:     ClassVar[str]       = "id_compte"
    SQL_FIELDS: ClassVar[list[str]] = [
        "id_compte", "label", "numero", "description",
        "date_ouverture", "date_cloture",
        "solde_init", "solde_min", "solde_max",
        "compte_favori", "cache_le_compte",
        "banque_id", "type_compte_id",
        "date_der_rapprochement",
    ]

    # ---- Champs de données ------------------------------------------ #
    id_compte:               Optional[int]    = None
    nom_du_compte:           str              = ""
    identifiant:             Optional[str]    = None
    description:             str              = ""
    date_ouverture:          Optional[date]   = None
    date_cloture:            Optional[date]   = None
    solde_init:              float            = 0.0
    solde_min:               float            = 0.0
    solde_max:               float            = 0.0
    compte_favori:           bool             = False
    cache_le_compte:         bool             = False
    date_der_rapprochement:  Optional[date]   = None
    banque:                  Optional[Banque]     = None
    type_compte:             Optional[TypeCompte] = None

    # ---- Affichage -------------------------------------------------- #

    @property
    def display_name(self) -> str:
        nom = self.nom_du_compte or self.identifiant or f"Compte {self.id_compte or ''}"
        banque_label = self.banque.label if (self.banque and self.banque.label) else "Inconnue"
        return f"{nom} ({banque_label})"

    @property
    def display_short(self) -> str:
        return self.nom_du_compte or self.identifiant or f"Compte {self.id_compte or ''}"

    @property
    def est_actif(self) -> bool:
        if self.cache_le_compte:
            return False
        if self.date_cloture and self.date_cloture <= date.today():
            return False
        return True

    # ---- Sérialisation ---------------------------------------------- #

    def to_dict(self) -> dict:
        """Dictionnaire UI complet (objets liés sérialisés récursivement)."""
        return {
            "id_compte":               self.id_compte,
            "nom_du_compte":           self.nom_du_compte,
            "identifiant":             self.identifiant,
            "description":             self.description,
            "date_ouverture":          self.date_ouverture,
            "date_cloture":            self.date_cloture,
            "solde_init":              self.solde_init,
            "solde_min":               self.solde_min,
            "solde_max":               self.solde_max,
            "compte_favori":           self.compte_favori,
            "cache_le_compte":         self.cache_le_compte,
            "date_der_rapprochement":  self.date_der_rapprochement,
            "banque":                  self.banque.to_dict() if self.banque else None,
            "type_compte":             self.type_compte.to_dict() if self.type_compte else None,
        }

    def to_sql_dict(self) -> dict:
        """Colonnes pour INSERT / UPDATE dans la table `comptes`."""
        return {
            "id_compte":               self.id_compte,
            "label":                   self.nom_du_compte,
            "numero":                  self.identifiant,
            "description":             self.description,
            "date_ouverture":          self.date_ouverture,
            "date_cloture":            self.date_cloture,
            "solde_init":              self.solde_init,
            "solde_min":               self.solde_min,
            "solde_max":               self.solde_max,
            "compte_favori":           _to_int_bool(self.compte_favori),
            "cache_le_compte":         _to_int_bool(self.cache_le_compte),
            "banque_id":               self.banque.id_banque if self.banque else None,
            "type_compte_id":          self.type_compte.id_type_de_compte if self.type_compte else None,
            "date_der_rapprochement":  self.date_der_rapprochement,
        }


# ══════════════════════════════════════════════════════════════════════ #
#  SOUS-TYPES DE COMPTES
# ══════════════════════════════════════════════════════════════════════ #

@dataclass
class CompteCourant(CompteBase):
    """Compte courant ou compte d'épargne classique."""

    object_epargne:      bool  = False
    paiement_defaut:     int   = 0
    decouvert_autorise:  float = 0.0

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "object_epargne":     self.object_epargne,
            "paiement_defaut":    self.paiement_defaut,
            "decouvert_autorise": self.decouvert_autorise,
        })
        return data

    def to_sql_dict(self) -> dict:
        data = super().to_sql_dict()
        data.update({
            "object_epargne":     _to_int_bool(self.object_epargne),
            "decouvert_autorise": self.decouvert_autorise,
        })
        return data


@dataclass
class CompteCredit(CompteBase):
    """Crédit générique (immobilier, auto…)."""

    montant:              float = 0.0
    taux_interet:         float = 0.0
    remboursement_mini:   float = 0.0
    periode_type:         str   = ""
    periode_value:        int   = 0

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "montant":            self.montant,
            "taux_interet":       self.taux_interet,
            "remboursement_mini": self.remboursement_mini,
            "periode_type":       self.periode_type,
            "periode_value":      self.periode_value,
        })
        return data

    # to_sql_dict héritée de CompteBase (pas de colonnes supplémentaires en base)


@dataclass
class CompteCreditConso(CompteBase):
    """Crédit à la consommation."""

    montant_max:             float = 0.0
    taux_interet:            float = 0.0
    remboursement_mini:      float = 0.0
    remboursement_periode:   str   = ""

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "montant_max":           self.montant_max,
            "taux_interet":          self.taux_interet,
            "remboursement_mini":    self.remboursement_mini,
            "remboursement_periode": self.remboursement_periode,
        })
        return data


@dataclass
class ComptePlacement(CompteBase):
    """Compte de placement bloqué ou à terme."""

    taux_interet:  float = 0.0
    duree_periode: str   = ""
    duree_value:   float = 0.0

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "taux_interet":  self.taux_interet,
            "duree_periode": self.duree_periode,
            "duree_value":   self.duree_value,
        })
        return data

