import tkinter as tk
from tkinter import ttk

from _helpers.mode_de_paiement_editor_helpers import ModeDePaiementEditorHelpers
from interfaces_mod.mod_mode_paiement_editor import ModePaiementEditor
from interfaces_tabs.tabs_mode_paiement_editor_button import ModePaiementEditorButton
from interfaces_tabs.tabs_mode_paiement_editor_tree import ModePaiementTree


GRID = dict(sticky="nsew", padx=2, pady=2)


class ModePaiementViewEditor(tk.Frame):
    """
    Vue principale :
        - Gestion des modes de paiement
        - Affichage des opérations affectées
    """

    def __init__(self, parent, services):
        super().__init__(parent)
        fenetre_principale = parent.winfo_toplevel()
        fenetre_principale.title("Éditeur de Modes de Paiement - Gestion Financière")

        self.services = services
        self.helper = ModeDePaiementEditorHelpers(services)
        self.selected_mode_id = None

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
        self._build_mode_panel()

        # Ajout au paned
        self.main_pane.add(self.mode_panel, weight=1)

    # =========================================================
    # MODE PANEL
    # =========================================================

    def _build_mode_panel(self):

        self.mode_panel = ttk.Frame(self.main_pane, padding=5)

        self.mode_panel.rowconfigure(0, weight=1)
        self.mode_panel.rowconfigure(1, weight=0)

        self.mode_panel.columnconfigure(0, weight=1)

        # ------------------- TREE -------------------

        self.mode_tree = ModePaiementTree(
            self.mode_panel,
            callbacks=self.callbacks
        )
        self.mode_tree.grid(row=0, column=0, **GRID)

        # ------------------- ACTIONS -------------------

        self.mode_actions = ModePaiementEditorButton(
            self.mode_panel,
            callbacks=self.callbacks
        )
        self.mode_actions.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(5, 0)
        )

    # =========================================================
    # CALLBACKS
    # =========================================================

    def _build_callbacks(self):

        return {
            "on_mode_paiement_selected": self.on_select_mode,
            "refresh_modes": self.refresh_tree,
            "action_add_mode_paiement": self.action_add_mode,
            "action_delete_mode_paiement": self.action_delete_mode,
        }

    # =========================================================
    # EVENTS
    # =========================================================

    def on_select_mode(self, row):
        print(f"Mode de paiement sélectionné : {row}")
        self.selected_mode_id = row.get("id_mode_paiement") if row else None

    def action_add_mode(self):
        print(f'[DEBUG]ModePaiementViewEditor:action_add_mode')
        editor_modal = ModePaiementEditor(
            self,
            self.services,
        )
        editor_modal.protocol("WM_DELETE_WINDOW", lambda: self._close_mode_editor(editor_modal))

    def _close_mode_editor(self, editor):
        editor.destroy()
        self.refresh_tree()

    def action_delete_mode(self):
        data = self.mode_tree._get_selected()
        if not data:
            return
        selected_id = data.get("id_mode_paiement")
        if not selected_id:
            return
        
        obj = self.helper.mode_trackers.get_by_id(selected_id)
        if obj and self.helper.mode_trackers.delete(obj):
            self.refresh_tree()

    # =========================================================
    # DATA
    # =========================================================

    def initialise(self):
        self.refresh_tree()

    def refresh_tree(self):
        rows = self.helper.fetch_row_complet()
        self.mode_tree.insert_rows(rows)


# =============================================================
# TEST
# =============================================================

if __name__ == '__main__':
    from _services._bootstrap_services import build_app_services

    root = tk.Tk()
    root.title("Gestion Modes de Paiement")

    services = build_app_services()

    app = ModePaiementViewEditor(root, services)
    app.pack(fill='both', expand=True)

    root.geometry("800x600")

    root.mainloop()
