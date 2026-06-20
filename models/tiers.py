# -*- coding: utf-8 -*-
####################################
# Projet : CostTracker
# Fichier : models/tiers.py
# Description : Tiers (contacts, fournisseurs, organisations)
# Date : 13/06/2026     Etat : Stable
####################################

from dataclasses import dataclass
from typing import Optional, ClassVar

from models._model_base import ModelBase


# ══════════════════════════════════════════════════════════════════════ #
#  TIER (personne physique ou morale)
# ══════════════════════════════════════════════════════════════════════ #

@dataclass(kw_only=True)
class Tier(ModelBase):
    """
    Représente un tiers : personne physique, entreprise ou organisme.
    Correspond à une ligne de la table `tiers`.
    """

    SQL_ID:     ClassVar[str]       = "id_tiers"
    SQL_FIELDS: ClassVar[list[str]] = [
        "id_tiers", "titre", "nom", "prenom",
        "organisation", "description", "montant_max", "montant_min",
    ]

    # ---- Champs de données ------------------------------------------ #
    id_tiers:     Optional[int] = None
    organisation: str           = ""
    titre:        str           = ""
    nom:          str           = ""
    prenom:       str           = ""
    description:  str           = ""
    montant_max:  float         = 0.0   # corrigé : int = "" était invalide
    montant_min:  float         = 0.0

    # ---- Affichage -------------------------------------------------- #

    @property
    def display_name(self) -> str:
        """Format complet : TITRE NOM PRÉNOM (ORGANISATION)."""
        identite = " ".join(filter(None, [
            (self.titre      or "").strip(),
            (self.nom        or "").upper(),
            (self.prenom     or "").strip(),
        ])).strip()
        org = (self.organisation or "").upper().strip()
        if identite and org:
            return f"{identite} ({org})"
        return identite or org or f"Tiers {self.id_tiers or '(nouveau)'}"

    @property
    def display_full(self) -> str:
        """Alias de display_name (compatibilité tiers_helpers)."""
        return self.display_name

    @property
    def display_short(self) -> str:
        """Format court pour les listes : NOM PRÉNOM."""
        return " ".join(filter(None, [
            (self.nom    or "").upper(),
            (self.prenom or "").strip(),
        ])).strip() or self.display_name

    @property
    def display_org_first(self) -> str:
        """Format centré organisation : ORGANISATION - NOM."""
        org = (self.organisation or "").upper().strip()
        nom = (self.nom          or "").upper().strip()
        result = " - ".join(filter(None, [org, nom]))
        return result or self.display_name

    @property
    def tiers_label(self) -> str:
        """Label utilisé par les propriétés tiers_label des opérations."""
        return self.display_short or self.display_name

    def __repr__(self) -> str:
        return self.display_name

    # ---- Sérialisation ---------------------------------------------- #

    def to_dict(self) -> dict:
        return {
            "id_tiers":     self.id_tiers,
            "organisation": self.organisation,
            "titre":        self.titre,
            "nom":          self.nom,
            "prenom":       self.prenom,
            "description":  self.description,
            "montant_max":  self.montant_max,
            "montant_min":  self.montant_min,
        }

    def to_sql_dict(self) -> dict:
        """Identique à to_dict pour ce modèle (pas de champs transients)."""
        return self.to_dict()


# ══════════════════════════════════════════════════════════════════════ #
#  ORGANISATION (vue simplifiée — legacy)
# ══════════════════════════════════════════════════════════════════════ #

@dataclass(kw_only=True)
class Organisation(ModelBase):
    """
    Vue simplifiée d'un tiers vu sous l'angle de son organisation.
    Utilisé dans certains combobox centrés entreprise.
    """

    SQL_ID:     ClassVar[str]       = "id_entreprise"
    SQL_FIELDS: ClassVar[list[str]] = ["id_entreprise", "organisation"]

    id_entreprise: Optional[int] = None
    organisation:  str           = ""

    @property
    def display_name(self) -> str:
        return (self.organisation or "").strip()
