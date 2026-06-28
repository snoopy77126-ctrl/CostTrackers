import tkinter as tk
from tkinter import ttk
from interfaces_tabs._tabs_generique_data import BaseFormFrame

class ChequierEditorData(BaseFormFrame):
    def __init__(self, parent, callbacks=None):
        super().__init__(parent, title="", callbacks=callbacks)
        self.add_entry("chequier_num", "Chéquier N°")
        self.add_combobox("nbr_cheque", "Nombre de Chéque")
        self.add_entry("premier_cheque", "1er chèque")
        self.add_date("date_reception", "Date de Réception")
        self.add_entry("dernier_emis", "Dernier émis")

        # Configuration du poids des colonnes pour l'expansion
        for i in range(5):
            self.form.columnconfigure(i, weight=1)