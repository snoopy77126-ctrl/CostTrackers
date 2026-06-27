import tkinter as tk
from datetime import date, datetime
from tkinter import ttk
from tkcalendar import DateEntry


class OperationSaisieData(ttk.Frame):
    def __init__(self, parent, callbacks=None):
        super().__init__(parent)
        self.callbacks = callbacks
        self.entries = {}
        self.vars = {}

        self.columnconfigure(1, weight=1)
        self.columnconfigure(3, weight=1)

        self.build_widgets()

    def build_widgets(self):
        # Ligne 0 : Libellé
        ttk.Label(self, text="Opération").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.vars["libelle"] = tk.StringVar()
        self.entries["libelle"] = ttk.Combobox(self, textvariable=self.vars["libelle"])
        self.entries["libelle"].grid(row=0, column=1, columnspan=3, sticky="ew", padx=5, pady=2)

        # Ligne 1 : Tiers et Banque
        ttk.Label(self, text="Tiers").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.vars["tiers_id"] = tk.StringVar()
        self.entries["tiers_id"] = ttk.Combobox(self, textvariable=self.vars["tiers_id"])
        self.entries["tiers_id"].grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(self, text="Banque").grid(row=1, column=2, sticky="w", padx=5, pady=2)
        self.vars["compte_id"] = tk.StringVar()
        self.entries["compte_id"] = ttk.Combobox(self, textvariable=self.vars["compte_id"])
        self.entries["compte_id"].grid(row=1, column=3, sticky="ew", padx=5, pady=2)

        # Ligne 2 : Note
        ttk.Label(self, text="Note").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.vars["commentaire"] = tk.StringVar()
        self.entries["commentaire"] = ttk.Entry(self, textvariable=self.vars["commentaire"])
        self.entries["commentaire"].grid(row=2, column=1, columnspan=3, sticky="ew", padx=5, pady=2)

        # Ligne 3 : Catégorie
        ttk.Label(self, text="Catégorie").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.vars["categorie_id"] = tk.StringVar()
        self.entries["categorie_id"] = ttk.Combobox(self, textvariable=self.vars["categorie_id"])
        self.entries["categorie_id"].grid(row=3, column=1, columnspan=3, sticky="ew", padx=5, pady=2)

        # Ligne 4 : Montant et Solde
        ttk.Label(self, text="Montant").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        self.vars["montant"] = tk.StringVar()
        self.entries["montant"] = ttk.Entry(self, textvariable=self.vars["montant"])
        self.entries["montant"].grid(row=4, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(self, text="Solde").grid(row=4, column=2, sticky="w", padx=5, pady=2)
        self.vars["solde"] = tk.StringVar()
        self.entries["solde"] = ttk.Entry(self, textvariable=self.vars["solde"])
        self.entries["solde"].grid(row=4, column=3, sticky="ew", padx=5, pady=2)

        # Ligne 5 : Date et Périodique
        ttk.Label(self, text="Date").grid(row=5, column=0, sticky="w", padx=5, pady=2)
        self.vars["date_operation"] = tk.StringVar()
        self.entries["date_operation"] = DateEntry(
            self,
            textvariable=self.vars["date_operation"],
            date_pattern="dd/MM/yyyy",
            locale="fr_FR"
        )
        self.entries["date_operation"].grid(row=5, column=1, sticky="ew", padx=5, pady=2)

        self.vars["periodique"] = tk.BooleanVar()
        self.entries["periodique"] = ttk.Checkbutton(
            self, text="Opération Périodique", variable=self.vars["periodique"]
        )
        self.entries["periodique"].grid(row=5, column=2, columnspan=2, sticky="w", padx=5, pady=2)

        # Ligne 6 : Virement (caché par défaut)
        self.label_dest = ttk.Label(self, text="Compte Dest.")
        self.vars["compte_dest_id"] = tk.StringVar()
        self.entries["compte_dest_id"] = ttk.Combobox(self, textvariable=self.vars["compte_dest_id"])

        self.toggle_virement_fields("Debit")

    # ------------------- Combobox -------------------

    def load_combobox_data(self, tiers, comptes, categories):
        """Charge les données et stocke les raw data pour select_combobox_by_key."""
        self._raw_data_tiers_id = tiers
        self._raw_data_compte_id = comptes
        self._raw_data_categorie_id = categories
        self._raw_data_compte_dest_id = comptes

        self.entries["tiers_id"]["values"] = [t['value'] for t in tiers]
        self.entries["compte_id"]["values"] = [c['value'] for c in comptes]
        self.entries["categorie_id"]["values"] = [cat['value'] for cat in categories]
        self.entries["compte_dest_id"]["values"] = [c['value'] for c in comptes]

    def select_combobox_by_key(self, key, selected_key):
        """Sélectionne une ligne de combobox depuis son iid_key."""
        combo = self.entries.get(key)
        if not isinstance(combo, ttk.Combobox):
            return False

        raw_data = getattr(self, f"_raw_data_{key}", [])
        for index, item in enumerate(raw_data):
            if str(item.get("iid_key")) == str(selected_key):
                combo.current(index)
                setattr(self, f"_selected_key_{key}", selected_key)
                self.vars[key].set(item.get("display_value") or item.get("value", ""))
                return True

        combo.set("")
        setattr(self, f"_selected_key_{key}", None)
        return False

    # ------------------- Remplissage formulaire -------------------

    def set_values_from_operation(self, data: dict):
        """Remplit les widgets depuis un dictionnaire d'opération."""
        for key, value in data.items():
            if key not in self.entries:
                continue
            widget = self.entries[key]

            if isinstance(widget, ttk.Combobox):
                success = self.select_combobox_by_key(key, value)
                if not success:
                    widget.set(str(value) if value is not None else "")

            elif isinstance(widget, DateEntry):
                date_val = self._format_date_for_display(value)
                if date_val:
                    widget.set_date(date_val)

            elif isinstance(widget, ttk.Entry):
                widget.delete(0, tk.END)
                widget.insert(0, str(value) if value is not None else "")

        # Checkbox périodique
        if "periodique" in self.vars:
            self.vars["periodique"].set(bool(data.get("periodique", False)))

    # ------------------- Lecture formulaire -------------------

    def get_form_values(self, type_operation):
        """Retourne les valeurs du formulaire sous forme de dictionnaire."""
        data = {}
        for key, widget in self.entries.items():
            if isinstance(widget, ttk.Checkbutton):
                data[key] = bool(self.vars[key].get())
            elif isinstance(widget, DateEntry):
                data[key] = self._format_date_for_storage(self.vars[key].get())
            elif isinstance(widget, ttk.Combobox):
                selected_key = getattr(self, f"_selected_key_{key}", None)
                data[key] = selected_key if selected_key is not None else self.vars.get(key, tk.StringVar()).get()
            else:
                val = self.vars.get(key, tk.StringVar()).get().strip()
                data[key] = val if val else None

        data["type_operation"] = type_operation
        return data

    # ------------------- Style -------------------

    def set_montant_style(self, style):
        color = {'depense': 'red', 'revenu': 'green', 'virement': '#2f4f7f'}
        self.entries["montant"].config(foreground=color.get(style, 'black'))

    # ------------------- Virement -------------------

    def toggle_virement_fields(self, type_operation):
        """Affiche ou masque le champ compte_dest_id selon le type."""
        if type_operation == "Virement":
            self.label_dest.grid(row=6, column=0, sticky="w", padx=5, pady=2)
            self.entries["compte_dest_id"].grid(row=6, column=1, columnspan=3, sticky="ew", padx=5, pady=2)
        else:
            self.label_dest.grid_remove()
            self.entries["compte_dest_id"].grid_remove()

    # ------------------- Utilitaires date -------------------

    @staticmethod
    def _format_date_for_display(value):
        """Convertit une date DB/Python en objet date pour DateEntry."""
        if value in (None, "", "None"):
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        value = str(value).strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y"):
            try:
                return datetime.strptime(value.split(" ")[0], fmt).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def _format_date_for_storage(value):
        """Convertit une date FR (JJ/MM/AAAA) en format ISO (AAAA-MM-JJ)."""
        if value in (None, "", "None"):
            return None
        if isinstance(value, (datetime, date)):
            return value.strftime("%Y-%m-%d")
        value = str(value).strip()
        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
            try:
                return datetime.strptime(value.split(" ")[0], fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None
