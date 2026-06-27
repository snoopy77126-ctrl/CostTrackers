import tkinter as tk

from _helpers.operation_view_helpers import OperationsViewHelpers
from interfaces_tabs.tabs_operation_saisie_button import OperationTypeButton, EditorButton
from interfaces_tabs.tabs_operation_saisie_data import OperationSaisieData


class ModOperationSaisie(tk.Toplevel):
    def __init__(self, parent, services=None, **context):
        super().__init__(parent)
        self.resizable(True, True)
        self.services = services
        self.selected_key = context.get("selected_key")

        # 1. Initialisation (Logique métier & Variables Tkinter de contrôle)
        self.helpers = OperationsViewHelpers(services)
        self.callbacks = self.menu_callbacks()
        self.on_save_callback = context.get("on_save_callback")

        # !! TRÈS IMPORTANT : Initialiser la variable AVANT de construire l'UI !!
        self.selected_type = tk.StringVar(value="Debit")

        # 2. Comportement de la fenêtre (Toplevel)
        self.title("Éditeur d'opérations")
        self.transient(parent)  # Liée à la fenêtre parente (se réduit avec elle)
        self.grab_set()  # Capture tous les événements (bloque la fenêtre principale)

        # 3. Construction de l'interface & Chargement initial
        self.build_widgets()
        if hasattr(self, 'initialise'):
            self.initialise()

            # Centrage automatique au moment de l'initialisation
            self.after(50, lambda: self._center_on_parent(parent))

    def _center_on_parent(self, parent):
        # Force le calcul de la taille réelle de la fenêtre
        self.update_idletasks()

        # Dimensions de la modale
        w = self.winfo_width()
        h = self.winfo_height()

        # Position du parent
        px = parent.winfo_x()
        py = parent.winfo_y()
        pw = parent.winfo_width()
        ph = parent.winfo_height()

        # Calcul du centre
        x = px + (pw // 2) - (w // 2)
        y = py + (ph // 2) - (h // 2)

        self.geometry(f"+{x}+{y}")

    # ------------------- Construction UI -------------------
    def build_widgets(self):
        # ==== Boutons Débit / Crédit / Virement ====
        self.frame_top = OperationTypeButton(self, callbacks=self.callbacks)
        self.frame_top.pack(pady=5)

        # ==== Formulaire (factorisé dans OperationSaisieData) ====
        self.form_data = OperationSaisieData(self, callbacks=self.callbacks)
        self.form_data.pack(fill="both", expand=True)

        # Cet appel fonctionne maintenant car self.selected_type ET self.form_data existent !
        self.update_type_buttons()

        # ==== Boutons Enregistrer / Annuler ====
        self.frame_buttons = EditorButton(self, callbacks=self.callbacks)
        self.frame_buttons.pack(side="bottom", fill="x")
        print(self.frame_buttons.winfo_manager())
        print(self.frame_buttons.winfo_children())



    # ------------------- Callbacks -------------------
    def menu_callbacks(self):
        return {
            "action_save": self._on_save,
            "action_cancel": self._on_cancel,
            "action_select_debit": lambda: self.set_type("Debit"),
            "action_select_credit": lambda: self.set_type("Credit"),
            "action_select_virement": lambda: self.set_type("Virement"),
        }

    def set_type(self, type_selected):
        self.selected_type.set(type_selected)
        self.update_type_buttons()

    def update_type_buttons(self):
        # On boucle sur les types pour mettre à jour l'UI
        types = ["Debit", "Credit", "Virement"]
        current = self.selected_type.get()

        for t in types:
            self.frame_top.set_button_style(t, active=(t == current))

        # Adapte le libellé/style du champ montant selon le type sélectionné
        type_mapping = {'Debit': 'depense', 'Credit': 'revenu', 'Virement': 'virement'}
        self.form_data.set_montant_style(type_mapping.get(current, 'depense'))

        current = self.selected_type.get()

        # Appel de la nouvelle méthode pour afficher/masquer le champ Virement
        if hasattr(self.form_data, 'toggle_virement_fields'):
            self.form_data.toggle_virement_fields(current)
    # ------------------- Initialisation -------------------
    def initialise(self):
        """Charge les données dynamiques dans les combobox."""
        self.helpers.initialise()

        tiers_data = self.helpers.fetch_tiers()
        comptes_data = self.helpers.fetch_comptes()
        categories_data = self.helpers.fetch_categories()
        self.form_data.load_combobox_data(tiers_data, comptes_data, categories_data)

        # Si une clé est sélectionnée, charger les données de l'opération
        if self.selected_key:
            data = self.helpers.fetch_data_by_iid(self.selected_key)
            if data:
                self._set_form_values(data)

    def _set_form_values(self, data: dict):
        """Applique le type d'opération puis délègue le remplissage au formulaire."""
        type_op = data.get('type_operation', 'depense')
        if type_op == 'depense':
            self.set_type('Debit')
        elif type_op == 'revenu':
            self.set_type('Credit')
        else:
            self.set_type('Virement')

        self.form_data.set_values_from_operation(data)

    # ------------------- Actions -------------------
    def _on_save(self):
        """Callback pour le bouton Enregistrer."""
        type_mapping = {'Debit': 'depense', 'Credit': 'revenu', 'Virement': 'virement'}
        type_operation = type_mapping.get(self.selected_type.get(), 'depense')

        data = self.form_data.get_form_values()
        data['type_operation'] = type_operation
        success = self.helpers.save_operation(data)

        if success:
            print("Sauvegarde réussie !")
            if self.on_save_callback:
                self.on_save_callback()
            self.destroy()
        else:
            print("Erreur lors de la sauvegarde")

    def _on_cancel(self):
        """Callback pour le bouton Annuler."""
        self.destroy()


# ------------------ Main test ------------------
if __name__ == '__main__':
    # Initialisation du parent (root)
    root = tk.Tk()
    root.title("Application Principale")
    # Taille fixe pour le parent
    w, h = 200, 200
    # 2. Calcul du centre de l'écran
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (w // 2)
    y = (screen_height // 2) - (h // 2)

    # 3. Application de la géométrie au centre
    root.geometry(f'{w}x{h}+{x}+{y}')

    # Simulation des services
    try:
        from _services._bootstrap_services import build_app_services

        services = build_app_services()
    except ImportError:
        services = None

    # Lancement de la modale liée au parent
    # On utilise root.after pour garantir que root est bien positionné
    app = ModOperationSaisie(root, services=services)
    # Force la fermeture de root quand on ferme la fenêtre
    app.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()
