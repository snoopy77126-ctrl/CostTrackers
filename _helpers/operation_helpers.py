from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import List, Optional

from _helpers._generique_helpers import BaseHelper

class OperationHelpers(BaseHelper):
    def __init__(self, services=None):

        self.trackers = services or {}
        # Propriétés ou raccourcis d'accès
        self.compte_tracker = services.get("compte")
        self.operation_tracker = services.get("operation")
        self.categorie_tracker = services.get("categorie")

        # Appel au parent BaseHelper
        super().__init__({
            "compte": self.compte_tracker,
            "operation": self.operation_tracker,
            "categorie": self.categorie_tracker
        })

    def initialise(self):
        """Demande au tiers_trackers de rafraîchir ses données."""
        self.compte_tracker.get_all()
        self.operation_tracker.get_all()
        self.categorie_tracker.get_all()


    def operations(self, limit=250):
        if not self.operation_tracker:
            return []
        return self.operation_tracker.get_recent(limit)

    def operation_rows(self, limit=250):
        rows = []

        # 1. On récupère les opérations
        ops = self.operations(limit)

        # 2. On groupe par compte pour calculer le solde courant de CHAQUE compte
        # (Car dans cette liste "tlc" - tous les comptes - les opérations sont mélangées !)
        soldes_courants = {}
        for c in self.comptes():
            key = getattr(c, 'display_name', '') or getattr(c, 'nom_du_compte', '')
            # Attention, selon la façon dont tu récupères les comptes, adapte ceci
            solde_initial = c.get('solde_init', 0.0) if isinstance(c, dict) else getattr(c, 'solde_init', 0.0)
            soldes_courants[key] = float(solde_initial or 0.0)

        # 3. On parcours dans l'ordre chronologique inverse (du plus récent au plus ancien)
        # Mais on VEUT afficher un solde courant décrémenté !
        for op in ops:
            print(f'operation_rows:op={op}')
            compte_label = op.display_name

            # Le solde sur cette ligne est le solde courant
            solde_ligne = soldes_courants.get(compte_label, 0.0)

            rows.append({
                "iid_key": op.id_import_ligne,  # Attention à bien gérer les IDs !
                "date_operation": op.date_operation,
                "libelle": op.libelle,
                "categorie":op.categorie_label,
                "tiers":op.tiers_label,
                "debit": self.money(op.debit) if hasattr(op, 'debit') and op.debit else "",
                "credit": self.money(op.credit) if hasattr(op, 'credit') and op.credit else "",
                "solde": self.money(solde_ligne),  # On injecte le solde calculé
                "montant": op.montant,
                "source": getattr(op, 'source', 'saisie'),
                "objet": op,
            })

            # On DÉDUIT le montant pour l'opération précédente (plus ancienne)
            if compte_label in soldes_courants:
                soldes_courants[compte_label] -= float(op.montant or 0)

        return rows  # Pas besoin de re-reversed ici si l'arbre Tkinter l'affiche correctement

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
                "paye_le": self.format_date(op.date_valeur),
                "retard": (today - op_date).days,
                "objet": op,
            })
        return sorted(rows, key=lambda row: row["retard"], reverse=True)

    def tresorerie_points(self, rows=None, limit=120):
        by_date = defaultdict(float)

        # 1. Si aucune liste n'est fournie, on récupère toutes les lignes par défaut
        if rows is None:
            rows = self.operation_rows(limit=limit)

        # 2. On boucle sur les lignes (qui sont vos dictionnaires contenant "objet")
        for row in rows:
            op = row["objet"]
            op_date = self.parse_date(op.date_operation)
            if op_date:
                by_date[op_date] += float(op.montant or 0)

        solde = 0.0
        points = []
        for op_date in sorted(by_date):
            solde += by_date[op_date]
            points.append((op_date.strftime("%d/%m"), solde))

        # 3. Retourne tous les points calculés (ou points[-30:] si vous voulez vraiment brider l'affichage)
        return points

    def _balance_for_compte(self, compte_id, compte_label=""):
        total = 0.0
        for op in self.operations(limit=2000):
            if compte_id and op.compte_id == compte_id:
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

