from interfaces_tabs._tabs_generique_tree import FlatTree


class OperationTree(FlatTree):
    HEADING = ("Fichier", "Statut", "Format", "Lignes",)
    COLUMNS = ("filename", "status", "format", "nb_lignes",)

    def __init__(self, parent, callbacks=None):
        # Stockage propre des callbacks de l'interface appelante
        self.callbacks_ui = callbacks or {}


        # Initialisation de la classe mère FlatTree
        super().__init__(
            parent,
            columns=self.COLUMNS,
            headings=self.HEADING,
            callbacks={
                "on_select": self._handle_row_selection,
                "on_double_click": self._handle_row_double_click,
                "on_right_click": self._handle_row_right_click,
            }
        )

        # Configuration des styles de lignes sur le composant Treeview sous-jacent
        self.tree.tag_configure("error", foreground="#b00020")
        self.tree.tag_configure("imported", foreground="#137333")
        self.tree.tag_configure("pending", foreground="#202124")

        self._configure_columns()

        self.mapping_vars = {}

    # =========================================================
    # GESTION DES ÉVÉNEMENTS (Sécurisés contre les lignes vides)
    # =========================================================
    def _configure_columns(self):
        # Définition des largeurs en pixels
        self.tree.column("filename", width=180, minwidth=150)
        self.tree.column("status", width=80, minwidth=100)
        self.tree.column("format", width=60, minwidth=50)
        self.tree.column("nb_lignes", width=60, minwidth=50)

    def _handle_row_selection(self, row):
        """Déclenché lors d'un simple clic sur une ligne du Treeview."""
        if not row:  # Sécurité si l'utilisateur clique dans le vide du tableau
            return

        cb = self.callbacks_ui.get("on_file_selected")
        if cb:
            cb(row)

    def _handle_row_double_click(self, row):
        """Déclenché lors d'un double-clic (ex: pour forcer l'import ou ouvrir)."""
        if not row:
            return

        # Si vous avez une callback spécifique pour le double-clic (ex: 'on_file_double_click')
        # utilisez-la, sinon on bascule par défaut sur la sélection classique.
        cb = self.callbacks_ui.get("on_file_double_click") or self.callbacks_ui.get("on_file_selected")
        if cb:
            cb(row)

    def _handle_row_right_click(self, row, event):
        """Déclenché lors d'un clic droit pour ouvrir un Menu Contextuel (Popup)."""
        if not row:
            return

        cb = self.callbacks_ui.get("on_right_click_file")
        if cb:
            # On transmet la ligne concernée ET l'événement (pour la position x/y du menu)
            cb(row, event)

class FilesTree(FlatTree):
    COLUMNS = ("Fichier","Statut","Format","Lignes",)
    HEADING = ("#0","label","format","rows",)

    def __init__(self, parent, callbacks=None):
        self.callbacks_ui = callbacks or {}

        super().__init__(
            parent,
            columns=self.COLUMNS,
            headings=self.HEADING,
            callbacks={
                "on_select": self._handle_row_selection,
                "on_double_click": self._handle_row_double_click,
                "on_right_click": self._on_right_click,
            }
        )

    def _handle_row_selection(self, row):
        cb = self.callbacks_ui.get("on_emetteur_selected")
        if cb: cb(row)

    def _handle_row_double_click(self, row):
        cb = self.callbacks_ui.get("on_emetteur_opened")
        if cb: cb(row)