# -*- coding: utf-8 -*-
####################################
# Projet : CostTracker
# Fichier : interfaces_tabs/tabs_budget_tree.py
# Description : Treeview des lignes budgétaires
# Date : 24/06/2026     Etat : Stable
####################################

from interfaces_tabs._tabs_generique_tree import FlatTree

COLUMNS  = ("categorie", "type", "prevu", "reel", "ecart", "ratio")
HEADINGS = ("Catégorie", "Type", "Prévu", "Réel", "Écart", "Avancement")


class BudgetTree(FlatTree):
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
        self.tree.column("categorie", width=200)
        self.tree.column("type",      width=70,  anchor="center")
        self.tree.column("prevu",     width=110, anchor="e")
        self.tree.column("reel",      width=110, anchor="e")
        self.tree.column("ecart",     width=110, anchor="e")
        self.tree.column("ratio",     width=80,  anchor="center")

        self.tree.tag_configure("ok",      foreground="#2a7a2a")   # vert
        self.tree.tag_configure("warning", foreground="#cc7700")   # orange
        self.tree.tag_configure("danger",  foreground="#cc2222")   # rouge
        self.tree.tag_configure("revenu",  foreground="#1a5fa8")   # bleu

    def insert_rows(self, rows):
        self.clear()
        for row in rows:
            iid    = str(row.get("iid_key", ""))
            values = row.get("values", [])
            ratio  = float(row.get("ratio", 0))
            t_flux = row.get("type_flux", "depense")

            if t_flux == "revenu":
                tags = ("revenu",)
            elif ratio >= 1.0:
                tags = ("danger",)
            elif ratio >= 0.80:
                tags = ("warning",)
            else:
                tags = ("ok",)

            self.iid_to_row[iid] = row
            self.tree.insert("", "end", iid=iid, values=values, tags=tags)

    def _on_select(self, row):
        cb = self._callbacks_ui.get("on_budget_selected")
        if cb:
            cb(row)

    def _on_double_click(self, row):
        cb = self._callbacks_ui.get("on_budget_opened")
        if cb:
            cb(row)
