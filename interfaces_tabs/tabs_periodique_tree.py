# -*- coding: utf-8 -*-
from interfaces_tabs._tabs_generique_tree import FlatTree

COLUMNS  = ("libelle", "tiers", "categorie", "compte", "montant", "frequence", "prochaine", "actif")
HEADINGS = ("Libellé", "Tiers", "Catégorie", "Compte", "Montant", "Fréquence", "Prochaine éch.", "Actif")


class PeriodiqueTree(FlatTree):
    def __init__(self, parent, callbacks=None):
        self._callbacks_ui = callbacks or {}
        super().__init__(
            parent,
            columns=COLUMNS,
            headings=HEADINGS,
            callbacks={
                "on_select":       self._on_select,
                "on_double_click": self._on_double_click,
            }
        )
        # Largeurs de colonnes
        self.tree.column("libelle",   width=180)
        self.tree.column("tiers",     width=130)
        self.tree.column("categorie", width=130)
        self.tree.column("compte",    width=120)
        self.tree.column("montant",   width=90,  anchor="e")
        self.tree.column("frequence", width=90)
        self.tree.column("prochaine", width=100)
        self.tree.column("actif",     width=45,  anchor="center")

        self.tree.tag_configure("inactif", foreground="gray")
        self.tree.tag_configure("due",     foreground="red")

    def insert_rows(self, rows):
        from datetime import date, datetime
        today = date.today()
        self.clear()

        for row in rows:
            iid = str(row.get("iid_key", ""))
            values = row.get("values", [])
            tags = []
            obj = row.get("objet")

            if obj and not obj.is_actif:
                tags.append("inactif")
            elif obj and obj.date_prochaine:
                # Conversion sécurisée de date_prochaine
                date_prochaine = obj.date_prochaine
                if isinstance(date_prochaine, str):
                    try:
                        # Adaptez le format '%Y-%m-%d' si votre base utilise un autre format
                        date_prochaine = datetime.strptime(date_prochaine, '%Y-%m-%d').date()
                    except ValueError:
                        # Optionnel : gérer les cas où la date est mal formatée
                        pass

                # Comparaison maintenant possible
                if isinstance(date_prochaine, date) and date_prochaine <= today:
                    tags.append("due")

            self.iid_to_row[iid] = row
            self.tree.insert("", "end", iid=iid, values=values, tags=tags)
    def _on_select(self, row):
        cb = self._callbacks_ui.get("on_periodique_selected")
        if cb: cb(row)

    def _on_double_click(self, row):
        cb = self._callbacks_ui.get("on_periodique_opened")
        if cb: cb(row)
