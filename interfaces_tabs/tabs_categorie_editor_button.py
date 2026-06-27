from tkinter import ttk
from typing import Dict, Optional, Callable

# Importez EditeurActions depuis le fichier correspondant
from interfaces_tabs._tabs_generique_button import EditeurActions


class EditorButton(EditeurActions):
    """
    Spécialisation de EditeurActions pour la gestion de fichiers (Ajouter, Modifier, Supprimer).
    """

    def __init__(self, parent, callbacks: Optional[Dict[str, Callable]] = None):
        # Initialisation via ttk.Frame
        super().__init__(parent)
        self.callbacks = callbacks or {}
        # Le conteneur interne pour les boutons (requis par EditeurActions)
        self.container = ttk.Frame(self, padding=5)
        self.container.pack(fill="x")

        self._build_widgets()

    def _build_widgets(self):
        self._add_btn_left("➕ Ajouter", "action_add_category")
        self._add_btn_left("🗑️ Supprimer", "action_delete_category")
        self._add_btn_end("💾 Editer", "action_edit_category")
        self._add_btn_end("✏️ Fusionner", "action_fusionner_category")

class EditorButton2(EditeurActions):
    """
    Spécialisation de EditeurActions pour la gestion de fichiers (Ajouter, Modifier, Supprimer).
    """

    def __init__(self, parent, callbacks: Optional[Dict[str, Callable]] = None):
        # Initialisation via ttk.Frame
        super().__init__(parent)
        self.callbacks = callbacks or {}
        # Le conteneur interne pour les boutons (requis par EditeurActions)
        self.container = ttk.Frame(self, padding=5)
        self.container.pack(fill="x")

        self._build_widgets()

    def _build_widgets(self):
        self._add_btn_left("➕ Ajouter", "action_add_category")
        self._add_btn_left("🗑️ Supprimer", "action_delete_category")
        self._add_btn_end("💾 Enregistrer", "action_edit_category")
        self._add_btn_end("✏️ Fusionner", "action_fusionner_category")

