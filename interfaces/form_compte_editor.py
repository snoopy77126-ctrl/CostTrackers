import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from _helpers.comptes_editor_helpers import CompteEditorHelpers
from interfaces_mod.mod_banque_editor import BanqueEditor
from interfaces_tabs.tabs_compte_editor_button import BanqueEditorButton, PaiementEditorButton
from interfaces_tabs.tabs_compte_editor_data import BanqueoptionData, BanquesoldeData, CompteGeneralData, CompteFiltreData
from interfaces_tabs.tabs_compte_editor_tree import BanqueEditorTree, MoyenPaiementTree
from interfaces_tabs.tabs_chequier_editor_data import ChequierEditorData
from interfaces_tabs.tabs_chequier_editor_button import ChequierEditorButtons

GRID = dict(sticky="nsew", padx=2, pady=2)

class CompteEditorview(tk.Frame):
    def __init__(self, parent, services=None, **context):
        super().__init__(parent)

        fenetre_principale = parent.winfo_toplevel()
        fenetre_principale.title("CompteEditorview - Gestion Financière")

        self.services = services
        self.helpers = CompteEditorHelpers(self.services)

        self.callbacks = self._build_callbacks()

        self.build_widgets()
        self.initialise()

    def build_widgets(self):
        self.container = ttk.Frame(self, padding=10)
        self.container.grid(row=0, column=0, sticky="nsew")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.container.columnconfigure(0, weight=0)
        self.container.columnconfigure(1, weight=2)
        self.container.rowconfigure(0, weight=1)

        self._build_left_frame().grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self._build_right_frame().grid(row=0, column=1, sticky="nsew", padx=(5, 0))

    def _build_left_frame(self) -> ttk.Frame:
        left_frame = ttk.Frame(self.container)
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)

        # L'arbre affiche la liste des Comptes et reçoit le dictionnaire de callbacks actif
        self.tree_compte = BanqueEditorTree(left_frame, callbacks=self.callbacks)
        self.tree_compte.grid(row=0, column=0, sticky="nsew")
        self.data_filtre_frame = CompteFiltreData(left_frame, callbacks=self.callbacks)
        self.data_filtre_frame.grid(row=1, column=0, sticky="nsew")
        return left_frame

    def _build_right_frame(self) -> ttk.Frame:
        right_frame = ttk.Frame(self.container)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=0)

        self.notebook = ttk.Notebook(right_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        self.general_data_frame = CompteGeneralData(self.notebook)
        self.notebook.add(self.general_data_frame, text="Général (Compte)")

        self.solde_data_frame = BanquesoldeData(self.notebook)
        self.notebook.add(self.solde_data_frame, text="Soldes")

        self.moyen_paiement_frame = self._build_moyen_paiement_panel(self.notebook)
        self.notebook.add(self.moyen_paiement_frame, text="Moyen de paiement")

        self.option_chequier_frame = self._build_chequier_panel(self.notebook)
        self.notebook.add(self.option_chequier_frame, text="Chéquiers")

        self.option_data_frame = BanqueoptionData(self.notebook)
        self.notebook.add(self.option_data_frame, text="Options")

        self.button_frame = BanqueEditorButton(right_frame, callbacks=self.callbacks)
        self.button_frame.grid(row=1, column=0, sticky="ew")
        return right_frame

    def _build_moyen_paiement_panel(self, parent):
        """Construit le contenu de l'onglet Moyen de paiement."""
        container = ttk.Frame(parent, padding=5)
        container.columnconfigure(1, weight=1)

        # PanedWindow pour diviser l'espace
        self.main_pane = ttk.PanedWindow(container, orient="horizontal")
        self.main_pane.grid(row=0, column=0, sticky="nsew")

        # Création du panneau où iront les widgets
        self.moyen_paiement_panel = ttk.Frame(self.main_pane)
        self.main_pane.add(self.moyen_paiement_panel)

        # Construction des widgets dans le panneau
        self.paiement_source_tree = MoyenPaiementTree(
            self.moyen_paiement_panel,
            callbacks=self.callbacks
        )
        self.paiement_source_tree.grid(row=0, column=0, **GRID)

        self.moyen_paiement_button = PaiementEditorButton(
            self.moyen_paiement_panel,
            callbacks=self.callbacks
        )
        self.moyen_paiement_button.grid(row=0, column=1, **GRID)

        # Construction des widgets dans le panneau
        self.paiement_select_tree = MoyenPaiementTree(
            self.moyen_paiement_panel,
            callbacks=self.callbacks
        )
        self.paiement_select_tree.grid(row=0, column=2, **GRID)

        return container

    def _build_chequier_panel(self, parent):
        """Construit le contenu de l'onglet Chequiers."""
        container = ttk.Frame(parent, padding=5)

        # Ajout d'un canvas si vous avez beaucoup de chéquiers pour permettre le scroll
        self.chk_container = ttk.Frame(container)
        self.chk_container.pack(fill="both", expand=True)

        self._refresh_chequiers_content()
        # Ligne de boutons associés
        chk_buttons = ChequierEditorButtons(self.chk_container, callbacks=self.callbacks)
        chk_buttons.grid(sticky="e", pady=2)
        return container

    # ---- Centralisation des appels conforme à vos autres formulaires ----
    def _build_callbacks(self):
        """Aiguille l'action demandée par les boutons vers la bonne méthode interne."""
        return {
            "on_compte_selected": self.on_compte_selected,
            "action_new_account": self.action_new,
            "action_save_account": self.action_save,
            "action_delete_account": self.action_delete,
            "add_new_banque": self.add_new_banque,
            "action_fusionner": self._action_fusionner,
            "action_select": self._action_paiement_select,
            "action_unselect": self._action_paiement_unselect,
            "action_select_all": self._action_paiement_select_all,
            "action_unselect_all": self._action_paiement_unselect_all,
            "_on_compte_filtre_change": self._on_compte_filtre_change,
        }

    # ---- Actions Métier ----
    def _action_paiement_select(self):
        """▶ Déplace la sélection du tree source vers le tree affecté."""
        rows = self.paiement_source_tree._get_all_selected()
        if not rows:
            return
        if self.helpers.action_select(rows):
            self._refresh_paiement_trees()

    def _action_paiement_unselect(self):
        """◀ Retire la sélection du tree affecté."""
        rows = self.paiement_select_tree._get_all_selected()
        if not rows:
            return
        if self.helpers.action_unselect(rows):
            self._refresh_paiement_trees()

    def _action_paiement_select_all(self):
        """⏭ Affecte tous les modes de paiement au compte courant."""
        if self.helpers.action_select_all():
            self._refresh_paiement_trees()

    def _action_paiement_unselect_all(self):
        """⏮ Retire tous les modes de paiement du compte courant."""
        if self.helpers.action_unselect_all():
            self._refresh_paiement_trees()

    def _refresh_paiement_trees(self):
        """Rafraîchit les deux trees après modification des liaisons."""
        compte_id = self.helpers._current_compte_id()
        source_rows = self.helpers.fetch_row_source_paiement()
        affected_rows = self.helpers.fetch_row_affected_paiement(compte_id)
        self.paiement_source_tree.insert_rows(source_rows)
        self.paiement_select_tree.insert_rows(affected_rows)

    def add_new_banque(self):
        """ Action par défaut new banque clic. """
        editor_modal = BanqueEditor(
            self,
            self.services
        )

        # 2. On attend que la fenêtre soit détruite
        self.wait_window(editor_modal)

        # 3. Une fois fermée, on rafraîchit l'arbre des fichiers

    def action_save(self):
        data = {}

        data.update(self.general_data_frame.get_values())
        data.update(self.solde_data_frame.get_values())
        data.update(self.option_data_frame.get_values())

        if self.helpers.save_compte(data):
            messagebox.showinfo("Compte", "Compte sauvegardé avec succès.")
            self.refresh_compte_tree()
        else:
            messagebox.showwarning("Compte", "Échec de la sauvegarde.")

    def action_new(self):
        self.helpers.new_compte()

        # Utilisez une méthode reset dédiée au lieu de _clear()
        # qui ne vide pas le contexte des dictionnaires internes
        for frame in [self.general_data_frame, self.solde_data_frame, self.option_data_frame]:
            if hasattr(frame, 'reset_form'):
                frame.reset_form()
            else:
                frame._clear()

        # IMPORTANT : Forcez la suppression de l'ID en cours pour éviter
        # que le prochain enregistrement ne fasse un UPDATE au lieu d'un INSERT
        self.current_key = None

    def action_delete(self):
        if not self.helpers.current_compte:
            messagebox.showwarning("Compte", "Aucun compte sélectionné.")
            return
        if not messagebox.askyesno("Compte", "Supprimer ce compte ?"):
            return
        if self.helpers.delete_compte():
            messagebox.showinfo("Compte", "Compte supprimé.")
            self.action_new()
            self.refresh_compte_tree()

    def _action_fusionner(self):
        data_list = self.tree_compte._get_all_selected()
        if len(data_list) < 2:
            print("[Avertissement] Il faut au moins 2 tiers pour fusionner.")
            return

            # Appel du nouveau module
        from interfaces_mod.mod_comptes_fusion import CompteFusionEditor
        editor = CompteFusionEditor(self, services=self.services, selected_compte=data_list)
        self.wait_window(editor)
        self._close_fusion_editor(editor)

    def _close_fusion_editor(self, editor):
        """Rafraîchit l'interface principale après la fusion."""
        editor.destroy()
        # On réinitialise les helpers pour vider les caches (Tiers + Operations)
        self.helpers.initialise()
        # On vide la sélection courante car les anciens IDs sont supprimés
        self.selected_compte_id = None
        # On rafraîchit tout
        self.refresh_compte_tree()

    # ---- Événements de l'Arbre ----
    def on_compte_selected(self, row):
        if not row: return

        compte_id = row.get("id") or row.get("iid_key")

        # 1. Récupération des données
        data = self.helpers.fetch_data_compte(compte_id)
        if not data: return

        # 2. Mise à jour des onglets (on envoie le dictionnaire complet,
        # chaque frame filtre ce dont il a besoin)
        self.general_data_frame.set_values(data)
        self.solde_data_frame.set_values(data)
        self.option_data_frame.set_values(data)

        # 3. Mise à jour des moyens de paiement
        paiement = self.helpers.fetch_row_affected_paiement(compte_id)
        self.paiement_select_tree.insert_rows(paiement)
        # S'assurer que le tree source est aussi à jour
        self.paiement_source_tree.insert_rows(self.helpers.fetch_row_source_paiement())

    def _on_compte_filtre_change(self):
        pass

    # ---- Initialisation & Synchronisation ----
    def initialise(self):
        self.helpers.initialise()

        # Chargement des banques disponibles dans la Combobox du formulaire de compte
        liste_banques = self.helpers.fetch_liste_banques()
        liste_type_compte = self.helpers.fetch_liste_type_compte()
        # Injection des listes de clés dans les onglets de données
        if hasattr(self.general_data_frame, 'set_values'):
            self.general_data_frame.set_values({
                "banque": liste_banques,
                "type_compte": liste_type_compte
            })

        self.refresh_compte_tree()
        self.refresh_moyen_paiement_tree()

    def refresh_compte_tree(self):
        rows = self.helpers.fetch_row_compte()
        self.tree_compte.insert_rows(rows)

    def _refresh_chequiers_content(self):
        """Méthode pour peupler dynamiquement les lignes."""
        # 1. Nettoyage
        for child in self.chk_container.winfo_children():
            child.destroy()

        # 2. Simulation de données (à remplacer par self.helpers.fetch_chequiers())
        chequiers_liste = self.helpers.fetch_chequiers() or [{}]

        # 3. Création des lignes
        for i, data in enumerate(chequiers_liste):
            # Ligne de données
            chk_widget = ChequierEditorData(self.chk_container, callbacks=self.callbacks)
            chk_widget.grid(row=i, column=0, sticky="ew", pady=2)
            chk_widget.set_values(data)  # Utilise la méthode de BaseFormFrame

    def refresh_moyen_paiement_tree(self, row=None):
        # Gestion sécurisée de l'ID
        compte_id = row.get("id") if isinstance(row, dict) else None

        source_rows = self.helpers.fetch_row_source_paiement()
        self.paiement_source_tree.insert_rows(source_rows)

        # Correction : utilisation de isinstance
        if isinstance(compte_id, int):
            affected_rows = self.helpers.fetch_row_affected_paiement(compte_id)
            self.paiement_select_tree.insert_rows(affected_rows)
        else:
            self.paiement_select_tree.clear()

# ==========================================================================
# TEST AUTONOME
# ==========================================================================

if __name__ == '__main__':
    from _services._bootstrap_services import build_app_services

    root = tk.Tk()
    root.title("Test Editor")

    all_services = build_app_services()

    app = CompteEditorview(
        parent=root,
        services=all_services,
        selected_key=3
    )

    app.pack(fill="both", expand=True)
    root.geometry('800x300')
    root.mainloop()
