# -*- coding: utf-8 -*-
####################################
# Projet : CostTracker
# Fichier : models/operations.py
# Description : Modèles d'opérations bancaires (import et saisie)
# Date : 13/06/2026     Etat : Stable
####################################

from dataclasses import dataclass, field, asdict
from typing import Optional, ClassVar, List

from models._model_base import ModelBase, WithLinkedObjects


# ══════════════════════════════════════════════════════════════════════ #
#  OPERATION — classe de base (champs communs)
# ══════════════════════════════════════════════════════════════════════ #

@dataclass
class OperationBase(ModelBase, WithLinkedObjects):
    """
    Champs communs à toutes les opérations (imports et saisies).

    Hérite de WithLinkedObjects pour porter compte_obj / tiers_obj /
    categorie_obj en mémoire sans les persister.

    SQL_ID et SQL_FIELDS sont définis dans les sous-classes car la table
    physique est partagée (operations_bancaires_lignes) mais les jeux de
    colonnes persistés diffèrent selon la source.
    """

    SQL_ID:     ClassVar[str]       = "id_import_ligne"
    SQL_FIELDS: ClassVar[list[str]] = []   # surchargé dans les sous-classes

    # ---- Champs persistés communs ----------------------------------- #
    id_import_ligne: Optional[int] = None
    libelle:         str           = ""
    date_operation:  str           = ""
    montant:         float         = 0.0
    commentaire:     str           = ""
    type_operation:  str           = "depense"
    source:          str           = ""
    statut:          str           = ""

    # ---- Propriétés calculées --------------------------------------- #

    @property
    def display_name(self) -> str:
        return self.libelle or f"Opération {self.id_import_ligne or ''}"

    @property
    def debit(self) -> float:
        """Montant négatif en valeur absolue (0 si crédit)."""
        return abs(self.montant) if self.montant < 0 else 0.0

    @property
    def credit(self) -> float:
        """Montant positif (0 si débit)."""
        return self.montant if self.montant > 0 else 0.0

    # Note : compte_label, tiers_label, categorie_label
    # sont fournis par le mixin WithLinkedObjects.


# ══════════════════════════════════════════════════════════════════════ #
#  OPERATION IMPORT (ligne bancaire importée)
# ══════════════════════════════════════════════════════════════════════ #

@dataclass
class OperationImport(OperationBase):
    """
    Ligne de la table `operations_bancaires_lignes` issue d'un import bancaire.
    source = 'import_bancaire'
    """

    SQL_FIELDS: ClassVar[list[str]] = [
        "id_import_ligne",
        "id_import",
        "numero_ligne",
        "date_operation",
        "date_valeur",
        "libelle",
        "montant",
        "type_operation",
        "commentaire",
        "source",
        "compte_num",
        "compte_label",
        "solde_compte",
        "tiers",
        "categorie",
        "categorie_parent",
        "fitid",
        "trntype",
        "raw_json",
        "import_key",
        "created_at",
        "compte_id",
        "tiers_id",
        "categorie_id",
    ]

    # ---- Champs supplémentaires ------------------------------------- #
    id_import:        Optional[int]   = None
    numero_ligne:     int             = 0
    date_valeur:      str             = ""
    compte_num:       str             = ""
    compte_label:     str             = ""
    solde_compte:     Optional[float] = None
    tiers:            str             = ""
    categorie:        str             = ""
    categorie_parent: str             = ""
    fitid:            str             = ""
    trntype:          str             = ""
    raw_json:         Optional[str]   = None
    import_key:       str             = ""
    created_at:       Optional[str]   = None
    compte_id:        Optional[int]   = None
    tiers_id:         Optional[int]   = None
    categorie_id:     Optional[int]   = None

    # ---- Sérialisation ---------------------------------------------- #

    def to_sql_dict(self) -> dict:
        """Colonnes persistées — exclut les objets liés transients."""
        d = asdict(self)
        for key in self._TRANSIENT_FIELDS:
            d.pop(key, None)
        # Ne garder que les colonnes déclarées dans SQL_FIELDS
        return {k: d[k] for k in self.SQL_FIELDS if k in d}

    @classmethod
    def from_dict(cls, data: dict) -> "OperationImport":
        """Construit depuis un dict BDD (ignore les clés inconnues)."""
        import inspect
        valid = set(inspect.signature(cls).parameters.keys())
        return cls(**{k: v for k, v in data.items() if k in valid})


# ══════════════════════════════════════════════════════════════════════ #
#  OPERATION SAISIE (saisie manuelle)
# ══════════════════════════════════════════════════════════════════════ #

@dataclass
class OperationSaisie(OperationBase):
    """
    Opération saisie manuellement.
    source = 'saisie'
    Stockée dans la même table `operations_bancaires_lignes`.
    """

    SQL_FIELDS: ClassVar[list[str]] = [
        "id_import_ligne",
        "date_operation",
        "date_valeur",
        "libelle",
        "montant",
        "type_operation",
        "commentaire",
        "source",
        "statut",
        "compte_id",
        "tiers_id",
        "categorie_id",
    ]

    # ---- Champs supplémentaires ------------------------------------- #
    date_valeur:  str           = ""
    compte_id:    Optional[int] = None
    tiers_id:     Optional[int] = None
    categorie_id: Optional[int] = None

    # ---- Sérialisation ---------------------------------------------- #

    def to_sql_dict(self) -> dict:
        """Colonnes persistées pour une saisie manuelle."""
        d = asdict(self)
        for key in self._TRANSIENT_FIELDS:
            d.pop(key, None)
        return {k: d[k] for k in self.SQL_FIELDS if k in d}

    @classmethod
    def from_dict(cls, data: dict) -> "OperationSaisie":
        import inspect
        valid = set(inspect.signature(cls).parameters.keys())
        return cls(**{k: v for k, v in data.items() if k in valid})

    def to_dict(self) -> dict:
        """Retourne le dictionnaire pour l'interface incluant les propriétés calculées."""
        # On récupère les champs de la dataclass
        d = asdict(self)

        # 1. Propriétés calculées depuis OperationBase
        d["debit"] = self.debit
        d["credit"] = self.credit

        # 2. Ajout des labels fournis par WithLinkedObjects
        # Ces attributs sont automatiquement peuplés si les objets liés (compte/tiers/catégorie)
        # sont chargés dans l'objet métier.
        d["compte"] = self.compte_label
        d["tiers"] = self.tiers_label
        d["categorie"] = self.categorie_label
        return d

# ══════════════════════════════════════════════════════════════════════ #
#  IMPORT BANCAIRE (métadonnées fichier)
# ══════════════════════════════════════════════════════════════════════ #

@dataclass
class ImportBancaire(ModelBase):
    """
    Métadonnées d'un fichier importé.
    Correspond à une ligne de la table `imports_bancaires`.
    Le champ `lignes` est transient (non persisté directement).
    """

    SQL_ID:     ClassVar[str]       = "id_import"
    SQL_FIELDS: ClassVar[list[str]] = [
        "id_import", "fichier", "chemin", "format_fichier",
        "checksum", "nb_lignes", "statut", "message",
    ]

    id_import:      Optional[int]           = None
    fichier:        str                     = ""
    chemin:         str                     = ""
    format_fichier: str                     = ""
    checksum:       str                     = ""
    nb_lignes:      int                     = 0
    statut:         str                     = ""
    message:        str                     = ""
    # Transient : liste des lignes chargées en mémoire (non persistée ici)
    lignes:         List[OperationImport]   = field(default_factory=list, repr=False, compare=False)

    # ---- Affichage -------------------------------------------------- #

    @property
    def display_name(self) -> str:
        return self.fichier or f"Import {self.id_import or '(nouveau)'}"

    # ---- Sérialisation ---------------------------------------------- #

    def to_sql_dict(self) -> dict:
        """Colonnes pour la table imports_bancaires (sans lignes)."""
        return {k: getattr(self, k, None) for k in self.SQL_FIELDS}

    def to_dict(self) -> dict:
        """Dictionnaire complet avec les lignes sérialisées."""
        d = self.to_sql_dict()
        d["lignes"] = [ligne.to_dict() for ligne in self.lignes]
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "ImportBancaire":
        import inspect
        valid = set(inspect.signature(cls).parameters.keys())
        return cls(**{k: v for k, v in data.items() if k in valid and k != "lignes"})
