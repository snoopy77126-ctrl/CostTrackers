import tkinter as tk
from tkinter import ttk

from _helpers.categorie_editor_helpers import CategorieEditorHelpers
from interfaces_tabs.tabs_categorie_editor_button import EditorButton2
from interfaces_tabs.tabs_categorie_editor_data import CategorieData
from interfaces_tabs.tabs_categorie_editor_tree import CategoryTree


class CategorieEditor(tk.Toplevel):
    def __init__(self, parent, services=None, **context):
        super().__init__(parent)
        self.services = services
        self.selected_key = context.get("selected_key")
        self.on_save_callback = context.get("on_save_callback")

        # 1. Initialisation (Logique métier)
        self.helpers = CategorieEditorHelpers(services)
        self.callbacks = self.menu_callbacks()

        # 2. Construction de l'interface segmentée
        self.transient(parent)  # Liée au parent
        self.grab_set()  # Bloque les clics sur la fenêtre principale
        self.title("Éditeur de categories")
        self.transient(parent)  # Réduit avec la fenêtre parente
        self.grab_set()  # Capture tous les événements (bloque le parent)

        # 3. Chargement initial
        self.build_widgets()
        self.initialise()
        if self.selected_key:
            data = self.helpers.fetch_data_by_iid(self.selected_key)
            if data:
                self.classeur_panel.set_values(data)

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
        self._build_right_frame()

    def _build_right_frame(self):
        """Zone droite : Liste des fichiers et boutons d'action."""
        self.right_frame = ttk.Frame(self.container, padding=5)
        self.right_frame.grid(row=0, column=1, sticky="nsew")

        # CONFIG GRID
        self.right_frame.rowconfigure(0, weight=0)  # CategorieData
        self.right_frame.rowconfigure(1, weight=0)  # Buttons
        self.right_frame.rowconfigure(2, weight=1)  # futur contenu (tree fichiers)
        self.right_frame.columnconfigure(0, weight=1)

        # 1. Panel CategorieData
        self.classeur_panel = CategorieData(self.right_frame)
        self.classeur_panel.grid(row=0, column=0, sticky="ew", pady=5)

        # 2. Barre de boutons
        self.button_panel = EditorButton2(self.right_frame, callbacks=self.callbacks)
        self.button_panel.grid(row=1, column=0, sticky="ew", pady=5)

    # ------------------- Callbacks -------------------
    def menu_callbacks(self):
        return {
            "action_add_category": self._action_add_file,
            "action_edit_category": self._action_edit_file,
            "action_delete_category": self._action_delete_file,
            "action_save_category": self._action_save_category,
            "on_category_selected": self._on_category_selected,
        }

    # ------------------- Callbacks Catégories -------------------
    def _on_category_selected(self, row):
        # L'UI extrait l'ID
        cat_id = row.get("iid_key")
        # L'UI demande les données formatées au Helper
        data = self.helpers.fetch_data_by_iid(cat_id)

        # L'UI applique les données au formulaire
        if data:
            self.classeur_panel.set_values(data)

    def _on_category_opened(self, event):
        print("[TreeClick]on_double_click")

    def _on_right_click_category(self, event):
        print("[TreeClick]on_right_click")

    def _action_add_file(self, event=None):
        self.classeur_panel._clear()
        self.helpers.categorie_current = None

    def _action_edit_file(self, event=None):
        print("[BOUTTON] Modifier un fichier")

    def _action_delete_file(self, event=None):
        obj = self.helpers.categorie_current
        if obj and self.helpers.cat_trackers.delete(obj):
            self.initialise()
            self.classeur_panel._clear()
            self.helpers.categorie_current = None

    def _action_save_category(self):
        """Action déclenchée par le bouton Sauvegarder."""
        print('[DEBUG]_action_save_category: click')
        data = self.classeur_panel.get_values()
        # Demander au helper de sauvegarder
        success = self.helpers.save_category(data)

        if success:
            print("Sauvegarde réussie !")
            # 4. Rafraîchir l'arbre pour voir les changements
            self.initialise()
            # 5. Optionnel : Clear le formulaire
            self.classeur_panel._clear()
            self.helpers.categorie_current = None
            if self.on_save_callback:
                self.on_save_callback()
        else:
            print("Erreur lors de la sauvegarde")

    def _on_armoire_selected(self, row):
        if row:
            print(f"ID sélectionné : {row['key']}")
            print(f"Libellé sélectionné : {row['value']}")

    # ------------------- Logique de Données -------------------
    def initialise(self):
        """Chargement initial au lancement du formulaire."""
        self.helpers.initialise()
        self._add_categorie_combobox()

    def _add_categorie_combobox(self):
        """Remplis la combo catégorie"""
        rows = self.helpers.fetch_row_categorie()
        print(f'[DEBUG]CategorieEditor:_add_categorie_combobox')
        print(f'[DEBUG]rows= {rows}')
        self.classeur_panel.set_values({"categorie": rows})


# ------------------ Main test ------------------
if __name__ == '__main__':
    from _services._bootstrap_services import build_app_services

    root = tk.Tk()
    root.title("Test Editor")
    services = build_app_services()

    app = CategorieEditor(root, services=services)

    # Force la fermeture de root quand on ferme la fenêtre CategorieEditor
    app.protocol("WM_DELETE_WINDOW", root.destroy)

    # Optionnel : Ajuste la taille pour que root ne soit pas un
    # tout petit carré vide visible derrière l'éditeur
    root.geometry(f'10x10+{0}+{0}')

    root.mainloop()

