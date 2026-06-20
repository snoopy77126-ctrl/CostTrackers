import tkinter as tk
from tkinter import ttk

from _helpers.compte_fusion_helpers import CompteFusionHelpers

class CompteFusionEditor(tk.Toplevel):
    def __init__(self, parent, selected_compte, services=None):
        super().__init__(parent)

        # Construction de l'interface
        self.title("Fusionner les Comptes")
        self.geometry("900x450")

        # Rend la fenêtre modale par rapport au parent
        self.transient(parent)
        self.grab_set()

        # Initialisation (Logique métier)
        self.services = services
        self.helper = CompteFusionHelpers(services)
        self.helper.load_data(selected_compte)
        self.callbacks = self._build_callbacks()

        # Chargement initial
        self.build_widgets()
        self._populate_data()

    def build_widgets(self):
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # --- Conteneur principal ---
        main_frame = ttk.Frame(self, padding=10)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        # --- Treeview ---
        cols, headings = self.helper.get_columns_config()
        self.tree = ttk.Treeview(main_frame, columns=cols, show="headings")

        for col, heading in zip(cols, headings):
            self.tree.heading(col, text=heading)
            # La colonne Champ et Après peuvent être plus larges
            width = 150 if col in ["champ", "apres"] else 120
            self.tree.column(col, width=width, anchor="w")

        # Styles pour les conflits
        self.tree.tag_configure("conflit", foreground="red")

        self.tree.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        # Scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=(0, 10))

        # Événement de clic pour sélectionner la valeur
        self.tree.bind("<ButtonRelease-1>", self._on_cell_click)

        # --- Zone d'information et Boutons ---
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        bottom_frame.columnconfigure(0, weight=1)

        info_text = "Il y a des conflits. Cliquez sur le contenu à conserver dans l'une des colonnes pour l'utiliser dans la colonne Après."
        ttk.Label(bottom_frame, text=info_text, wraplength=600).grid(row=0, column=0, sticky="w")

        btn_frame = ttk.Frame(bottom_frame)
        btn_frame.grid(row=0, column=1, sticky="e")

        ttk.Button(btn_frame, text="OK", command=self._action_ok).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Annuler", command=self.destroy).pack(side="left")

    def _build_callbacks(self):
        return {}

    def _populate_data(self):
        rows = self.helper.prepare_rows()
        for i, row_data in enumerate(rows):
            tags = ("conflit",) if row_data["conflit"] else ()
            values = (
                row_data["label"],
                row_data["valeur_apres"],
                *row_data["valeurs_tiers"],
            )
            # On stocke le champ_sql dans l'iid pour pouvoir le récupérer dans _action_ok
            self.tree.insert("", "end", iid=row_data["champ_sql"], values=values, tags=tags)

    def _on_cell_click(self, event):
        """Gestion de la copie de la valeur cliquée vers la colonne 'Après'"""
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        col_id = self.tree.identify_column(event.x)  # Format: '#3', '#4', etc.
        row_iid = self.tree.identify_row(event.y)

        if not row_iid:
            return

        # Conversion de l'ID colonne en index (0-based)
        col_idx = int(col_id.replace('#', '')) - 1
        values = list(self.tree.item(row_iid, "values"))

        # Sécurité : vérifier que l'index cliqué existe bien dans la liste des valeurs
        if 2 <= col_idx < len(values):
            valeur_selectionnee = values[col_idx]

            # Mise à jour de la colonne "Après" (index 1)
            values[1] = valeur_selectionnee

            # Mise à jour de la ligne dans le Treeview
            self.tree.item(row_iid, values=values)

            # Optionnel : retirer le tag conflit si une valeur est choisie
            self.tree.item(row_iid, tags=())

    def _action_ok(self):
        """Collecte les valeurs finales de la colonne 'Après' et lance la fusion."""
        resultats = {}
        for champ_sql in self.tree.get_children():
            values = self.tree.item(champ_sql, "values")
            if len(values) >= 2:
                valeur_apres = values[1]
                resultats[champ_sql] = valeur_apres  # clé = nom SQL réel

        self.helper.executer_fusion(resultats)
        self.destroy()

# ------------------ Main test ------------------
if __name__ == '__main__':
    # Import mocké ou réel
    try:
        from _services._bootstrap_services import build_app_services

        services_app = build_app_services()
    except ImportError:
        services_app = None  # Fallback pour forcer l'affichage lors du test

    selected_compte = [{'iid_key': 2, 'id': 2, 'value': 'BoursoBank (BousoBank)', 'actif': True},
				{'iid_key': 3, 'id': 3, 'value': 'BoursoBank (BousoBank)', 'actif': True}
                ]

    root = tk.Tk()
    root.title("Fenêtre Principale")

    # Au lieu de withdraw(), on réduit la fenêtre principale au minimum
    # pour qu'elle ne gêne pas, sans rendre la modale invisible.
    root.geometry('0x0+10000+10000')  # La place hors de l'écran

    # On passe les services ET les tiers sélectionnés
    app = CompteFusionEditor(
        parent=root,
        services=services_app,
        selected_compte=selected_compte
    )

    # Force la fermeture de l'application entière quand on ferme la modale
    app.protocol("WM_DELETE_WINDOW", root.destroy)

    # Indispensable : on lance la boucle d'événements pour afficher l'interface
    root.mainloop()