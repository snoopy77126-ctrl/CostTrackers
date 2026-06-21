import tkinter as tk
from tkinter import ttk

from _helpers.categorie_editor_helpers import CategorieEditorHelpers
from interfaces_mod.mod_categorie_editor import CategorieEditor
from interfaces_tabs.tabs_categorie_editor_button import EditorButton
from interfaces_tabs.tabs_categorie_editor_tree import CategoryTree
from interfaces_tabs.tabs_operation_view_tree import OperationTree

GRID = dict(sticky="nsew", padx=2, pady=2)


class CategoriesDepensesView(tk.Frame):
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
        self.callbacks = self.menu_callbacks()

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

        self.operations_graph = ttk.LabelFrame(
            self.operation_panel,
            text="Visualisation des dépenses"
        )
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

    def menu_callbacks(self):

        return {
            "on_category_selected": self.on_select_category,
            "refresh_categories": self.refresh_category_tree,
            "action_add_category": self.action_add_category_tree,
            "action_edit_category": self.action_add_category_tree,
            "action_delete_category": self.action_delete_category,
        }

    # =========================================================
    # EVENTS
    # =========================================================

    def on_select_category(self, row):

        category_id = row.get("id") or row.get("id_armoire") or row.get("id_classeur") or row.get("iid_key")
        print(f"Catégorie sélectionnée : {category_id}")

        # TODO :
        # - charger les opérations liées
        # - mettre à jour les stats
        # - refresh graphique

    def action_add_category_tree(self):
        data = self.category_tree._get_selected()
        selected_key = data["iid_key"] if data else None
        editor_modal = CategorieEditor(
            self,
            self.services,
            selected_key=selected_key,
            on_save_callback=lambda: self.refresh_category_tree()
        )
        editor_modal.protocol("WM_DELETE_WINDOW", lambda: self._close_category_editor(editor_modal))

    def _close_category_editor(self, editor):
        editor.destroy()
        self.refresh_category_tree()

    def action_delete_category(self):
        data = self.category_tree._get_selected()
        if not data:
            return
        selected_id = data.get("id_armoire") or data.get("id_classeur") or data.get("id") or data.get("iid_key")
        if isinstance(selected_id, str) and "_" in selected_id:
            selected_id = selected_id.split("_", 1)[1]
        obj = self.helper.tracker.get_by_id(selected_id)
        if obj and self.helper.tracker.delete(obj):
            self.refresh_category_tree()

    # =========================================================
    # DATA
    # =========================================================

    def initialise(self):

        self.refresh_category_tree()

    def refresh_category_tree(self):

        rows = self.helper.fetch_row_complet()

        self.category_tree.insert_rows(rows)


# =============================================================
# TEST
# =============================================================

if __name__ == '__main__':
    from _services._bootstrap_services import build_app_services

    root = tk.Tk()
    root.title("Gestion Catégories Dépenses")

    services = build_app_services()

    app = CategoriesDepensesView(root, services)
    app.pack(fill='both', expand=True)

    root.geometry("1200x700")

    root.mainloop()
