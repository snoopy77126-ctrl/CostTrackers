# -*- coding: utf-8 -*-
####################################
# Projet : CostTracker
# Fichier : models/periodiques.py
# Description : Modèle pour les charges périodiques (abonnements, prélèvements récurrents)
# Date : 23/06/2026     Etat : Stable
####################################

from dataclasses import dataclass, field, asdict
from typing import Optional, ClassVar, Any
from datetime import date

from databases.schema_inspector import register_model
from models._model_base import ModelBase, transient_field


FREQUENCES = ["mensuel", "trimestriel", "semestriel", "annuel"]
TYPES_FLUX = ["depense", "revenu"]


@register_model
@dataclass(kw_only=True)
class Periodique(ModelBase):
    """
    Charge ou revenu récurrent (prélèvement, abonnement, remboursement de prêt…).
    Stocké dans la table `periodiques`.
    """

    SQL_TABLE:  ClassVar[str]       = "periodiques"
    SQL_ID:     ClassVar[str]       = "id_periodique"
    SQL_FIELDS: ClassVar[list[str]] = [
        "id_periodique",
        "libelle",
        "montant",
        "frequence",
        "type_flux",
        "date_prochaine",
        "actif",
        "categorie_id",
        "tiers_id",
        "compte_id",
        "commentaire",
    ]

    # ---- Champs persistés ------------------------------------------ #
    id_periodique:  Optional[int]   = None
    libelle:        str             = ""
    montant:        float           = 0.0
    frequence:      str             = "mensuel"   # mensuel|trimestriel|semestriel|annuel
    type_flux:      str             = "depense"   # depense|revenu
    date_prochaine: Optional[date]  = None
    actif:          int             = 1           # 1=actif, 0=inactif (SQLite bool)
    categorie_id:   Optional[int]   = None
    tiers_id:       Optional[int]   = None
    compte_id:      Optional[int]   = None
    commentaire:    str             = ""

    # ---- Objets liés (transients) ----------------------------------- #
    _TRANSIENT_FIELDS: ClassVar[tuple] = ("categorie_obj", "tiers_obj", "compte_obj")

    categorie_obj:  Optional[Any]   = transient_field(default=None)
    tiers_obj:      Optional[Any]   = transient_field(default=None)
    compte_obj:     Optional[Any]   = transient_field(default=None)

    # ---- Affichage -------------------------------------------------- #

    @property
    def display_name(self) -> str:
        return self.libelle or f"Périodique {self.id_periodique or '(nouveau)'}"

    @property
    def categorie_label(self) -> str:
        if self.categorie_obj:
            return getattr(self.categorie_obj, "display_name", "")
        return ""

    @property
    def tiers_label(self) -> str:
        if self.tiers_obj:
            return getattr(self.tiers_obj, "display_name", "")
        return ""

    @property
    def compte_label(self) -> str:
        if self.compte_obj:
            return getattr(self.compte_obj, "display_name", "")
        return ""

    @property
    def montant_display(self) -> str:
        return f"{self.montant:,.2f} €".replace(",", " ").replace(".", ",")

    @property
    def is_actif(self) -> bool:
        return bool(self.actif)

    # ---- Sérialisation ---------------------------------------------- #

    def to_sql_dict(self) -> dict:
        d = asdict(self)
        for key in self._TRANSIENT_FIELDS:
            d.pop(key, None)
        return {k: d[k] for k in self.SQL_FIELDS if k in d}

    def to_dict(self) -> dict:
        d = self.to_sql_dict()
        d["categorie_label"] = self.categorie_label
        d["tiers_label"]     = self.tiers_label
        d["compte_label"]    = self.compte_label
        d["montant_display"] = self.montant_display
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Periodique":
        import inspect
        valid = set(inspect.signature(cls).parameters.keys())
        return cls(**{k: v for k, v in data.items() if k in valid})
