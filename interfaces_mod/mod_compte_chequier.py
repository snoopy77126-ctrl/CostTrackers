
import tkinter as tk
from tkinter import ttk
from interfaces_tabs._tabs_generique_data import BaseFormFrame
from _helpers.chequier_editor_helpers import ChequierEditorHelpers
from interfaces_tabs.tabs_chequier_editor_data import ChequierEditorData
from interfaces_tabs.tabs_chequier_editor_button import ChequierEditorButtons


class ModChequierEditor(tk.Toplevel):
    def __init__(self, parent, services=None, compte_id=None):
        super().__init__(parent)

        # Construction de l'interface segmentée
        self.transient(parent)  # Liée au parent
        self.grab_set()  # Bloque les clics sur la fenêtre principale
        self.title("Carnet de Chèque")

        # Initialisation (Logique métier)
        self.services = services
        self.helpers = ChequierEditorHelpers(services)
        self.compte_id = compte_id  # Peut être None au début
        self.callbacks = self._build_callbacks()


        # Chargement initial
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
        y = py + (ph // 2) - (h)

        self.geometry(f"+{x}+{y}")

    def build_widgets(self):
        self.container = ttk.Frame(self, padding=10)
        self.container.pack(fill="both", expand=True)

    def _build_chequier(self):
        # 1. Préparation du conteneur (LabelFrame)
        if not hasattr(self, "chk_container"):
            self.chk_container = tk.LabelFrame(self.container, text="Gestion des chéquiers", padx=5, pady=5)
            self.chk_container.pack(fill="x", pady=10)

        # 2. Nettoyage
        for child in self.chk_container.winfo_children():
            child.destroy()

        # 3. Récupération des données
        chequiers_liste = [1]
        #chequiers_liste = self.helpers.fetch_row_telephone()  # Supposons que c'est une liste de dicts


        # On détermine le nombre de lignes : au moins 1, sinon la longueur de la liste
        nb_rows = max(1, len(chequiers_liste))

        # 4. Boucle de création
        for i in range(nb_rows):
            # Création des widgets
            chk_widget = ChequierEditorData(self.chk_container, callbacks=self.callbacks)
            chk_widget.grid(row=i, column=0, sticky="nw", padx=5, pady=2)

            chk_buttons = ChequierEditorButtons(self.chk_container, callbacks=self.callbacks)
            chk_buttons.grid(row=i, column=1, sticky="nw", padx=5, pady=2)

            # 5. Remplissage avec gestion d'erreur (si l'index i n'existe pas dans telephones)
            try:
                current_data = chequiers_liste[i]
                for key, value in current_data.items():
                    if key in chk_widget.vars:
                        chk_widget.vars[key].set(value or "")
            except IndexError:
                # C'est une ligne vide (nouveau contact ou ajout), on ne fait rien
                pass

        # 6. Mise à jour des combobox
        self._fill_comboboxes()

    def _build_callbacks(self):
        return {

        }

    def initialise(self):
        """Charge les données et remplit les combos."""
        # SI aucun compte n'est passé par le parent, on va le chercher nous-mêmes
        if self.compte_id is None:
            self.compte_id = self.helpers.get_first_compte_id()

        # Maintenant on a forcément un compte_id, on peut charger les données
        if self.compte_id:
            self._load_data_for_compte(self.compte_id)

    def _load_data_for_compte(self, compte_id):
        pass


# ------------------ Main test ------------------
if __name__ == '__main__':
    # Initialisation du parent (root)
    root = tk.Tk()
    root.title("Application Principale")
    # Taille fixe pour le parent
    w, h = 10, 10
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
    app = ModChequierEditor(root, services=services)
    # Force la fermeture de root quand on ferme la fenêtre
    app.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()
