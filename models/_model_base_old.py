# -*- coding: utf-8 -*-
####################################
# Projet : CostTracker
# Fichier : models/_model_base.py
# Description : Classe générique de base pour tous les modèles métier.
#               Fournit : identification, sérialisation SQL/dict, état new/dirty,
#               from_dict, display_name, __repr__, __str__.
# Date : 13/06/2026     Etat : Stable
####################################

from __future__ import annotations

import inspect
from dataclasses import dataclass, asdict, fields, field
from typing import Any, ClassVar, Optional


@dataclass
class ModelBase:
    """
    Classe racine commune à tous les modèles métier CostTracker.

    Chaque sous-classe DOIT déclarer deux attributs de classe :

        SQL_ID      : str  — nom du champ identifiant primaire (ex: "id_compte")
        SQL_FIELDS  : list — liste des colonnes persistées en base
                             (doit exclure les champs transients / objets liés)

    Exemple minimal :

        @dataclass
        class Banque(ModelBase):
            SQL_ID     = "id_banque"
            SQL_FIELDS = ["id_banque", "label", "identifiant", "description"]

            id_banque   : Optional[int] = None
            label       : Optional[str] = None
            identifiant : Optional[str] = None
            description : Optional[str] = None

    """

    # ------------------------------------------------------------------ #
    # Attributs de classe à surcharger dans chaque modèle concret
    # ------------------------------------------------------------------ #
    SQL_ID:     ClassVar[str]        = ""     # Clé primaire SQL
    SQL_FIELDS: ClassVar[list[str]]  = []     # Colonnes persistées

    # ------------------------------------------------------------------ #
    # Champs de données transients (non persistés, communs à tous)
    # ------------------------------------------------------------------ #
    # Aucun champ transient n'est déclaré ici pour ne pas polluer les
    # sous-classes pures. Les modèles qui en ont besoin les déclarent
    # eux-mêmes avec field(default=None, repr=False, compare=False).

    # ================================================================== #
    # 1. IDENTIFICATION
    # ================================================================== #

    @property
    def pk(self) -> Optional[int]:
        """Retourne la valeur de la clé primaire (lecture seule)."""
        return getattr(self, self.SQL_ID, None) if self.SQL_ID else None

    def is_new(self) -> bool:
        """Vrai si l'objet n'a pas encore été persisté (PK absente ou nulle)."""
        pk = self.pk
        return pk is None or pk == 0

    def is_dirty(self, other: "ModelBase") -> bool:
        """
        Vrai si au moins un champ SQL diffère entre self et other.
        Utile pour éviter un UPDATE inutile.
        """
        for fname in (self.SQL_FIELDS or []):
            if getattr(self, fname, None) != getattr(other, fname, None):
                return True
        return False

    # ================================================================== #
    # 2. SÉRIALISATION
    # ================================================================== #

    def to_dict(self) -> dict:
        """
        Dictionnaire complet de l'objet (tous les champs dataclass).
        Les champs transients (objets liés, non picklables) sont inclus
        sous forme de None — les surcharges peuvent les exclure.
        """
        try:
            return asdict(self)
        except Exception:
            # Fallback si asdict échoue (champs non-dataclass imbriqués)
            return {f.name: getattr(self, f.name, None) for f in fields(self)}

    def to_sql_dict(self) -> dict:
        """
        Dictionnaire restreint aux colonnes SQL déclarées dans SQL_FIELDS.
        C'est ce dictionnaire qui est passé aux INSERT / UPDATE du GenericManager.
        La PK est incluse (le manager la retire avant INSERT).
        """
        all_data = self.to_dict()
        if self.SQL_FIELDS:
            return {k: all_data[k] for k in self.SQL_FIELDS if k in all_data}
        # Si SQL_FIELDS n'est pas défini, on exclut les champs se terminant par _obj
        return {k: v for k, v in all_data.items() if not k.endswith("_obj")}

    @classmethod
    def from_dict(cls, data: dict) -> "ModelBase":
        """
        Construit une instance à partir d'un dictionnaire (issu de la BDD ou de l'UI).
        Seuls les champs présents dans la signature __init__ sont injectés.
        Les clés inconnues sont silencieusement ignorées.
        """
        valid_keys = set(inspect.signature(cls).parameters.keys())
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

    # ================================================================== #
    # 3. AFFICHAGE
    # ================================================================== #

    @property
    def display_name(self) -> str:
        """
        Nom d'affichage par défaut.
        Cherche les attributs communs dans l'ordre : label, designation,
        nom, libelle, organisation, puis fallback sur la PK.
        Chaque modèle peut surcharger cette propriété.
        """
        for attr in ("label", "designation", "nom", "libelle", "organisation"):
            val = getattr(self, attr, None)
            if val:
                return str(val).strip()
        pk = self.pk
        return f"{type(self).__name__} {pk or '(nouveau)'}"

    def __repr__(self) -> str:
        return self.display_name

    def __str__(self) -> str:
        return self.display_name


# ====================================================================== #
#  MIXIN optionnel : champs transients (objets liés non persistés)
#  À utiliser en héritage multiple pour les modèles qui résolvent des FK
# ====================================================================== #

@dataclass
class WithLinkedObjects:
    """
    Mixin pour les modèles qui portent des objets résolus en mémoire
    (compte_obj, tiers_obj, categorie_obj…).

    Usage :
        @dataclass
        class OperationImport(ModelBase, WithLinkedObjects):
            ...

    to_sql_dict() exclut automatiquement les champs _obj.
    """
    compte_obj:    Any = field(default=None, repr=False, compare=False)
    tiers_obj:     Any = field(default=None, repr=False, compare=False)
    categorie_obj: Any = field(default=None, repr=False, compare=False)

    # Noms des champs transients à exclure de la sérialisation SQL
    _TRANSIENT_FIELDS: ClassVar[tuple[str, ...]] = (
        "compte_obj", "tiers_obj", "categorie_obj",
    )

    @property
    def compte_label(self) -> str:
        return getattr(self.compte_obj, "display_name", "") or ""

    @property
    def tiers_label(self) -> str:
        t = self.tiers_obj
        if not t:
            return ""
        return getattr(t, "display_short", None) or getattr(t, "display_name", "") or ""

    @property
    def categorie_label(self) -> str:
        c = self.categorie_obj
        if not c:
            return ""
        return getattr(c, "categorie_label", None) or getattr(c, "display_name", "") or ""
