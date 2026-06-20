import tkinter as tk
from tkinter import ttk

from _helpers.banque_editor_helpers import BanqueEditorHelpers

from interfaces_tabs.tabs_banque_editor_button import BanqueButton
from interfaces_tabs.tabs_banque_editor_data import BanqueData
from interfaces_tabs.tabs_banque_editor_tree import BanqueTree

class BanqueEditor(tk.Toplevel):
    def __init__(self, parent, services=None):
        super().__init__(parent)
        self.services = services

        # 1. Initialisation (Logique métier)
        self.helpers = BanqueEditorHelpers(services)
        self.callbacks = self._build_callbacks()

        # 2. Construction de l'interface segmentée
        self.transient(parent)  # Liée au parent
        self.grab_set()  # Bloque les clics sur la fenêtre principale
        self.title("Liste des Banques")

        # 3. Chargement initial
        self.build_widgets()
        self.initialise()

    def build_widgets(self):
        self.container = ttk.Frame(self, padding=10)
        self.container.pack(fill="both", expand=True)

        # Splitter Gauche/Droite
        self.pw = ttk.PanedWindow(self.container, orient="horizontal")
        self.pw.pack(fill="both", expand=True)

        # GAUCHE : L'arbre des contacts
        self.tree = BanqueTree(self.pw, callbacks=self.callbacks)
        self.pw.add(self.tree, weight=1)

        # DROITE : Formulaire et Boutons
        self.right_panel = ttk.Frame(self.pw)
        self.pw.add(self.right_panel, weight=2)

        self.form = BanqueData(self.right_panel)
        self.form.pack(fill="x", pady=5)

        self.buttons = BanqueButton(self.right_panel, callbacks=self.callbacks)
        self.buttons.pack(fill="x")

    def _build_callbacks(self):
        return {
            "action_add_banque": self._on_add_new,
            "action_delete_banque": self._on_delete,
            "action_save_banque": self._on_save,
            "on_banque_selected": self._on_select,
        }

    def initialise(self):
        """Charge les données et remplit les combos."""
        self.helpers.initialise()
        self.refresh_tree()
        # Remplit la combo des parents avec les entreprises existantes
        parent_selection = self.helpers.fetch_row_organisation()
        self.form.set_values({"parent_selection": parent_selection})

    def refresh_tree(self):
        # 1. On récupère les objets
        banques = self.helpers.fetch_all('banques')

        rows_pour_ui = []
        for banque in banques:
            # 2. On transforme en dictionnaire (via to_dict ou vars)
            data = banque.to_dict() if hasattr(banque, 'to_dict') else vars(banque).copy()

            # 3. LIGNE CRUCIALE : On injecte iid_key
            data["iid_key"] = str(banque.id_banque)

            # Facultatif mais utile pour FlatTree
            data["actif"] = True

            rows_pour_ui.append(data)

        # 4. On envoie au tableau
        self.tree.insert_rows(rows_pour_ui)

    def _on_save(self):
        data = self.form.get_submit_data()
        if self.helpers.save_banque(data):
            self.initialise()

    def _on_delete(self):
        data = self.form.get_submit_data()
        if self.helpers.delete_banque(data):
            self.initialise()
            self.form._clear()

    def _on_select(self, row):
        if not row:
            return
        full_data = self.helpers.fetch_data_banque(row["id"])
        self.form.set_values(full_data)

    def _on_add_new(self):
        self.form._clear()
        self.helpers.current_id = None


# ------------------ Main test ------------------
if __name__ == '__main__':
    from _trackers.banque_trackers import BanqueTracker

    root = tk.Tk()
    root.title("Test Editor")

    # 1. On crée l'instance du tiers_trackers (le tampon mémoire)
    banque_tracker = BanqueTracker()

    # 2. On prépare le dictionnaire de services
    mes_services = {
        'banques': banque_tracker
    }

    # 3. On passe le dictionnaire 'services' à l'éditeur
    app = BanqueEditor(root, services=mes_services)

    # Force la fermeture de root quand on ferme la fenêtre
    app.protocol("WM_DELETE_WINDOW", root.destroy)

    # Ajuste la taille du root pour qu'il soit discret
    root.geometry(f'10x10+{0}+{0}')

    root.mainloop()

