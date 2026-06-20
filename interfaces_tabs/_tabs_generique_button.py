from tkinter import ttk
from typing import Dict, Optional, Callable


class EditeurActions(ttk.Frame):
    """
    Barre de boutons standardisée.
    Permet de placer des boutons aux 4 points cardinaux du conteneur.
    """

    def _create_btn(self, text, cb_name, side, width=None, style=None):
        btn = ttk.Button(
            self.container,
            text=text,
            width=width,
            style=style if style else "TButton",
            command=lambda: self._trigger(cb_name)
        )
        # fill='x' est utile surtout pour top/bottom pour prendre toute la largeur
        fill = "x" if side in ["top", "bottom"] else "none"
        btn.pack(side=side, padx=2, pady=2, fill=fill)
        return btn

    def _trigger(self, callback_name):
        callback = self.callbacks.get(callback_name)
        if callback:
            callback()

    def _add_btn_left(self, text, cb_name, width=None, style=None):
        """Aligne à gauche (side='left')."""
        return self._create_btn(text, cb_name, "left", width, style)

    def _add_btn_end(self, text, cb_name, width=None, style=None):
        """Aligne à droite (side='right')."""
        return self._create_btn(text, cb_name, "right", width, style)

    def _add_btn_top(self, text, cb_name, width=None, style=None):
        """Aligne en haut (side='top')."""
        return self._create_btn(text, cb_name, "top", width, style)

    def _add_btn_bottom(self, text, cb_name, width=None, style=None):
        """Aligne en bas (side='bottom')."""
        return self._create_btn(text, cb_name, "bottom", width, style)


class ExempleActions(EditeurActions):
    def __init__(self, parent, callbacks: Optional[Dict[str, Callable]] = None):
        # Initialisation via ttk.Frame
        super().__init__(parent)
        self.callbacks = callbacks or {}

        # Le conteneur interne pour les boutons (requis par EditeurActions)
        self.container = ttk.Frame(self, padding=5)
        self.container.pack(fill="x")

        self._build_widgets()

    def _build_widgets(self):
        self._add_btn_left("📁 + Dossier", "add_dossier")
        self._add_btn_left("⚙️ Param", "view_param")
        self._add_btn_end('❬', "action_next_file")
        self._add_btn_end("<", "action_prev_file")
        self._add_btn_left("📄 + Classeur", "add_classeur")
        self._add_btn_left("➕ Nouveau", "action_add_file")
        self._add_btn_left("✨ Reconnaître", "action_recognize_file")
        self._add_btn_left("🗑️ Supprimer", "action_delete_file")
        self._add_btn_end("✏️ Modifier", "action_edit_file")
        self._add_btn_end("💾 Sauvegarder", "action_save_file")
        self._add_btn_end(" 🔥 force", "purge_cache_tracker")
        self._add_btn_end("⏮"   "⏭", "action_next_file")
        self._add_btn_end("◀"   "▶", "action_prev_file")
        self._add_btn_end("➡", 'action_next_file')
        self._add_btn_end("⬅", "action_prev_file")

