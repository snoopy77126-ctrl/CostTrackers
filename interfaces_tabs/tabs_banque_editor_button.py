from tkinter import ttk
from typing import Dict, Optional, Callable

# Importez EditeurActions depuis le fichier correspondant
from interfaces_tabs._tabs_generique_button import EditeurActions


class BanqueButton(EditeurActions):
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
        self._add_btn_left("➕ Nouveau", "action_add_banque")
        self._add_btn_left("🗑️ Supprimer", "action_delete_banque")
        # self._add_btn_end("✏️ Modifier", "action_edit_file")
        self._add_btn_end("💾 Sauvegarder", "action_save_banque")

