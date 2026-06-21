from tkinter import ttk
import tkinter as tk
from typing import Dict, List, Optional, Callable


class BaseTree(ttk.Frame):
    def __init__(self, parent, columns=None, headings=None, callbacks: Optional[Dict[str, Callable]] = None):
        super().__init__(parent)
        self.callbacks = callbacks or {}

        # Conteneur principal pour permettre au FlatTree de pack-er le tree en dessous
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)

        if columns:
            self.tree = ttk.Treeview(self.container, columns=columns, show="headings")
            for col, title in zip(columns, headings or columns):
                self.tree.heading(col, text=title)
        else:
            self.tree = ttk.Treeview(self.container, show="tree")

        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(self.container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.tree.tag_configure("inactive", foreground="gray")
        self.tree.tag_configure("active", foreground="black")
        self.iid_to_row: Dict[str, dict] = {}

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-3>", self._on_right_click)

    # --- Méthodes BaseTree inchangées ---
    def clear(self):
        self.tree.delete(*self.tree.get_children())
        self.iid_to_row.clear()

    def _on_select(self, event):
        row = self._get_selected()
        if row and self.callbacks.get("on_select"): self.callbacks["on_select"](row)

    def _on_double_click(self, event):
        row = self._get_selected()
        if row and self.callbacks.get("on_double_click"): self.callbacks["on_double_click"](row)

    def _on_right_click(self, event):
        row = self._get_selected()
        if row and self.callbacks.get("on_right_click"): self.callbacks["on_right_click"](row, event)

    def _get_selected(self):
        selected = self.tree.selection()
        return self.iid_to_row.get(selected[0]) if selected else None

    def _get_all_selected(self) -> List[dict]:
        """NOUVELLE MÉTHODE : Retourne la liste complète des éléments sélectionnés."""
        selected_iids = self.tree.selection()
        # On construit une liste avec toutes les lignes correspondant aux IIDs sélectionnés
        return [self.iid_to_row.get(iid) for iid in selected_iids if iid in self.iid_to_row]

class FlatTree(BaseTree):
    def insert_rows(self, rows: List[dict]):
        self.clear()
        for row in rows:
            iid = str(row.get("iid_key", row.get("id", "")))
            values = row.get("values") or [row.get(col, "") for col in self.tree["columns"]]
            self.iid_to_row[iid] = row
            self.tree.insert("", "end", iid=iid, values=values)


class TreeView(BaseTree):
    def insert_rows(self, rows: List[dict]):
        self.clear()
        nodes = {}
        for row in rows:
            iid = str(row.get("iid_key", row.get("id", "")))
            parent = nodes.get(str(row.get("parent_id")), "") if row.get("parent_id") else ""
            self.iid_to_row[iid] = row
            nodes[iid] = self.tree.insert(parent, "end", iid=iid, text=row.get("value", ""),
                                          values=row.get("values", []))