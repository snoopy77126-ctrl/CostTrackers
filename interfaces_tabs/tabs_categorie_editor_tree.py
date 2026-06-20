from interfaces_tabs._tabs_generique_tree import TreeView


class CategoryTree(TreeView):

    def __init__(self, parent, callbacks=None):
        self.callbacks_ui = callbacks or {}

        super().__init__(
            parent,
            callbacks={
                "on_select": self._handle_row_selection,
                "on_double_click": self._handle_row_double_click,
                "on_right_click": self._handle_row_right_click,
            }
        )

    # --------------------------
    # EVENTS UI → METIER
    # --------------------------
    def _handle_row_selection(self, row):
        cb = self.callbacks_ui.get("on_category_selected")
        if cb:
            cb(row)

    def _handle_row_double_click(self, row):
        cb = self.callbacks_ui.get("on_category_opened")
        if cb:
            cb(row)

    def _handle_row_right_click(self, row, event):
        cb = self.callbacks_ui.get("on_right_click_category")
        if cb:
            cb(row, event)

