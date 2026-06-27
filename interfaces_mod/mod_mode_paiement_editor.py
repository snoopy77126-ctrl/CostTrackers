import tkinter as tk
from tkinter import ttk

from _helpers.mode_de_paiement_editor_helpers import ModeDePaiementEditorHelpers
from interfaces_tabs.tabs_mode_paiement_editor_button import ModePaiementEditorButton
from interfaces_tabs.tabs_mode_paiement_editor_data import ModePaiementData
from interfaces_tabs.tabs_mode_paiement_editor_tree import ModePaiementTree


class ModePaiementEditor(tk.Toplevel):
    def __init__(self, parent, services=None):
        super().__init__(parent)

        # Construction de l'interface segmentée
        self.transient(parent)
        self.grab_set()
        self.title("Éditeur de Modes de Paiement")

        # Initialisation (Logique métier)
        self.services = services
        self.helpers = ModeDePaiementEditorHelpers(services)
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

        # GAUCHE : L'arbre des modes de paiement
        self.tree = ModePaiementTree(self.pw, callbacks=self.callbacks)
        self.pw.add(self.tree, weight=1)

        # DROITE : Formulaire et Boutons
        self.right_panel = ttk.Frame(self.pw)
        self.pw.add(self.right_panel, weight=2)

        self.form = ModePaiementData(self.right_panel)
        self.form.pack(fill="x", pady=5)

        self.buttons = ModePaiementEditorButton(self.right_panel, callbacks=self.callbacks)
        self.buttons.pack(fill="x")

    def _build_callbacks(self):
        return {
            "action_add_mode_paiement": self._on_add_new,
            "action_delete_mode_paiement": self._on_delete,
            "action_save_mode_paiement": self._on_save,
            "on_mode_paiement_selected": self._on_select,
        }

    def initialise(self):
        """Charge les données et remplit les combos."""
        self.helpers.initialise()
        self.refresh_tree()

    def refresh_tree(self):
        rows = self.helpers.fetch_row_complet()
        self.tree.insert_rows(rows)

    def _on_save(self):
        data = self.form.get_submit_data()
        if self.helpers.save_mode_paiement(data):
            self.initialise()

    def _on_delete(self):
        data = self.form.get_submit_data()
        if self.helpers.delete_mode_paiement(data):
            self.initialise()
            self.form._clear()

    def _on_select(self, row):
        if not row:
            return
        full_data = self.helpers.fetch_data_by_iid(row["iid_key"])
        if full_data:
            self.form.set_values(full_data)

    def _on_add_new(self):
        self.form._clear()


# ------------------ Main test ------------------
if __name__ == '__main__':
    from _trackers.mode_de_paiement_tracker import ModeDePaiementTracker

    root = tk.Tk()
    root.title("Test Editor")

    mode_paiement_tracker = ModeDePaiementTracker()

    app = ModePaiementEditor(root)

    app.protocol("WM_DELETE_WINDOW", root.destroy)

    root.geometry(f'10x10+{0}+{0}')

    root.mainloop()
