import tkinter as tk
from tkinter import ttk

from _helpers.categorie_fusion_helpers import CategorieFusionHelpers


class CategorieFusionEditor(tk.Toplevel):
    def __init__(self, parent, selected_categories, services=None):
        super().__init__(parent)

        self.title("Fusionner les Catégories")
        self.geometry("900x450")
        self.transient(parent)
        self.grab_set()

        self.services = services
        self.helper = CategorieFusionHelpers(services)
        self.helper.load_data(selected_categories)
        self.callbacks = self._build_callbacks()

        self.build_widgets()
        self._populate_data()

    def build_widgets(self):
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        main_frame = ttk.Frame(self, padding=10)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        cols, headings = self.helper.get_columns_config()
        self.tree = ttk.Treeview(main_frame, columns=cols, show="headings")

        for col, heading in zip(cols, headings):
            self.tree.heading(col, text=heading)
            width = 150 if col in ("champ", "apres") else 120
            self.tree.column(col, width=width, anchor="w")

        self.tree.tag_configure("conflit", foreground="red")
        self.tree.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=(0, 10))

        self.tree.bind("<ButtonRelease-1>", self._on_cell_click)

        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        bottom_frame.columnconfigure(0, weight=1)

        info_text = ("Il y a des conflits. Cliquez sur le contenu à conserver "
                     "dans l'une des colonnes pour l'utiliser dans la colonne Après.")
        ttk.Label(bottom_frame, text=info_text, wraplength=600).grid(row=0, column=0, sticky="w")

        btn_frame = ttk.Frame(bottom_frame)
        btn_frame.grid(row=0, column=1, sticky="e")
        ttk.Button(btn_frame, text="OK",      command=self._action_ok).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Annuler", command=self.destroy).pack(side="left")

    def _build_callbacks(self):
        return {}

    def _populate_data(self):
        rows = self.helper.prepare_rows()
        for row_data in rows:
            tags = ("conflit",) if row_data["conflit"] else ()
            values = (
                row_data["label"],
                row_data["valeur_apres"],
                *row_data["valeurs_tiers"],
            )
            self.tree.insert("", "end", iid=row_data["champ_sql"], values=values, tags=tags)

    def _on_cell_click(self, event):
        """Copie la valeur cliquée (colonne source) vers la colonne Après."""
        if self.tree.identify_region(event.x, event.y) != "cell":
            return

        col_id  = self.tree.identify_column(event.x)
        row_iid = self.tree.identify_row(event.y)
        if not row_iid:
            return

        col_idx = int(col_id.replace("#", "")) - 1
        values  = list(self.tree.item(row_iid, "values"))

        if 2 <= col_idx < len(values):
            values[1] = values[col_idx]
            self.tree.item(row_iid, values=values, tags=())

    def _action_ok(self):
        """Collecte les valeurs finales et lance la fusion."""
        resultats = {}
        for champ_sql in self.tree.get_children():
            values = self.tree.item(champ_sql, "values")
            if len(values) >= 2:
                resultats[champ_sql] = values[1]

        self.helper.executer_fusion(resultats)
        self.destroy()


# ------------------ Main test ------------------
if __name__ == "__main__":
    try:
        from _services._bootstrap_services import build_app_services
        services_app = build_app_services()
    except ImportError:
        services_app = None

    selected_categories = [
        {"iid_key": "c_12", "designation": "SUPERMARCHE"},
        {"iid_key": "c_47", "designation": "SUPERMARCHE"},
    ]

    root = tk.Tk()
    root.geometry("0x0+10000+10000")

    app = CategorieFusionEditor(
        parent=root,
        services=services_app,
        selected_categories=selected_categories,
    )
    app.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()
