from tkinter import ttk
from typing import Dict, Optional, Callable

# Importez EditeurActions depuis le fichier correspondant
from interfaces_tabs._tabs_generique_button import EditeurActions

class OperationButton(EditeurActions):
    """ Spécialisation de EditeurActions pour la gestion de fichiers (Ajouter, Modifier, Supprimer). """

    def __init__(self, parent, callbacks: Optional[Dict[str, Callable]] = None):
        # Initialisation via ttk.Frame
        super().__init__(parent)
        self.callbacks = callbacks or {}

        # Le conteneur interne pour les boutons (requis par EditeurActions)
        self.container = ttk.Frame(self, padding=5)
        self.container.pack(fill="x")

        self._build_widgets()

    def _build_widgets(self):
        """
        Remplace la création manuelle par les méthodes standardisées
        de la classe parente.
        """
        # Utilisation de _add_btn_left pour un alignement horizontal classique
        self._add_btn_top("➕ New Opération", "action_add_operation")
        self._add_btn_top("Actualiser", "reload")

class OperationButton_old(EditeurActions):
    """ Spécialisation de EditeurActions pour la gestion de fichiers (Ajouter, Modifier, Supprimer). """

    def __init__(self, parent, callbacks: Optional[Dict[str, Callable]] = None):
        # Initialisation via ttk.Frame
        super().__init__(parent)
        self.callbacks = callbacks or {}

        # Le conteneur interne pour les boutons (requis par EditeurActions)
        self.container = ttk.Frame(self, padding=5)
        self.container.pack(fill="x")

        self._build_widgets()

    def _build_widgets(self):
        """
        Remplace la création manuelle par les méthodes standardisées
        de la classe parente.
        """
        # Utilisation de _add_btn_left pour un alignement horizontal classique
        self._add_btn_left("Tester fichier", "test_selected_file")
        self._add_btn_left("Importer fichier", "import_selected_file")
        self._add_btn_left("Importer dossier", "import_folder")
        self._add_btn_left("Actualiser", "reload")

