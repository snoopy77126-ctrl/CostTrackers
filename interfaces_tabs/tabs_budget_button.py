# -*- coding: utf-8 -*-
####################################
# Projet : CostTracker
# Fichier : interfaces_tabs/tabs_budget_button.py
# Description : Boutons du module Budget
# Date : 24/06/2026     Etat : Stable
####################################

from tkinter import ttk
from typing import Dict, Optional, Callable
from interfaces_tabs._tabs_generique_button import EditeurActions


class BudgetButton(EditeurActions):
    def __init__(self, parent, callbacks: Optional[Dict[str, Callable]] = None):
        super().__init__(parent)
        self.callbacks = callbacks or {}
        self.container = ttk.Frame(self, padding=5)
        self.container.pack(fill="x")
        self._build_widgets()

    def _build_widgets(self):
        self._add_btn_left("➕ Nouveau",          "action_add")
        self._add_btn_left("🗑️ Supprimer",       "action_delete")
        self._add_btn_left("⚡ Depuis périodiques","action_init_periodiques")
        self._add_btn_end( "💾 Sauvegarder",      "action_save")
