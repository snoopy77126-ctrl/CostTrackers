from interfaces_tabs._tabs_generique_tree import FlatTree

class OperationTree(FlatTree):

    def __init__(self, parent, callbacks=None, columns=None, headings=None):
        self.callbacks_ui = callbacks or {}
        columns = columns or ("date_operation", "categorie", "tiers", "debit", "credit", "solde")
        headings = headings or ("Date", "CategorieParent", "Tiers", "Débit", "Crédit", "Solde")
        super().__init__(
            parent,
            columns=columns,
            headings=headings,
            callbacks={
                "on_select": self._handle_row_selection,
                "on_double_click": self._handle_row_double_click,
            }
        )
        for col in columns:
            self.tree.column(col, width=110, stretch=True)

    def _handle_row_selection(self, row):
        print(f'[DEBUG]FilesTree:_handle_row_selection')
        cb = self.callbacks_ui.get("on_operation_selected")
        if cb: cb(row)

    def _handle_row_double_click(self, row):
        print(f'[DEBUG]FilesTree:_handle_row_double_click')
        cb = self.callbacks_ui.get("on_operation_opened")
        if cb: cb(row)