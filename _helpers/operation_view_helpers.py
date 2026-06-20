from typing import List, Optional, Dict, Any
from collections import defaultdict
from datetime import date, datetime, timedelta

from ._generique_helpers import BaseHelper


class OperationsViewHelpers(BaseHelper):
    """
    Helper pour l'éditeur d'opérations.
    Hérite de BaseHelper pour la résolution des clés étrangères.
    """

    def __init__(self, services):
        # On passe le dictionnaire de tiers_trackers au BaseHelper
        super().__init__(services)
        self.operation_tracker = services.get('operation')
        self.tiers_tracker = services.get('tiers')
        self.compte_tracker = services.get('compte')
        self.categorie_tracker = services.get('categorie')

    def initialise(self):
        """Initialise les trackers et charge les données."""
        if self.operation_tracker:
            self.operation_tracker.load_all()
        if self.tiers_tracker:
            self.tiers_tracker.load_all()
        if self.compte_tracker:
            self.compte_tracker.load_all()
        if self.categorie_tracker:
            self.categorie_tracker.load_all()

    def fetch_tiers(self) -> List[Dict[str, Any]]:
        """Récupère la liste des tiers pour la combobox."""
        if not self.tiers_tracker:
            return []
        tiers = self.tiers_tracker.get_all()
        return [{"id": t.id_tiers, "value": t.display_name if hasattr(t, 'display_name') else str(t)} for t in tiers]

    def fetch_comptes(self) -> List[Dict[str, Any]]:
        """Récupère la liste des comptes pour la combobox."""
        if not self.compte_tracker:
            return []
        comptes = self.compte_tracker.get_all()
        return [{"id": c.id_compte, "value": c.display_name if hasattr(c, 'display_name') else str(c)} for c in comptes]

    def fetch_categories(self) -> List[Dict[str, Any]]:
        """Récupère la liste des catégories pour la combobox."""
        if not self.categorie_tracker:
            return []
        categories = self.categorie_tracker.get_all()
        return [{"id": c.id_categorie, "value": c.designation if hasattr(c, 'designation') else str(c)} for c in categories]

    def fetch_data_by_iid(self, operation_id: int) -> Optional[Dict[str, Any]]:
        """Récupère les données d'une opération par son ID."""
        if not self.operation_tracker or not operation_id:
            return None
        operation = self.operation_tracker.get_by_id(operation_id)
        if not operation:
            return None
        self.operation_current = operation
        return operation.to_dict() if hasattr(operation, 'to_dict') else operation.__dict__

    def save_operation(self, data: Dict[str, Any]) -> bool:
        if not self.operation_tracker:
            return False

        data = self._fill_labels_from_associations(data)
        data['source'] = 'saisie'  # ← toujours forcer la source

        data.pop('compte_label', None)
        data.pop('categorie_label', None)
        data.pop('tiers_label', None)
        # ------------------------------
        current_id = getattr(self.operation_current, 'id_import_ligne', None) \
            if self.operation_current else None

        if current_id:
            operation = self.operation_current
            self.apply_form_to_object(operation, data, fk_fields=['tiers_id', 'compte_id', 'categorie_id'])
            success = self.operation_tracker.update(operation)
        else:
            operation = self.operation_tracker.create()
            self.apply_form_to_object(operation, data, fk_fields=['tiers_id', 'compte_id', 'categorie_id'])
            new_operation = self.operation_tracker.add(operation)
            success = new_operation is not None
            if success:
                self.operation_current = new_operation

        return success

    def _fill_labels_from_associations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remplit les champs label depuis les tables associées."""
        # Compte label
        compte_id = data.get('compte_id')
        if compte_id and self.compte_tracker:
            compte = self.compte_tracker.get_by_id(compte_id)
            if compte and hasattr(compte, 'display_name'):
                data['compte_label'] = compte.display_name
            elif compte and hasattr(compte, 'nom_du_compte'):
                data['compte_label'] = compte.nom_du_compte
        
        # Tiers label
        tiers_id = data.get('tiers_id')
        if tiers_id and self.tiers_tracker:
            tiers = self.tiers_tracker.get_by_id(tiers_id)
            if tiers and hasattr(tiers, 'display_full'):
                data['tiers_label'] = tiers.display_full
            elif tiers and hasattr(tiers, 'display_short'):
                data['tiers_label'] = tiers.display_short
            elif tiers and hasattr(tiers, 'organisation'):
                data['tiers_label'] = tiers.organisation
        
        # Catégorie label
        categorie_id = data.get('categorie_id')
        if categorie_id and self.categorie_tracker:
            categorie = self.categorie_tracker.get_by_id(categorie_id)
            if categorie and hasattr(categorie, 'display_name'):
                data['categorie_label'] = categorie.display_name
            elif categorie and hasattr(categorie, 'designation'):
                data['categorie_label'] = categorie.designation
        
        return data

    def get_filtered_rows(self, compte_key, compte_value, periode_key):
        print(f'[DEBUG]OperationsViewHelpers:get_filtered_rows')
        """Logique métier de filtrage centralisée."""
        rows = self.operation_tracker.get_all()  # Récupération des données via le tracker
        print(f'[DEBUG]rows: {rows}')
        # 1. Filtrage par compte
        if compte_key != "tlc":
            print(f'[DEBUG]compte_key= {compte_key}')
            rows = [r for r in rows if getattr(r, "compte_id", "") == compte_value]

        # 2. Filtrage par période
        return self._apply_periode_filter(rows, periode_key)

    def _apply_periode_filter(self, rows, periode_key):
        if periode_key == "toutesdates": return rows

        today = date.today()
        # Calculs de dates (mois précédent, etc.)
        mois_prec = (today.month - 2) % 12 + 1
        annee_prec_mois = today.year if today.month > 1 else today.year - 1

        filtres = {
            "mois_courant": lambda d: d.year == today.year and d.month == today.month,
            "mois_precedent": lambda d: d.year == annee_prec_mois and d.month == mois_prec,
            "3_mois": lambda d: (today.year - d.year) * 12 + (today.month - d.month) < 3,
            "annee_courante": lambda d: d.year == today.year,
            "annee_precedente": lambda d: d.year == today.year - 1,
        }

        filtre_fn = filtres.get(periode_key)
        if not filtre_fn: return rows

        # Utilisation d'une méthode de parsing de date (assurez-vous qu'elle existe dans BaseHelper ou ajoutez-la ici)
        return [
            r for r in rows
            if (op_date := self.parse_date(r.date_operation)) and filtre_fn(op_date)
        ]
    def get_total_mouvement(self, rows):
        return sum(float(r.objet.montant or 0) for r in rows)

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
                "iid_key": op.id_saisie,
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


