from interfaces_tabs._tabs_generique_tree import TreeView


class EmetteurTree(TreeView):
    def __init__(self, parent, callbacks=None):
        self.callbacks_ui = callbacks or {}
        super().__init__(
            parent,
            callbacks={
                "on_select": self._handle_row_selection,
                "on_double_click": self._handle_row_double_click,
            }
        )

    def _handle_row_selection(self, row):
        cb = self.callbacks_ui.get("on_emetteur_selected")
        if cb: cb(row)

    def _handle_row_double_click(self, row):
        cb = self.callbacks_ui.get("on_emetteur_opened")
        if cb: cb(row)

