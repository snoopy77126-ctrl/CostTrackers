# -*- coding: utf-8 -*-
####################################
# Projet : CostTracker
# Fichier : models/budget.py
# Description : Modèle Budget — enveloppes mensuelles par catégorie
# Date : 24/06/2026     Etat : Stable
####################################

from dataclasses import dataclass, field, asdict
from typing import Optional, ClassVar, Any
from datetime import date

from databases.schema_inspector import register_model
from models._model_base import ModelBase, transient_field


@register_model
@dataclass(kw_only=True)
class BudgetLigne(ModelBase):
    """
    Enveloppe budgétaire mensuelle par catégorie.
    Table : budget_lignes
    Une ligne = (categorie, mois, annee) → montant_prevu
    """

    SQL_TABLE:  ClassVar[str]       = "budget_lignes"
    SQL_ID:     ClassVar[str]       = "id_budget"
    SQL_FIELDS: ClassVar[list[str]] = [
        "id_budget",
        "categorie_id",
        "mois",
        "annee",
        "montant_prevu",
        "type_flux",
        "commentaire",
    ]

    id_budget:     Optional[int]  = None
    categorie_id:  Optional[int]  = None
    mois:          int            = 1       # 1–12
    annee:         int            = 2026
    montant_prevu: float          = 0.0
    type_flux:     str            = "depense"   # depense | revenu
    commentaire:   str            = ""

    # Objets liés (transients)
    _TRANSIENT_FIELDS: ClassVar[tuple] = ("categorie_obj",)
    categorie_obj: Optional[Any] = transient_field(default=None)

    # ── Affichage ─────────────────────────────────────────────────────

    @property
    def display_name(self) -> str:
        cat = self.categorie_label or f"Catégorie {self.categorie_id}"
        return f"{cat} — {self.mois:02d}/{self.annee}"

    @property
    def categorie_label(self) -> str:
        if self.categorie_obj:
            return getattr(self.categorie_obj, "display_name", "")
        return ""

    @property
    def periode_label(self) -> str:
        return f"{self.mois:02d}/{self.annee}"

    # ── Sérialisation ─────────────────────────────────────────────────

    def to_sql_dict(self) -> dict:
        d = asdict(self)
        for k in self._TRANSIENT_FIELDS:
            d.pop(k, None)
        return {k: d[k] for k in self.SQL_FIELDS if k in d}

    def to_dict(self) -> dict:
        d = self.to_sql_dict()
        d["categorie_label"] = self.categorie_label
        d["periode_label"]   = self.periode_label
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "BudgetLigne":
        import inspect
        valid = set(inspect.signature(cls).parameters.keys())
        return cls(**{k: v for k, v in data.items() if k in valid})
