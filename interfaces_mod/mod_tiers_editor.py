import tkinter as tk
from tkinter import ttk

from _helpers.tiers_editor_helpers import TiersEditorHelpers
from interfaces_tabs.tabs_tiers_editor_button import EditorButton
from interfaces_tabs.tabs_tiers_editor_data import EmetteurData
from interfaces_tabs.tabs_tiers_editor_tree import EmetteurTree


class EmetteurEditor(tk.Toplevel):
    def __init__(self, parent, services=None):
        super().__init__(parent)

        # Construction de l'interface segmentée
        self.transient(parent)  # Liée au parent
        self.grab_set()  # Bloque les clics sur la fenêtre principale
        self.title("Carnet d'Adresses Émetteurs")

        # Initialisation (Logique métier)
        self.services = services
        self.helpers = TiersEditorHelpers(services)
        self.callbacks = self._build_callbacks()


        # Chargement initial
        self.build_widgets()
        self.initialise()

    def build_widgets(self):
        self.container = ttk.Frame(self, padding=10)
        self.container.pack(fill="both", expand=True)

        # Splitter Gauche/Droite
        self.pw = ttk.PanedWindow(self.container, orient="horizontal")
        self.pw.pack(fill="both", expand=True)

        # GAUCHE : L'arbre des contacts
        self.tree = EmetteurTree(self.pw, callbacks=self.callbacks)
        self.pw.add(self.tree, weight=1)

        # DROITE : Formulaire et Boutons
        self.right_panel = ttk.Frame(self.pw)
        self.pw.add(self.right_panel, weight=2)

        self.form = EmetteurData(self.right_panel)
        self.form.pack(fill="x", pady=5)

        self.buttons = EditorButton(self.right_panel, callbacks=self.callbacks)
        self.buttons.pack(fill="x")

    def _build_callbacks(self):
        return {
            "action_add_emetteur": self._on_add_new,
            "action_delete_emetteur": self._on_delete,
            "action_save_emetteur": self._on_save,
            "on_emetteur_selected": self._on_select,
        }

    def initialise(self):
        """Charge les données et remplit les combos."""
        self.helpers.initialise()
        self.refresh_tree()
        # Remplit la combo des parents avec les entreprises existantes
        parent_selection = self.helpers.fetch_row_organisation()
        self.form.set_values({"parent_selection": parent_selection})

    def refresh_tree(self):
        # Utilise display_name: "CHR LENS (DUPONT Pierre)"
        rows = self.helpers.fetch_tree_grouped()
        self.tree.insert_rows(rows)

    def _on_save(self):
        data = self.form.get_submit_data()
        if self.helpers.save_emetteur(data):
            self.initialise()

    def _on_delete(self):
        data = self.form.get_submit_data()
        if self.helpers.delete_emetteur(data):
            self.initialise()
            self.form._clear()

    def _on_select(self, row):
        if not row:
            return
        full_data = self.helpers.fetch_data_emetteur(row["id"])
        self.form.set_values(full_data)

    def _on_add_new(self):
        self.form._clear()
        self.helpers.current_id = None


# ------------------ Main test ------------------
if __name__ == '__main__':
    from _trackers.tiers_tracker import TiersTracker  # On importe le tiers_trackers

    root = tk.Tk()
    root.title("Test Editor")

    # 1. On crée l'instance du tiers_trackers (le tampon mémoire)
    # C'est lui qui fera le lien avec le Manager et la DB
    emetteur_tracker = TiersTracker()

    # 2. On passe le tiers_trackers à l'éditeur lors de l'initialisation
    app = EmetteurEditor(root)

    # Force la fermeture de root quand on ferme la fenêtre
    app.protocol("WM_DELETE_WINDOW", root.destroy)

    # Ajuste la taille du root pour qu'il soit discret
    root.geometry(f'10x10+{0}+{0}')

    root.mainloop()

