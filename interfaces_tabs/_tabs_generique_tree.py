from tkinter import ttk
from typing import Dict, Optional, Callable, List


class BaseTree(ttk.Frame):

    def __init__(
            self,
            parent,
            columns=None,
            headings=None,
            callbacks: Optional[Dict[str, Callable]] = None
    ):
        super().__init__(parent)

        self.callbacks = callbacks or {}

        # =========================
        # TREEVIEW CORE
        # =========================
        if columns:
            self.tree = ttk.Treeview(self, columns=columns, show="headings")
            for col, title in zip(columns, headings or columns):
                self.tree.heading(col, text=title)
        else:
            self.tree = ttk.Treeview(self, show="tree")

        self.tree.pack(side="left", fill="both", expand=True)

        # =========================
        # SCROLLBAR
        # =========================
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # =========================
        # STYLES
        # =========================
        self.tree.tag_configure("inactive", foreground="gray")
        self.tree.tag_configure("active", foreground="black")

        # =========================
        # CACHE UI
        # =========================
        self.iid_to_row: Dict[str, dict] = {}

        # =========================
        # EVENTS
        # =========================
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-3>", self._on_right_click)

    # =========================================================
    # CORE API (RESET)
    # =========================================================
    def clear(self):
        self.tree.delete(*self.tree.get_children())
        self.iid_to_row.clear()

    def insert_row(self, iid: str, values=None, text=None, parent=""):
        self.tree.insert(
            parent,
            "end",
            iid=iid,
            values=values,
            text=text
        )

    # =========================================================
    # EVENTS
    # =========================================================
    def _get_selected(self):
        selected = self.tree.selection()
        if not selected:
            return None

        iid = selected[0]
        return self.iid_to_row.get(iid)

    def _get_all_selected(self) -> List[dict]:
        """NOUVELLE MÉTHODE : Retourne la liste complète des éléments sélectionnés."""
        selected_iids = self.tree.selection()
        # On construit une liste avec toutes les lignes correspondant aux IIDs sélectionnés
        return [self.iid_to_row.get(iid) for iid in selected_iids if iid in self.iid_to_row]

    def _on_select(self, event):
        row = self._get_selected()
        cb = self.callbacks.get("on_select")
        if row and cb:
            cb(row)

    def _on_double_click(self, event):
        row = self._get_selected()
        cb = self.callbacks.get("on_double_click")
        if row and cb:
            cb(row)

    def _on_right_click(self, event):
        row = self._get_selected()
        cb = self.callbacks.get("on_right_click")
        if row and cb:
            cb(row, event)


class FlatTree(BaseTree):

    def insert_rows(self, rows: List[dict]):
        self.clear()

        for row in rows:
            iid = str(row["iid_key"])

            values = row.get("values") or [
                row.get(col, "") for col in self.tree["columns"]
            ]

            tag = "active" if row.get("actif", True) else "inactive"

            self.iid_to_row[iid] = row

            self.tree.insert(
                "",
                "end",
                iid=iid,
                values=values,
                tags=(tag,)
            )


class TreeView(BaseTree):

    def insert_rows(self, rows: List[dict]):
        self.clear()
        nodes = {}

        for row in rows:
            iid = str(row["iid_key"]) or row["id"]
            parent_id = row.get("parent_id")
            tag = "active" if row.get("actif", True) else "inactive"

            # Logique NEUTRE :
            # On cherche d'abord dans 'values', sinon on mappe les clés
            # correspondant aux noms des colonnes du Treeview.
            values = row.get("values") or [
                row.get(col, "") for col in self.tree["columns"]
            ]

            self.iid_to_row[iid] = row

            # Détermination du parent (si parent_id est None ou vide, parent = "")
            parent = nodes.get(str(parent_id), "") if parent_id else ""

            # Insertion
            node = self.tree.insert(
                parent,
                "end",
                iid=iid,
                text=row["value"],  # Données pour le mode 'headings'
                tags=(tag,)
            )

            nodes[iid] = node

