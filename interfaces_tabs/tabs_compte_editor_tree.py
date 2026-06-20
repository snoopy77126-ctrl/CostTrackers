from interfaces_tabs._tabs_generique_tree import TreeView


class BanqueEditorTree(TreeView):
    def __init__(self, parent, callbacks=None):
        # Contiendra {"on_banque_selected": ..., "on_banque_opened": ...}
        self.callbacks_ui = callbacks or {}
        super().__init__(
            parent,
            callbacks={
                "on_select": self._handle_row_selection,
                "on_double_click": self._handle_row_double_click,
                "on_right_click": self._handle_row_right_click,
            }
        )

    # Liens Événements UI → Callbacks externes reçues de la vue principale
    def _handle_row_selection(self, row):
        cb = self.callbacks_ui.get("on_compte_selected")
        if cb:
            cb(row)

    def _handle_row_double_click(self, row):
        cb = self.callbacks_ui.get("on_compte_selected")
        if cb:
            cb(row)

    def _handle_row_right_click(self, row, event):
        cb = self.callbacks_ui.get("on_right_click_banque")
        if cb:
            cb(row, event)

