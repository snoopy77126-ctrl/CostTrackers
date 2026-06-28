from typing import List

class TiersEditorHelpers:
    def __init__(self, services=None):
        self.services = services or {}
        self.tiers_trackers = self.services.get("tiers")
        self.operation_tracker = self.services.get("operation")
        self.emetteur_current = None

    def initialise(self):
        """Demande au tiers_trackers de rafraîchir ses données."""
        if self.tiers_trackers:
            self.tiers_trackers.get_all()
        if self.operation_tracker:
            self.operation_tracker.get_all()

    def fetch_row_emetteur(self):
        """Format pour le TreeView."""
        # Récupération des données
        data = [
            {
                "iid_key": tiers.id_tiers,
                "id": tiers.id_tiers,
                "value": tiers.display_full or tiers.display_org_first,
                "actif": True,
            } for tiers in self.tiers_trackers.get_all()
        ]

        # Tri par la clé 'value' (ordre croissant par défaut)
        data.sort(key=lambda x: x["value"].lower() if isinstance(x["value"], str) else "")

        return data

    def fetch_data_emetteur(self, emetteur_id):
        obj = self.tiers_trackers.get_by_id(emetteur_id)
        self.emetteur_current = obj
        if not obj:
            return {}

        data = obj.to_dict()
        data["parent_selection"] = None

        return data

    def save_emetteur(self, data):
        """Sauvegarde via le tiers_trackers."""
        data.pop("parent_id", None)
        if self.emetteur_current:
            # Update de l'objet existant
            for key, value in data.items():
                if hasattr(self.emetteur_current, key):
                    setattr(self.emetteur_current, key, value)
            return self.tiers_trackers.update(self.emetteur_current)
        else:
            # Création
            nouveau = self.tiers_trackers.create(**data)
            return self.tiers_trackers.add(nouveau) is not None

    def delete_emetteur(self, data):
        if self.emetteur_current:
            for key, value in data.items():
                if hasattr(self.emetteur_current, key):
                    setattr(self.emetteur_current, key, value)
            return self.tiers_trackers.delete(self.emetteur_current.id_tiers)
        return False

    def fetch_row_operations(self, selected_tiers_id, limit=250):
        if not selected_tiers_id:
            return []

        # 1. On récupère les opérations (assurez-vous que self.operations() filtre déjà par tiers si possible)
        all_ops = self.operations(limit)
        # Filtrage par tiers
        ops = [op for op in all_ops if getattr(op, 'tiers_id', None) == selected_tiers_id]
        rows = []
        soldes_courants = {}

        # 2. On trie les opérations par date (souvent nécessaire pour un calcul de solde cohérent)
        # Si ops est déjà trié, vous pouvez retirer cette ligne.
        ops.sort(key=lambda x: x.date_operation)

        for op in ops:
            compte_label = op.display_name
            montant = (op.credit or 0.0) - (op.debit or 0.0)

            # Mise à jour du solde courant pour ce compte spécifique
            nouveau_solde = soldes_courants.get(compte_label, 0.0) + montant
            soldes_courants[compte_label] = nouveau_solde

            rows.append({
                "iid_key": op.id_import_ligne,
                "date_operation": op.date_operation,
                "libelle": op.libelle,
                "categorie": op.categorie_label,
                "tiers": op.tiers_label,
                "debit": self.money(op.debit) if hasattr(op, 'debit') and op.debit else "",
                "credit": self.money(op.credit) if hasattr(op, 'credit') and op.credit else "",
                "solde": self.money(nouveau_solde),
                "montant": op.montant,
                "source": getattr(op, 'source', 'saisie'),
                "objet": op,
            })

        return rows

    def operations(self, limit=250):
        if not self.operation_tracker:
            return []
        ops = self.operation_tracker.get_recent(limit)
        return ops

    @staticmethod
    def money(value):
        try:
            amount = float(value or 0)
        except (TypeError, ValueError):
            amount = 0.0
        return f"{amount:,.2f} EUR".replace(",", " ").replace(".", ",")

    def _operation_points(self,selected_tiers_id):
        """
        Retourne une liste de tuples (mois "MM/YY", depenses, revenus)
        pour TabsGrafBaton. Les dépenses sont en valeur absolue (>= 0).
        """
        if not selected_tiers_id:
            return []

        rows = self.fetch_row_operations(selected_tiers_id)

        from collections import defaultdict

        monthly_dep = defaultdict(float)
        monthly_rev = defaultdict(float)

        for row in rows:
            op = row["objet"]
            date_obj = op.date_operation
            if not date_obj:
                continue
            month_key = date_obj.strftime("%m/%y")
            montant = float(op.montant or 0)
            if montant < 0:
                monthly_dep[month_key] += abs(montant)   # dépense : valeur absolue
            else:
                monthly_rev[month_key] += montant         # revenu  : positif

        all_keys = set(monthly_dep.keys()) | set(monthly_rev.keys())
        sorted_keys = sorted(all_keys, key=lambda d: (d.split('/')[1], d.split('/')[0]))

        return [(k, monthly_dep[k], monthly_rev[k]) for k in sorted_keys]
