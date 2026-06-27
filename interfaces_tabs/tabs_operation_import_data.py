from interfaces_tabs._tabs_generique_data import BaseFormFrame
from tkinter import ttk


class OperationImportData(BaseFormFrame):
    def __init__(self, parent, callbacks=None, target_columns=None):
        super().__init__(parent, title="Affectation des colonnes", callbacks=callbacks)
        self.target_columns = target_columns or {}
        self.combo_widgets = {}
        self._all_columns = []  # ← initialisé vide
        self._build_fields()

    def _build_fields(self):
        left_frame = ttk.Frame(self.form)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        right_frame = ttk.Frame(self.form)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        items = list(self.target_columns.items())
        midpoint = (len(items) + 1) // 2

        self._row_counter = 0
        for target, label in items[:midpoint]:
            original_form = self.form
            self.form = left_frame
            # ← on_select branché ici
            self.add_combobox(target, f"{label} :", on_select=lambda _: self._refresh_available_columns())
            self.form = original_form

        self._row_counter = 0
        for target, label in items[midpoint:]:
            original_form = self.form
            self.form = right_frame
            self.add_combobox(target, f"{label} :", on_select=lambda _: self._refresh_available_columns())
            self.form = original_form

    def _refresh_available_columns(self):
        """Retire des listes les colonnes déjà affectées dans une autre combobox."""
        # 1. Collecter toutes les valeurs actuellement sélectionnées
        selected = {var.get() for var in self.vars.values() if var.get()}

        # 2. Pour chaque combobox, reconstruire sa liste sans les valeurs
        #    prises par les autres (sauf la sienne propre)
        for key, widget in self.entries.items():
            if not (hasattr(widget, "widgetName") and "combobox" in widget.widgetName):
                continue

            current_val = self.vars[key].get()
            # Valeurs disponibles = toutes les colonnes - celles prises par les autres
            available = [c for c in self._all_columns if c == "" or c not in selected or c == current_val]
            widget["values"] = available

    def get_mapping(self):
        """Récupère l'état actuel du mapping pour le parent."""
        return {k: v.get() for k, v in self.vars.items()}

    def _clear(self):
        """Réinitialisation propre."""
        self.set_values({k: "" for k in self.vars.keys()})
