import tkinter as tk
from tkinter import ttk

from interfaces_mod.mod_tiers_editor import TiersEditorHelpers
from interfaces_tabs._tabs_graf import TabsGraf
from interfaces_tabs.tabs_operation_view_tree import OperationTree
from interfaces_tabs.tabs_tiers_editor_button import EditorButton
from interfaces_tabs.tabs_tiers_editor_tree import EmetteurTree


class TiersEditor(tk.Frame):
    def __init__(self, parent, services):
        super().__init__(parent)
        fenetre_principale = parent.winfo_toplevel()
        fenetre_principale.title("TiersEditor - Gestion Financière")

        self.services = services
        self.tiers_helpers = TiersEditorHelpers(services)
        self.selected_tiers_id = None

        # 1. Initialisation (Logique métier)
        self.callbacks = self._build_callbacks()

        # 2. Construction de l'interface segmentée
        self.build_widgets()

        # 3. Chargement initial des données
        self.initialise()

    # ------------------- Construction UI -------------------
    def build_widgets(self):
        """Orchestrateur principal de la vue."""
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Container principal pour gérer les espacements
        self.container = ttk.Frame(self, padding=10)
        self.container.grid(row=0, column=0, sticky="nsew")

        # Configuration du Grid : Gauche (1/3) et Droite (2/3)
        self.container.rowconfigure(0, weight=1)
        self.container.columnconfigure(0, weight=1)  # Pour la zone Catégories
        self.container.columnconfigure(1, weight=2)  # Pour la zone Fichiers

        # Appels des méthodes de construction segmentées
        self._build_left_frame()
        self._build_right_frame()

    def _build_left_frame(self):
        """Zone gauche : Bouton Action."""
        self.left_frame = ttk.Frame(self.container, padding=5)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.left_frame.rowconfigure(0, weight=1)
        self.left_frame.rowconfigure(1, weight=0)
        self.left_frame.columnconfigure(0, weight=1)

        self.tiers_tree = EmetteurTree(self.left_frame, callbacks=self.callbacks)
        self.tiers_tree.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        self.button_panel_tiers = EditorButton(self.left_frame, callbacks=self.callbacks)
        self.button_panel_tiers.grid(row=1, column=0, sticky="ew", pady=5)

    def _build_right_frame(self):
        """Zone droite : Liste, graph et boutons d'action."""
        self.right_frame = ttk.Frame(self.container, padding=5)
        self.right_frame.grid(row=0, column=1, sticky="nsew")

        # Configuration des poids pour que les arbres s'étendent
        self.right_frame.rowconfigure(0, weight=1)  # Espace pour les Treeviews
        self.right_frame.rowconfigure(1, weight=0)  # Espace pour les boutons
        self.right_frame.columnconfigure(0, weight=1)  # Colonne Tiers
        self.right_frame.columnconfigure(1, weight=1)  # Colonne Opérations

        self.graph_view = TabsGraf(self.right_frame, title="Activite du tiers")
        self.graph_view.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)

        self.ops_tree = OperationTree(self.right_frame, callbacks=self.callbacks)
        self.ops_tree.grid(row=1, column=1, sticky="nsew", padx=2, pady=2)

    # ------------------- Callbacks -------------------
    def _build_callbacks(self):
        return {
            "on_emetteur_selected": self._on_tiers_selected,
            "action_add": self._open_tiers_editor,
            "action_edit": self._open_tiers_editor,
            "action_delete": self._open_tiers_editor,
            "action_view_categorie": self._open_categories_editor,
            "action_fusionner": self._action_fusionner,
        }

    # ------------------- Logique de Données -------------------
    def initialise(self):
        """Chargement initial au lancement du formulaire."""
        self.tiers_helpers.initialise()
        self.refresh()

    def refresh(self):
        self.tiers_tree.insert_rows(self.tiers_helpers.fetch_row_emetteur())
        self.ops_tree.insert_rows(self.tiers_helpers.fetch_row_operations(self.selected_tiers_id))
        self.graph_view.set_points(self._operation_points())

    def _on_tiers_selected(self, row):
        self.selected_tiers_id = row.get("id") if row else None
        self.ops_tree.insert_rows(self.tiers_helpers.fetch_row_operations(self.selected_tiers_id))
        self.graph_view.set_points(self._operation_points())

    def _open_tiers_editor(self):
        editor = TiersEditorHelpers(self, services=self.services)
        editor.protocol("WM_DELETE_WINDOW", lambda: self._close_editor(editor))

    def _close_editor(self, editor):
        editor.destroy()
        self.tiers_helpers.initialise()
        self.refresh()

    def _open_categories_editor(self):
        from interfaces_mod.mod_categorie_editor import CategorieEditor
        editor = CategorieEditor(self, services=self.services)
        editor.protocol("WM_DELETE_WINDOW", lambda: self._close_editor(editor))

    def _operation_points(self):
        rows = list(reversed(self.tiers_helpers.fetch_row_operations(self.selected_tiers_id)[-30:]))
        total = 0.0
        points = []
        for row in rows:
            total += float(row["objet"].montant or 0)
            points.append((row["date_operation"], total))
        return points

    def _action_fusionner(self):
        print(f'[DEBUG]TierEditor:_action_fusionner')
        data_list = self.tiers_tree._get_all_selected()
        if len(data_list) < 2:
            print("[Avertissement] Il faut au moins 2 tiers pour fusionner.")
            return

            # Appel du nouveau module
        from interfaces_mod.mod_tiers_fusion import TiersFusionEditor
        editor = TiersFusionEditor(self, services=self.services, selected_tiers=data_list)

        # On définit le protocole pour rafraîchir à la fermeture
        editor.protocol("WM_DELETE_WINDOW", lambda: self._close_fusion_editor(editor))

    def _close_fusion_editor(self, editor):
        """Rafraîchit l'interface principale après la fusion."""
        editor.destroy()
        print("[DEBUG] Rafraîchissement de l'interface après fusion.")

        # 1. On réinitialise les helpers pour vider les caches (Tiers + Operations)
        self.tiers_helpers.initialise()

        # 2. On vide la sélection courante car les anciens IDs sont supprimés
        self.selected_tiers_id = None

        # 3. On rafraîchit tout
        self.refresh()


# ------------------ Main test ------------------
if __name__ == '__main__':
    from _services._bootstrap_services import build_app_services

    root = tk.Tk()
    root.title("Test Cat/Tiers")

    services = build_app_services()

    app = TiersEditor(root, services)
    app.pack(fill='both', expand=True)

    root.geometry('900x300')
    root.mainloop()
