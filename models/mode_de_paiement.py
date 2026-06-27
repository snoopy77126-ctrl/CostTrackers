# -*- coding: utf-8 -*-
####################################
# Projet : CostTracker
# Fichier : models/mode_de_paiement.py
# Description : Modes de paiement (carte, espèces, virement, etc.)
# Date : 24/06/2026     Etat : Stable
####################################

from dataclasses import dataclass
from typing import Optional, ClassVar

from models._model_base import ModelBase


# ══════════════════════════════════════════════════════════════════════ #
#  MODE DE PAIEMENT
# ══════════════════════════════════════════════════════════════════════ #

@dataclass(kw_only=True)
class ModeDePaiement(ModelBase):
    """
    Représente un mode de paiement : carte, espèces, virement, prélèvement, etc.
    Correspond à une ligne de la table `mode_de_paiement`.
    """
    SORT_KEY = "display_name"
    SQL_ID:     ClassVar[str]       = "id_mode_paiement"
    SQL_FIELDS: ClassVar[list[str]] = [
        "id_mode_paiement", "code", "designation", "description"
    ]

    # ---- Champs de données ------------------------------------------ #
    id_mode_paiement: Optional[int] = None
    code:            str           = ""  # Code court (ex: "CB", "ESP", "VIR")
    designation:     str           = ""  # Nom complet (ex: "Carte Bancaire")
    description:     str           = ""  # Description détaillée
    # ---- Affichage -------------------------------------------------- #

    @property
    def display_name(self) -> str:
        """Format : CODE - DESIGNATION."""
        code = (self.code or "").upper().strip()
        designation = (self.designation or "").strip()
        if code and designation:
            return f"{code} - {designation}"
        return designation or code or f"Mode {self.id_mode_paiement or '(nouveau)'}"

    @property
    def display_short(self) -> str:
        """Format court pour les listes : CODE."""
        return (self.code or "").upper() or self.display_name

    @property
    def display_full(self) -> str:
        """Format complet avec description."""
        result = self.display_name
        if self.description:
            result += f" ({self.description})"
        return result

    def __repr__(self) -> str:
        return self.display_name

    # ---- Sérialisation ---------------------------------------------- #

    def to_dict(self) -> dict:
        return {
            "id_mode_paiement": self.id_mode_paiement,
            "code": self.code,
            "designation": self.designation,
            "description": self.description,
        }

    def to_sql_dict(self) -> dict:
        """Identique à to_dict pour ce modèle (pas de champs transients)."""
        return self.to_dict()
