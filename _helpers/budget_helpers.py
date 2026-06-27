# -*- coding: utf-8 -*-
####################################
# Projet : CostTracker
# Fichier : _helpers/budget_helpers.py
# Description : Logique métier du module Budget
# Date : 24/06/2026     Etat : Stable
####################################

from datetime import date
from typing import List, Optional

from models.budget import BudgetLigne


class BudgetHelpers:
    def __init__(self, services: dict):
        self.services       = services
        self.tracker        = services.get("budget")
        self.cat_tracker    = services.get("categorie")
        self.op_tracker     = services.get("operation")
        self.current_id: Optional[int] = None
        self._mois  = date.today().month
        self._annee = date.today().year

    # ── Init ──────────────────────────────────────────────────────────

    def initialise(self):
        if self.tracker:    self.tracker.load_all()
        if self.cat_tracker: self.cat_tracker.load_all()
        if self.op_tracker:  self.op_tracker.load_all()

    def set_periode(self, mois: int, annee: int):
        self._mois  = mois
        self._annee = annee

    # ── Dépenses réelles (depuis les opérations) ──────────────────────

    def _get_reel_par_categorie(self) -> dict:
        """Calcule le total des dépenses réelles par categorie_id pour la période courante."""
        if not self.op_tracker:
            return {}

        from _services.dates_services import DatesManager
        d_debut, d_fin = DatesManager.get_date_bounds("mois_en_cours")

        try:
            ops = self.op_tracker.manager.get_filtered(
                compte_id=None,
                date_debut=str(d_debut) if d_debut else None,
                date_fin=str(d_fin) if d_fin else None
            )
        except Exception:
            ops = []

        totaux: dict = {}
        for op in ops:
            if op and op.categorie_id and op.montant:
                totaux[op.categorie_id] = totaux.get(op.categorie_id, 0.0) + float(op.montant or 0)
        return totaux

    # ── Lignes pour le Treeview ───────────────────────────────────────

    def fetch_rows(self) -> List[dict]:
        lignes  = self.tracker.get_by_periode(self._mois, self._annee) if self.tracker else []
        reels   = self._get_reel_par_categorie()
        rows    = []

        for b in sorted(lignes, key=lambda x: x.categorie_label.lower()):
            prevu = float(b.montant_prevu or 0)
            reel  = abs(float(reels.get(b.categorie_id, 0)))
            ecart = prevu - reel
            ratio = min(reel / prevu, 1.0) if prevu > 0 else 0.0

            rows.append({
                "iid_key": b.id_budget,
                "id":      b.id_budget,
                "values": [
                    b.categorie_label or "—",
                    b.type_flux.capitalize(),
                    f"{prevu:,.2f} €".replace(",", " ").replace(".", ","),
                    f"{reel:,.2f} €".replace(",", " ").replace(".", ","),
                    f"{ecart:,.2f} €".replace(",", " ").replace(".", ","),
                    f"{ratio * 100:.0f} %",
                ],
                "ratio":      ratio,
                "prevu":      prevu,
                "reel":       reel,
                "ecart":      ecart,
                "type_flux":  b.type_flux,
                "objet":      b,
            })

        return rows

    def fetch_resume(self) -> dict:
        """Totaux globaux dépenses/revenus pour l'en-tête de la vue."""
        rows   = self.fetch_rows()
        total_depenses_prevu = sum(r["prevu"] for r in rows if r["type_flux"] == "depense")
        total_depenses_reel  = sum(r["reel"]  for r in rows if r["type_flux"] == "depense")
        total_revenus_prevu  = sum(r["prevu"] for r in rows if r["type_flux"] == "revenu")
        total_revenus_reel   = sum(r["reel"]  for r in rows if r["type_flux"] == "revenu")
        return {
            "depenses_prevu": total_depenses_prevu,
            "depenses_reel":  total_depenses_reel,
            "revenus_prevu":  total_revenus_prevu,
            "revenus_reel":   total_revenus_reel,
            "solde_prevu":    total_revenus_prevu - total_depenses_prevu,
            "solde_reel":     total_revenus_reel  - total_depenses_reel,
        }

    # ── Données pour le formulaire ────────────────────────────────────

    def fetch_data(self, id_budget: int) -> dict:
        obj = self.tracker.get_by_id(id_budget) if self.tracker else None
        self.current_id = id_budget if obj else None
        if not obj:
            return {}
        data = obj.to_dict()
        data["categorie_id"] = {
            "iid_key":       obj.categorie_id,
            "value":         obj.categorie_label,
            "display_value": obj.categorie_label,
        }
        return data

    # ── Combobox options ──────────────────────────────────────────────

    def fetch_categories(self) -> List[dict]:
        if not self.cat_tracker:
            return []
        items = sorted(self.cat_tracker.get_all(), key=lambda c: c.display_name.lower())
        return [
            {"iid_key": c.id_categorie, "value": c.display_name, "display_value": c.display_name}
            for c in items
        ]

    @staticmethod
    def fetch_types_flux() -> List[dict]:
        return [
            {"iid_key": "depense", "value": "Dépense", "display_value": "Dépense"},
            {"iid_key": "revenu",  "value": "Revenu",  "display_value": "Revenu"},
        ]

    @staticmethod
    def fetch_periodes() -> List[dict]:
        """12 derniers mois + 3 prochains."""
        from dateutil.relativedelta import relativedelta  # type: ignore
        today   = date.today()
        result  = []
        for delta in range(-11, 4):
            try:
                from dateutil.relativedelta import relativedelta as rd
                d = today.replace(day=1)
                # Simple calcul sans dateutil
                m = today.month + delta
                y = today.year + (m - 1) // 12
                m = (m - 1) % 12 + 1
                result.append({
                    "iid_key": f"{m:02d}/{y}",
                    "value":   f"{m:02d}/{y}",
                    "display_value": f"{m:02d}/{y}",
                    "mois": m, "annee": y,
                })
            except Exception:
                pass
        return result

    # ── Initialisation rapide depuis les périodiques ──────────────────

    def init_from_periodiques(self, mois: int, annee: int) -> int:
        """Crée les lignes budgétaires manquantes depuis les charges périodiques."""
        if not self.tracker:
            return 0
        per_tracker = self.services.get("periodique")
        if not per_tracker:
            return 0

        created = 0
        for p in per_tracker.get_all():
            if not p.is_actif or not p.categorie_id:
                continue
            existing = self.tracker.get_or_create(p.categorie_id, mois, annee, p.type_flux)
            if existing.id_budget is None:
                # Nouvelle ligne à créer
                existing.montant_prevu = float(p.montant or 0)
                result = self.tracker.add(existing)
                if result:
                    created += 1
        return created

    # ── CRUD ──────────────────────────────────────────────────────────

    def save(self, data: dict) -> bool:
        if not self.tracker:
            return False

        cat_val = data.get("categorie_id")
        if isinstance(cat_val, dict):
            categorie_id = cat_val.get("iid_key")
        else:
            categorie_id = cat_val

        type_val = data.get("type_flux")
        if isinstance(type_val, dict):
            type_flux = type_val.get("iid_key", "depense")
        else:
            type_flux = type_val or "depense"

        try:
            montant = float(str(data.get("montant_prevu", "0")).replace(",", ".").replace(" ", "") or 0)
        except ValueError:
            montant = 0.0

        if self.current_id:
            obj = self.tracker.get_by_id(self.current_id)
            if not obj:
                return False
            obj.categorie_id  = categorie_id
            obj.montant_prevu = montant
            obj.type_flux     = type_flux
            obj.commentaire   = data.get("commentaire", "")
            return self.tracker.update(obj)
        else:
            obj = BudgetLigne(
                categorie_id  = categorie_id,
                mois          = self._mois,
                annee         = self._annee,
                montant_prevu = montant,
                type_flux     = type_flux,
                commentaire   = data.get("commentaire", ""),
            )
            result = self.tracker.add(obj)
            if result:
                self.current_id = result.id_budget
            return result is not None

    def delete(self) -> bool:
        if self.tracker and self.current_id:
            ok = self.tracker.delete(self.current_id)
            if ok:
                self.current_id = None
            return ok
        return False
