from tkinter import ttk
from typing import Dict, Optional, Callable

from interfaces_tabs._tabs_generique_button import EditeurActions


class ModePaiementEditorButton(EditeurActions):
    """
    Spécialisation de EditeurActions pour la gestion des modes de paiement (Ajouter, Modifier, Supprimer).
    """

    def __init__(self, parent, callbacks: Optional[Dict[str, Callable]] = None):
        super().__init__(parent)
        self.callbacks = callbacks or {}

        self.container = ttk.Frame(self, padding=5)
        self.container.pack(fill="x")

        self._build_widgets()

    def _build_widgets(self):
        self._add_btn_left("➕ Nouveau", "action_add_mode_paiement")
        self._add_btn_left("🗑️ Supprimer", "action_delete_mode_paiement")
        self._add_btn_end("💾 Sauvegarder", "action_save_mode_paiement")
