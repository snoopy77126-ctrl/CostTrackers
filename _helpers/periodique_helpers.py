# -*- coding: utf-8 -*-
####################################
# Projet : CostTracker
# Fichier : _helpers/periodique_helpers.py
# Description : Logique métier pour la vue et l'éditeur des périodiques
# Date : 23/06/2026     Etat : Stable
####################################

from datetime import date
from typing import List, Optional

from models.periodiques import Periodique, FREQUENCES, TYPES_FLUX


class PeriodiqueHelpers:
    def __init__(self, services: dict):
        self.services           = services
        self.tracker            = services.get("periodique")
        self.cat_tracker        = services.get("categorie")
        self.tiers_tracker      = services.get("tiers")
        self.compte_tracker     = services.get("compte")
        self.current_id: Optional[int] = None

    # ── Init / Refresh ────────────────────────────────────────────────

    def initialise(self):
        if self.tracker:       self.tracker.load_all()
        if self.cat_tracker:   self.cat_tracker.load_all()
        if self.tiers_tracker: self.tiers_tracker.load_all()
        if self.compte_tracker:self.compte_tracker.load_all()

    # ── Lignes pour le Treeview ───────────────────────────────────────

    def fetch_rows(self) -> List[dict]:
        items = self.tracker.get_all() if self.tracker else []
        rows  = []
        for p in items:
            rows.append({
                "iid_key":       p.id_periodique,
                "id":            p.id_periodique,
                "values": [
                    p.libelle,
                    p.tiers_label   or "",
                    p.categorie_label or "",
                    p.compte_label  or "",
                    p.montant_display,
                    p.frequence.capitalize(),
                    str(p.date_prochaine) if p.date_prochaine else "",
                    "✓" if p.is_actif else "✗",
                ],
                "actif": p.is_actif,
                "objet": p,
            })
        rows.sort(key=lambda r: (not r["actif"], r["values"][0].lower()))
        return rows

    # ── Données d'un périodique pour le formulaire ───────────────────

    def fetch_data(self, pid: int) -> dict:
        obj = self.tracker.get_by_id(pid) if self.tracker else None
        self.current_id = pid if obj else None
        if not obj:
            return {}

        data = obj.to_dict()

        # Comboboxes structurées
        data["categorie_id"] = {
            "iid_key":      obj.categorie_id,
            "value":        obj.categorie_label,
            "display_value": obj.categorie_label,
        }
        data["tiers_id"] = {
            "iid_key":      obj.tiers_id,
            "value":        obj.tiers_label,
            "display_value": obj.tiers_label,
        }
        data["compte_id"] = {
            "iid_key":      obj.compte_id,
            "value":        obj.compte_label,
            "display_value": obj.compte_label,
        }
        return data

    # ── Options pour les comboboxes ───────────────────────────────────

    def fetch_categories(self) -> List[dict]:
        if not self.cat_tracker:
            return []
        return [
            {"iid_key": c.id_categorie, "value": c.display_name, "display_value": c.display_name}
            for c in self.cat_tracker.get_all()
        ]

    def fetch_tiers(self) -> List[dict]:
        if not self.tiers_tracker:
            return []
        items = sorted(self.tiers_tracker.get_all(), key=lambda t: t.display_name.lower())
        return [
            {"iid_key": t.id_tiers, "value": t.display_name, "display_value": t.display_name}
            for t in items
        ]

    def fetch_comptes(self) -> List[dict]:
        if not self.compte_tracker:
            return []
        items = sorted(self.compte_tracker.get_all(), key=lambda c: c.display_name.lower())
        return [
            {"iid_key": c.id_compte, "value": c.display_name, "display_value": c.display_name}
            for c in items
        ]

    @staticmethod
    def fetch_frequences() -> List[dict]:
        return [{"iid_key": f, "value": f.capitalize(), "display_value": f.capitalize()} for f in FREQUENCES]

    @staticmethod
    def fetch_types_flux() -> List[dict]:
        labels = {"depense": "Dépense", "revenu": "Revenu"}
        return [{"iid_key": f, "value": labels[f], "display_value": labels[f]} for f in TYPES_FLUX]

    # ── Sauvegarde ────────────────────────────────────────────────────

    def save(self, data: dict) -> bool:
        if not self.tracker:
            return False

        # Extraire les IDs depuis les dicts combobox
        categorie_id = self._extract_id(data.get("categorie_id"))
        tiers_id     = self._extract_id(data.get("tiers_id"))
        compte_id    = self._extract_id(data.get("compte_id"))
        frequence    = self._extract_id(data.get("frequence")) or data.get("frequence", "mensuel")
        type_flux    = self._extract_id(data.get("type_flux")) or data.get("type_flux", "depense")

        if self.current_id:
            obj = self.tracker.get_by_id(self.current_id)
            if not obj:
                return False
            obj.libelle        = data.get("libelle", obj.libelle)
            obj.montant        = float(data.get("montant") or 0)
            obj.frequence      = frequence
            obj.type_flux      = type_flux
            obj.date_prochaine = data.get("date_prochaine") or obj.date_prochaine
            obj.actif          = 1 if data.get("actif") else 0
            obj.commentaire    = data.get("commentaire", "")
            obj.categorie_id   = categorie_id
            obj.tiers_id       = tiers_id
            obj.compte_id      = compte_id
            return self.tracker.update(obj)
        else:
            obj = Periodique(
                libelle        = data.get("libelle", ""),
                montant        = float(data.get("montant") or 0),
                frequence      = frequence,
                type_flux      = type_flux,
                date_prochaine = data.get("date_prochaine"),
                actif          = 1 if data.get("actif", True) else 0,
                commentaire    = data.get("commentaire", ""),
                categorie_id   = categorie_id,
                tiers_id       = tiers_id,
                compte_id      = compte_id,
            )
            result = self.tracker.add(obj)
            if result:
                self.current_id = result.id_periodique
            return result is not None

    def delete(self) -> bool:
        if self.tracker and self.current_id:
            ok = self.tracker.delete(self.current_id)
            if ok:
                self.current_id = None
            return ok
        return False

    # ── Génération des occurrences ────────────────────────────────────

    def get_echeances_dues(self) -> List[Periodique]:
        if not self.tracker:
            return []
        return self.tracker.get_echeances_dues()

    def avancer_echeance(self, pid: int) -> bool:
        if not self.tracker:
            return False
        obj = self.tracker.get_by_id(pid)
        if not obj:
            return False
        return self.tracker.avancer_echeance(obj)

    # ── Utils ─────────────────────────────────────────────────────────

    @staticmethod
    def _extract_id(value):
        if value is None:
            return None
        if isinstance(value, dict):
            return value.get("iid_key")
        return value
