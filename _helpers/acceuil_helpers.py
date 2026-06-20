from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import List, Optional

from _helpers._generique_helpers import BaseHelper

class AcceuilHelpers(BaseHelper):
    def __init__(self, services=None):
        self.services = services or {}
        self.compte_tracker = self.services.get("compte")
        self.operation_tracker = self.services.get("operation")
        self.categorie_tracker = self.services.get("categorie")

    def initialise(self):
        for tracker in (self.compte_tracker, self.operation_tracker, self.categorie_tracker):
            if tracker:
                tracker.get_all()

    def operations(self, limit=250):
        if not self.operation_tracker:
            return []
        return self.operation_tracker.get_recent(limit)

    def comptes(self):
        comptes = self.compte_tracker.get_all() if self.compte_tracker else []
        if comptes:
            return comptes

        labels = {}
        for op in self.operations(limit=1000):
            label = (op.compte_label or "").strip()
            if label:
                labels[label] = labels.get(label, 0.0) + float(op.montant or 0)
        return [
            {
                "display_name": label,
                "solde_init": total,
                "est_favori": True,
            }
            for label, total in sorted(labels.items())
        ]

    def operation_rows(self, limit=250):
        rows = []
        solde = 0.0
        for op in reversed(self.operations(limit)):
            solde += float(op.montant or 0)
            rows.append({
                "iid_key": op.id_import_ligne,
                "date_operation": self.format_date(op.date_operation),
                "libelle": op.libelle,
                "tiers": op.tiers_label,
                "categorie": op.categorie_label,
                "debit": self.money(op.debit) if op.debit else "",
                "credit": self.money(op.credit) if op.credit else "",
                "solde": self.money(solde),
                "montant": op.montant,
                "source": op.source,
                "objet": op,
            })
        return list(reversed(rows))

    def compte_rows(self):
        rows = []
        for index, compte in enumerate(self.comptes(), start=1):
            if isinstance(compte, dict):
                name = compte.get("display_name", "")
                solde = compte.get("solde_init", 0.0)
                favori = compte.get("est_favori", True)
                key = name or index
            else:
                name = compte.display_name
                solde = compte.solde_init or self._balance_for_compte(compte.id_compte, name)
                favori = compte.compte_favori
                key = compte.id_compte or index
            rows.append({
                "iid_key": key,
                "compte": name,
                "value": name,
                "mise_a_jour": date.today().strftime("%d/%m/%Y"),
                "solde": self.money(solde),
                "actif": favori,
            })
        return rows

    def categorie_budget_rows(self, limit=5):
        totals = defaultdict(float)

        # 1. Récupération de l'année et du mois en cours
        aujourd_hui = date.today()
        annee_courante = aujourd_hui.year
        mois_courant = aujourd_hui.month

        for op in self.operations(limit=1000):
            # 2. Conversion et extraction de la date de l'opération
            op_date = self.parse_date(op.date_operation)

            # 3. FILTRE : On ignore l'opération si elle n'est pas du mois en cours
            if not op_date or op_date.year != annee_courante or op_date.month != mois_courant:
                continue

            # 4. Traitement habituel pour les dépenses (montant négatif)
            label = op.categorie_label or "Non classe"
            if float(op.montant or 0) < 0:
                totals[label] += abs(float(op.montant or 0))

        return [
            {
                "categorie": label,
                "montant": self.money(total),
                "ratio": min(total / max(max(totals.values(), default=1), 1), 1),
            }
            for label, total in sorted(totals.items(), key=lambda item: item[1], reverse=True)[:limit]
        ]

    def echeance_rows(self, days_window=45):
        today = date.today()
        min_day = today - timedelta(days=730)
        max_day = today + timedelta(days=days_window)
        rows = []
        for op in self.operations(limit=1000):
            op_date = self.parse_date(op.date_operation)
            if not op_date or op_date < min_day or op_date > max_day:
                continue
            rows.append({
                "iid_key": op.id_import_ligne,
                "tiers": op.tiers_label or op.libelle,
                "montant": self.money(op.montant),
                "prochaine": self.format_date(op.date_operation),
                "periodicite": "Ponctuelle",
                "compte": op.compte_label,
                "paye_le": self.format_date(op.date_operation),
                "retard": (today - op_date).days,
                "objet": op,
            })
        return sorted(rows, key=lambda row: row["retard"], reverse=True)

    def tresorerie_points(self, limit=120):
        by_date = defaultdict(float)
        for op in self.operations(limit=limit):
            op_date = self.parse_date(op.date_operation)
            if op_date:
                by_date[op_date] += float(op.montant or 0)
        solde = 0.0
        points = []
        for op_date in sorted(by_date):
            solde += by_date[op_date]
            points.append((op_date.strftime("%d/%m"), solde))
        # return points[-30:]
        return None

    def _balance_for_compte(self, compte_id, compte_label=""):
        total = 0.0
        for op in self.operations(limit=2000):
            if compte_id and op.compte_id == compte_id:
                total += float(op.montant or 0)
            elif compte_label and op.compte_label == compte_label:
                total += float(op.montant or 0)
        return total

    @staticmethod
    def parse_date(value):
        if not value:
            return None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y%m%d"):
            try:
                return datetime.strptime(str(value).split(" ")[0], fmt).date()
            except ValueError:
                continue
        return None

    @classmethod
    def format_date(cls, value):
        parsed = cls.parse_date(value)
        return parsed.strftime("%d/%m/%Y") if parsed else ""

    @staticmethod
    def money(value):
        try:
            amount = float(value or 0)
        except (TypeError, ValueError):
            amount = 0.0
        return f"{amount:,.2f} EUR".replace(",", " ").replace(".", ",")

