from tkinter import ttk
from typing import Dict, Optional, Callable

# Importez EditeurActions depuis le fichier correspondant
from interfaces_tabs._tabs_generique_button import EditeurActions


class BanqueEditorButton(EditeurActions):
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
        self._add_btn_left("➕ Ajouter", "action_new_account")
        self._add_btn_left("💾 Sauvegarder", "action_save_account")
        self._add_btn_left("🗑️ Supprimer", "action_delete_account")
        self._add_btn_end("✏️ Fusionner", "action_fusionner")

class PaiementEditorButton(EditeurActions):
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
        self._add_btn_top("⏮", "action_unselect_all")
        self._add_btn_top("◀", "action_unselect")

        self._add_btn_bottom("⏭", "action_select_all")
        self._add_btn_bottom("▶", "action_select")
