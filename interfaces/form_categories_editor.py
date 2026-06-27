import tkinter as tk
from tkinter import ttk

from _helpers.categorie_editor_helpers import CategorieEditorHelpers
from interfaces_mod.mod_categorie_editor import CategorieEditor
from interfaces_mod.mod_categorie_fusion import CategorieFusionEditor
from interfaces_tabs._tabs_graf import TabsGraf, TabsGrafBaton
from interfaces_tabs.tabs_categorie_editor_button import EditorButton
from interfaces_tabs.tabs_categorie_editor_tree import CategoryTree
from interfaces_tabs.tabs_operation_view_tree import OperationTree

GRID = dict(sticky="nsew", padx=2, pady=2)


class CategoriesViewEditor(tk.Frame):
    """
    Vue principale :
        - Gestion des catégories de dépenses
        - Affichage des opérations affectées
        - Zone graphique/statistiques
    """

    def __init__(self, parent, services):
        super().__init__(parent)
        fenetre_principale = parent.winfo_toplevel()
        fenetre_principale.title("Éditeur de Catégories - Gestion Financière")

        self.services = services
        self.helper = CategorieEditorHelpers(services)

        # ------------------- CALLBACKS -------------------
        self.callbacks = self._build_callbacks()

        # ------------------- UI -------------------
        self.build_widgets()

        # ------------------- DATA -------------------
        self.initialise()

    # =========================================================
    # UI
    # =========================================================

    def build_widgets(self):

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Container principal
        self.main_container = ttk.Frame(self, padding=10)
        self.main_container.grid(row=0, column=0, sticky="nsew")

        self.main_container.rowconfigure(0, weight=1)
        self.main_container.columnconfigure(0, weight=1)

        # =====================================================
        # PANED WINDOW PRINCIPAL
        # =====================================================

        self.main_pane = ttk.PanedWindow(
            self.main_container,
            orient="horizontal"
        )
        self.main_pane.grid(row=0, column=0, sticky="nsew")

        # Construction des panneaux
        self._build_category_panel()
        self._build_operation_panel()

        # Ajout au paned
        self.main_pane.add(self.category_panel, weight=1)
        self.main_pane.add(self.operation_panel, weight=2)

    # =========================================================
    # CATEGORY PANEL
    # =========================================================

    def _build_category_panel(self):

        self.category_panel = ttk.Frame(self.main_pane, padding=5)

        self.category_panel.rowconfigure(0, weight=1)
        self.category_panel.rowconfigure(1, weight=0)

        self.category_panel.columnconfigure(0, weight=1)

        # ------------------- TREE -------------------

        self.category_tree = CategoryTree(
            self.category_panel,
            callbacks=self.callbacks
        )
        self.category_tree.grid(row=0, column=0, **GRID)

        # ------------------- ACTIONS -------------------

        self.category_actions = EditorButton(
            self.category_panel,
            callbacks=self.callbacks
        )
        self.category_actions.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(5, 0)
        )

    # =========================================================
    # OPERATION PANEL
    # =========================================================

    def _build_operation_panel(self):

        self.operation_panel = ttk.Frame(self.main_pane, padding=5)

        self.operation_panel.rowconfigure(0, weight=2)
        self.operation_panel.rowconfigure(1, weight=3)

        self.operation_panel.columnconfigure(0, weight=1)

        # ------------------- GRAPH / STATS -------------------

        self.operations_graph = TabsGrafBaton(self.operation_panel, title="Activite du tiers")
        self.operations_graph.grid(row=0, column=0, **GRID)

        # Placeholder
        ttk.Label(
            self.operations_graph,
            text="Graphiques / statistiques"
        ).pack(expand=True)

        # ------------------- OPERATIONS TREE -------------------

        self.operation_tree = OperationTree(
            self.operation_panel,
            callbacks=self.callbacks
        )
        self.operation_tree.grid(row=1, column=0, **GRID)

    # =========================================================
    # CALLBACKS
    # =========================================================

    def _build_callbacks(self):

        return {
            "on_category_selected": self.on_select_category,
            "refresh_categories": self.refresh_tree,
            "action_add_category": self.action_add_category_tree,
            "action_edit_category": self.action_add_category_tree,
            "action_delete_category": self.action_delete_category,
            "action_fusionner_category": self._action_fusionner_category,
        }

    # =========================================================
    # EVENTS
    # =========================================================

    def on_select_category(self, row):
        print(f"Catégorie sélectionnée : {row}")
        selected_id = row.get("id") or row.get("id_armoire") or row.get("id_classeur") or row.get("iid_key")
        print(f"category_id : {selected_id}")
        self.operation_tree.insert_rows(self.helper.fetch_row_operations(selected_id))
        self.operations_graph.set_points(self._operation_points(selected_id))

    def action_add_category_tree(self):
        print(f'[DEBUG]CategoriesViewEditor:action_add_category_tree')
        data = self.category_tree._get_selected()
        selected_key = data["iid_key"] if data else None
        editor_modal = CategorieEditor(
            self,
            self.services,
            selected_key=selected_key,
            on_save_callback=lambda: self.refresh_tree()
        )
        editor_modal.protocol("WM_DELETE_WINDOW", lambda: self._close_category_editor(editor_modal))

    def _close_category_editor(self, editor):
        editor.destroy()
        self.refresh_tree()

    def action_delete_category(self):
        data = self.category_tree._get_selected()
        if not data:
            return
        selected_id = data.get("id_armoire") or data.get("id_classeur") or data.get("id") or data.get("iid_key")
        if isinstance(selected_id, str) and "_" in selected_id:
            selected_id = selected_id.split("_", 1)[1]
        obj = self.helper.cat_trackers.get_by_id(selected_id)
        if obj and self.helper.cat_trackers.delete(obj):
            self.refresh_tree()

    def _action_fusionner_category(self):
        print(f'[DEBUG]CategoriesViewEditor:_action_fusionner_category')
        data_list = self.category_tree._get_all_selected()
        print(f'[DEBUG]Selected categories: {data_list}')
        if len(data_list) < 2:
            print("[Avertissement] Il faut au moins 2 tiers pour fusionner.")
            return

            # Appel du nouveau module
        from interfaces_mod.mod_categorie_fusion import CategorieFusionEditor
        editor = CategorieFusionEditor(self, services=self.services, selected_categories=data_list)
        self.wait_window(editor)
        self._close_fusion_editor(editor)

    # =========================================================
    # DATA
    # =========================================================

    def initialise(self):

        self.refresh_tree()

    def refresh_tree(self):

        rows = self.helper.fetch_row_complet()

        self.category_tree.insert_rows(rows)

    def _close_fusion_editor(self, editor):
        """Rafraîchit l'interface principale après la fusion."""
        editor.destroy()
        # On réinitialise les helpers pour vider les caches (Tiers + Operations)
        self.helper.initialise()
        # On vide la sélection courante car les anciens IDs sont supprimés
        self.selected_compte_id = None
        # On rafraîchit tout
        self.refresh_tree()

    def _operation_points(self,selected_id):
        """
        Retourne une liste de tuples (mois "MM/YY", depenses, revenus)
        pour TabsGrafBaton. Les dépenses sont en valeur absolue (>= 0).
        """
        if not selected_id:
            return []

        rows = self.helper.fetch_row_operations(selected_id)

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


# =============================================================
# TEST
# =============================================================

if __name__ == '__main__':
    from _services._bootstrap_services import build_app_services

    root = tk.Tk()
    root.title("Gestion Catégories Dépenses")

    services = build_app_services()

    app = CategoriesViewEditor(root, services)
    app.pack(fill='both', expand=True)

    root.geometry("1200x700")

    root.mainloop()
