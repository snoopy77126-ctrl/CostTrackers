# models/ui/tabs_prevision_button.py

import tkinter as tk
from tkinter import ttk
from tkinter import ttk
from typing import Dict, Optional, Callable

from interfaces_tabs._tabs_generique_button import EditeurActions

class PrevisionButton(EditeurActions):
    def __init__(self, parent, callbacks: Optional[Dict[str, Callable]] = None):
        super().__init__(parent)
        self.callbacks = callbacks or {}

        # Le conteneur interne pour les boutons (requis par EditeurActions)
        self.container = ttk.Frame(self, padding=5)
        self.container.pack(fill="x")

        self._build_widgets()

    def _build_widgets(self):
        self._add_btn_left("✏️ Ajouter détail", "action_add_detail")
        self._add_btn_left("💾 Sauvegarder", "action_save_prevision")
