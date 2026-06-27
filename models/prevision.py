# models/prevision.py
from dataclasses import dataclass, field
from typing import Optional, ClassVar, List
from datetime import date
from models._model_base import ModelBase, transient_field


@dataclass(kw_only=True)
class Prevision(ModelBase):
    """
    Représente une période budgétaire (ex: 'Juillet - Vacances', 'Septembre - Travail').
    """
    SQL_TABLE: ClassVar[str] = "previsions"
    SQL_ID: ClassVar[str] = "id_prevision"

    id_prevision: Optional[int] = None
    libelle: str = ""  # Ex: "Période Vacances Été"
    date_debut: date = None
    date_fin: date = None
    type_periode: str = "travail"  # travail, repos, vacances

    # Liste des détails de budget spécifiques à cette période (hors périodiques)
    details: List["PrevisionDetail"] = transient_field(default_factory=list)

    @property
    def display_name(self) -> str:
        return f"{self.libelle} ({self.type_periode})"


@dataclass(kw_only=True)
class PrevisionDetail(ModelBase):
    """
    Dépense ponctuelle spécifique à une prévision.
    """
    SQL_TABLE: ClassVar[str] = "prevision_details"
    SQL_ID: ClassVar[str] = "id_detail"

    id_detail: Optional[int] = None
    prevision_id: int = 0
    libelle: str = ""
    montant: float = 0.0
    categorie_id: int = 0