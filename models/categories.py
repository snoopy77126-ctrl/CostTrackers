# -*- coding: utf-8 -*-
####################################
# Projet : CostTracker
# Fichier : models/categories.py
# Description : Catégories et sous-catégories de dépenses
# Date : 13/06/2026     Etat : Stable
####################################

from dataclasses import dataclass, field
from typing import Optional, ClassVar

from models._model_base import ModelBase


# ══════════════════════════════════════════════════════════════════════ #
#  CATEGORIE (racine)
# ══════════════════════════════════════════════════════════════════════ #

@dataclass(kw_only=True)
class Categorie(ModelBase):
    """
    Catégorie racine.
    Correspond aux lignes de la table `categories` avec parent_id IS NULL.
    """

    SQL_ID:     ClassVar[str]       = "id_categorie"
    SQL_FIELDS: ClassVar[list[str]] = ["id_categorie", "designation", "parent_id"]

    id_categorie: Optional[int] = None
    designation:  str           = ""

    # ---- Identification --------------------------------------------- #

    @property
    def parent_id(self) -> None:
        """Une catégorie racine n'a pas de parent."""
        return None

    # ---- Affichage -------------------------------------------------- #

    @property
    def display_name(self) -> str:
        return self.designation

    @property
    def categorie_label(self) -> str:
        return self.designation

    @property
    def display_tree(self) -> str:
        """Format pour l'arbre UI (label de nœud parent)."""
        return f"{self.designation}:"

    def __repr__(self) -> str:
        return f"Categorie({self.id_categorie} => {self.designation})"

    # ---- Sérialisation ---------------------------------------------- #

    def to_dict(self) -> dict:
        return {
            "id_categorie": self.id_categorie,
            "designation":  self.designation,
        }

    def to_sql_dict(self) -> dict:
        return {
            "id_categorie": self.id_categorie,
            "designation":  self.designation,
            "parent_id":    None,               # toujours NULL pour une racine
        }


# ══════════════════════════════════════════════════════════════════════ #
#  SOUS-CATEGORIE
# ══════════════════════════════════════════════════════════════════════ #

@dataclass(kw_only=True)
class SSCategorie(ModelBase):
    """
    Sous-catégorie.
    Correspond aux lignes de la table `categories` avec parent_id NOT NULL.
    Porte une référence vers l'objet Categorie parent (non persisté directement).
    """

    SQL_ID:     ClassVar[str]       = "id_categorie"
    SQL_FIELDS: ClassVar[list[str]] = ["id_categorie", "designation", "parent_id"]

    id_categorie: Optional[int]            = None
    designation:  str                      = ""
    categorie:    Optional["Categorie"]    = field(default=None, repr=False)

    # ---- Identification --------------------------------------------- #

    @property
    def parent_id(self) -> Optional[int]:
        return self.categorie.id_categorie if self.categorie else None

    # ---- Affichage -------------------------------------------------- #

    @property
    def display_name(self) -> str:
        """Format 'Parent: Enfant' utilisé dans les combobox."""
        parent_nom = self.categorie.designation if self.categorie else "Inconnue"
        return f"{parent_nom}: {self.designation}"

    @property
    def categorie_label(self) -> str:
        """Alias de display_name (compatibilité tiers_helpers)."""
        return self.display_name

    @property
    def parent_name(self) -> str:
        return self.categorie.designation if self.categorie else "Inconnue"

    @property
    def display_tree(self) -> str:
        """Indentation visuelle dans les arbres UI."""
        return f"        {self.designation}"

    def __repr__(self) -> str:
        return f"SSCategorie({self.id_categorie} => {self.display_name})"

    def __str__(self) -> str:
        return f"{self.id_categorie} => {self.display_name}"

    # ---- Sérialisation ---------------------------------------------- #

    def to_dict(self) -> dict:
        return {
            "id_categorie": self.id_categorie,
            "designation":  self.designation,
            "parent_id":    self.parent_id,
            "categorie":    self.categorie.to_dict() if self.categorie else None,
        }

    def to_sql_dict(self) -> dict:
        return {
            "id_categorie": self.id_categorie,
            "designation":  self.designation,
            "parent_id":    self.parent_id,     # FK vers la catégorie racine
        }
