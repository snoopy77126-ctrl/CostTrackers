import tkinter as tk
from datetime import date, datetime
from tkinter import ttk
from typing import Callable

from tkcalendar import DateEntry


class BaseFormFrame(ttk.Frame):
    """Moteur de génération de formulaire avec gestion automatique des lignes."""

    def __init__(self, parent, title="", callbacks: dict = None):
        super().__init__(parent)
        self.callbacks = callbacks or {}
        self._form_data = {}
        self.vars = {}
        self.entries = {}
        self._row_counter = 0

        self.form = ttk.LabelFrame(self, text=title, padding=10) if title else ttk.Frame(self, padding=10)
        self.form.pack(fill="both", expand=True)
        self.form.columnconfigure(1, weight=1)

    def next_row(self):
        """Incrémente et retourne l'index de la ligne suivante."""
        r = self._row_counter
        self._row_counter += 1
        return r

    def select_combobox_by_key(self, key, selected_key):
        """
        Sélectionne une ligne de combobox depuis son iid_key.
        C'est cette méthode qui causait l'AttributeError.
        """
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

    def _bind_clear_key(self, key, widget):
        widget.bind("<Delete>", lambda event: self._clear_widget_value(key))

    def _clear_widget_value(self, key):
        widget = self.entries.get(key)
        if widget is None:
            return "break"

        if isinstance(widget, ttk.Combobox):
            widget.set("")
            self.vars[key].set("")
            setattr(self, f"_selected_key_{key}", None)
        else:
            widget.delete(0, "end")
            self.vars[key].set("")

        return "break"

    def reset_form(self):
        """Méthode explicite pour vider totalement le formulaire."""
        self._form_data = {}
        self._snapshot = {}  # Vider le snapshot !
        self._clear()  # Appelle la méthode de la classe parente

    def add_entry(self, key, label, row=None, grid_options=None):
        if row is None: row = self.next_row()
        ttk.Label(self.form, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)

        var = tk.StringVar()
        entry = ttk.Entry(self.form, textvariable=var)

        # Application du grid par défaut ou personnalisé
        default_opts = {"row": row, "column": 1, "sticky": "ew", "padx": 5, "pady": 2}
        if grid_options:
            default_opts.update(grid_options)

        entry.grid(**default_opts)

        self.vars[key] = var
        self.entries[key] = entry
        self._bind_clear_key(key, entry)
        return entry

    def add_combobox(self, key, label, row=None, on_select: Callable = None, container=None, grid_options=None):
        target_parent = container if container is not None else self.form

        if row is None: row = self.next_row()
        ttk.Label(target_parent, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        var = tk.StringVar()
        combo = ttk.Combobox(target_parent, textvariable=var, state="readonly")

        # Application du grid par défaut ou personnalisé
        default_opts = {"row": row, "column": 1, "sticky": "ew", "padx": 5, "pady": 2}
        if grid_options:
            default_opts.update(grid_options)

        combo.grid(**default_opts)
        combo.bind("<<ComboboxSelected>>", lambda e: self._on_combobox_selected(key, on_select))
        self.vars[key] = var
        self.entries[key] = combo
        self._bind_clear_key(key, combo)
        return combo

    def add_checkbox(self, key, label, text="", row=None):
        """
        Ajoute une case à cocher (Checkbutton).
        :param key: Clé unique pour identifier la donnée.
        :param label: Texte affiché à gauche (comme pour les autres champs).
        :param text: Texte optionnel affiché à côté de la case elle-même.
        """
        if row is None: row = self.next_row()

        # Libellé aligné à gauche
        ttk.Label(self.form, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)

        # Utilisation d'un BooleanVar (True/False)
        var = tk.BooleanVar(value=False)

        # Création du Checkbutton
        check = ttk.Checkbutton(self.form, text=text, variable=var)
        check.grid(row=row, column=1, sticky="w", padx=5, pady=2)

        self.vars[key] = var
        self.entries[key] = check

        # Liaison de la touche Suppr pour décocher
        self._bind_clear_key(key, check)

        return check

    def add_date(self, key, label, row=None, grid_options=None,date_defaut=False):
        if row is None: row = self.next_row()
        ttk.Label(self.form, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        var = tk.StringVar()
        date_ent = DateEntry(self.form, textvariable=var, date_pattern="dd/MM/yyyy", locale="fr_FR")
        # Supprimer la date par défaut (date du jour)
        if not date_defaut:
            date_ent.delete(0, "end")
        # Application du grid par défaut ou personnalisé
        default_opts = {"row": row, "column": 1, "sticky": "ew", "padx": 5, "pady": 2}
        if grid_options:
            default_opts.update(grid_options)

        date_ent.grid(**default_opts)
        self.vars[key] = var
        self.entries[key] = date_ent
        self._bind_clear_key(key, date_ent)
        return date_ent

    def add_combobox_with_action(self, key, label, action_cmd):
        row = self.next_row()
        ttk.Label(self.form, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)

        frame = ttk.Frame(self.form)
        frame.grid(row=row, column=1, sticky="ew", padx=5, pady=2)
        frame.columnconfigure(0, weight=1)

        var = tk.StringVar()
        combo = ttk.Combobox(frame, textvariable=var, state="readonly")
        combo.grid(row=0, column=0, sticky="ew")

        btn = ttk.Button(frame, text="+", width=3, command=action_cmd)
        btn.grid(row=0, column=1, padx=(5, 0))

        self.vars[key] = var
        self.entries[key] = combo
        self._bind_clear_key(key, combo)
        return combo

    def _on_combobox_selected(self, key, on_select: Callable = None):
        combo = self.entries.get(key)
        idx = combo.current()
        raw_data = getattr(self, f"_raw_data_{key}", [])

        selected_row = None
        if idx != -1:
            if raw_data and idx < len(raw_data):
                # Combobox avec données structurées (liste de dicts avec iid_key)
                selected_row = raw_data[idx]
                setattr(self, f"_selected_key_{key}", selected_row.get("iid_key"))
            else:
                # Combobox de valeurs simples (ex: colonnes de fichier pour le mapping)
                # On retourne la valeur texte directement
                selected_row = self.vars[key].get()

        if on_select:
            on_select(selected_row)

    def add_numeric(self, key, label, row=None, from_=0, to=100, increment=1, grid_options=None):
        """Ajoute un champ numérique avec des flèches de sélection."""
        if row is None: row = self.next_row()
        ttk.Label(self.form, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)

        var = tk.DoubleVar(value=from_)
        # Création de la Spinbox
        spin = ttk.Spinbox(self.form, from_=from_, to=to, increment=increment, textvariable=var)

        # Application du grid
        default_opts = {"row": row, "column": 1, "sticky": "ew", "padx": 5, "pady": 2}
        if grid_options:
            default_opts.update(grid_options)

        spin.grid(**default_opts)

        self.vars[key] = var
        self.entries[key] = spin
        self._bind_clear_key(key, spin)
        return spin

    def add_numeric_calc(self, key, label, row=None, grid_options=None):
        if row is None: row = self.next_row()
        ttk.Label(self.form, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)

        var = tk.StringVar()
        frame = ttk.Frame(self.form)

        entry = ttk.Entry(frame, textvariable=var)
        entry.pack(side="left", fill="x", expand=True)

        # Le bouton "Calc" ouvre la calculatrice
        btn = ttk.Button(frame, text="Σ", width=3,
                         command=lambda: CalculatorPopup(self, var))
        btn.pack(side="right", padx=(2, 0))

        default_opts = {"row": row, "column": 1, "sticky": "ew", "padx": 5, "pady": 2}
        if grid_options: default_opts.update(grid_options)
        frame.grid(**default_opts)

        self.vars[key] = var
        self.entries[key] = entry
        return entry

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
        if not value:
            return None

        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y"):
            try:
                return datetime.strptime(value.split(" ")[0], fmt).date()
            except ValueError:
                continue

        return None

    @staticmethod
    def _format_date_for_storage(value):
        """Convertit une date (JJ/MM/AAAA ou JJ/MM/AA) en format ISO."""
        if value in (None, "", "None"):
            return None

        if isinstance(value, (datetime, date)):
            return value.strftime("%Y-%m-%d")

        value = str(value).strip()
        if not value:
            return None

        clean_val = value.replace(".", "/").replace("-", "/").split(" ")[0]

        if clean_val.isdigit():
            if len(clean_val) == 6:
                clean_val = f"{clean_val[:2]}/{clean_val[2:4]}/{clean_val[4:]}"
            elif len(clean_val) == 8:
                clean_val = f"{clean_val[:2]}/{clean_val[2:4]}/{clean_val[4:]}"

        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y/%m/%d"):
            try:
                return datetime.strptime(clean_val, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue

        return None

    @staticmethod
    def _display_value(value):
        """Retourne un libellé lisible pour les objets et dictionnaires métier."""
        if value in (None, "", "None"):
            return ""

        if isinstance(value, dict):
            return value.get("display_value") or value.get("value") or ""

        for attr in ("display_name", "display_full", "display_tree", "label", "libelle", "value"):
            display = getattr(value, attr, None)
            if display:
                return display

        return str(value)

    @staticmethod
    def _object_key(value):
        """Extrait l'identifiant d'une valeur métier."""
        if isinstance(value, dict):
            for attr in ("iid_key", "id", "id_banque", "id_emetteur", "id_type"):
                key = value.get(attr)
                if key is not None:
                    return key

        for attr in ("id", "id_banque", "id_emetteur", "id_type", "iid_key"):
            key = getattr(value, attr, None)
            if key is not None:
                return key

        return None

    def set_values(self, data: dict):
        """ Méthode mise à jour pour gérer les dates ISO -> FR et les Checkbuttons """
        import copy
        self._form_data = copy.deepcopy(data)

        for key, value in data.items():
            if key in self.vars:
                widget = self.entries.get(key)

                # Si c'est une case à cocher
                if isinstance(widget, ttk.Checkbutton):
                    # Convertit gentiment les 1/0 ou "True"/"False" de la base en vrai booléen
                    if str(value).lower() in ("true", "1", "yes"):
                        self.vars[key].set(True)
                    else:
                        self.vars[key].set(False)

                # Si le widget est une DateEntry, on formate la date
                if isinstance(widget, DateEntry):
                    date_value = self._format_date_for_display(value)
                    if date_value is None:
                        # Vider la StringVar suffit — delete() sur DateEntry n'efface pas l'affichage
                        self.vars[key].set("")
                        widget.delete(0, "end")
                    else:
                        widget.set_date(date_value)

                # Logique standard pour les autres (Entry, Combo)
                elif isinstance(value, list) and isinstance(widget, ttk.Combobox):
                    setattr(self, f"_raw_data_{key}", value)
                    widget["values"] = [item.get("value", "") for item in value]
                    selected_key = getattr(self, f"_selected_key_{key}", None)
                    if selected_key is not None:
                        self.select_combobox_by_key(key, selected_key)
                elif isinstance(value, dict) and "value" in value:
                    selected_key = self._object_key(value)
                    if selected_key is not None:
                        setattr(self, f"_selected_key_{key}", selected_key)

                    display_value = value.get("display_value") or value["value"]
                    self.vars[key].set(display_value)

                    if isinstance(widget, ttk.Combobox):
                        raw_data = getattr(self, f"_raw_data_{key}", [])
                        for index, item in enumerate(raw_data):
                            if item.get("iid_key") == selected_key:
                                widget.current(index)
                                break
                else:
                    if isinstance(widget, ttk.Combobox):
                        selected_key = self._object_key(value)
                        if selected_key is not None:
                            setattr(self, f"_selected_key_{key}", selected_key)
                        elif value in (None, "", "None"):
                            widget.set("")
                            setattr(self, f"_selected_key_{key}", None)
                    self.vars[key].set(self._display_value(value))

    def get_selected_row(self, key):
        """Retourne le dictionnaire 'row' complet correspondant à la sélection."""
        combo = self.entries.get(key)

        if not combo: return None
        # Récupère l'index de l'élément sélectionné
        idx = combo.current()
        raw_data = getattr(self, f"_raw_data_{key}", [])
        if 0 <= idx < len(raw_data):
            return raw_data[idx]

        selected_key = getattr(self, f"_selected_key_{key}", None)
        if selected_key is not None:
            for row in raw_data:
                if str(row.get("iid_key")) == str(selected_key):
                    return row

        return None

    def get_values(self):
        import copy
        result = copy.deepcopy(self._form_data)
        for key, var in self.vars.items():
            widget = self.entries.get(key)
            # Traitement spécifique pour le Checkbutton
            if isinstance(widget, ttk.Checkbutton):
                result[key] = bool(var.get())
                continue  # On passe au champ suivant

            val = var.get().strip()

            # On convertit le vide de l'interface en vrai None pour le code
            final_val = None if val == "" or val.lower() == "none" else val

            if isinstance(widget, DateEntry):
                result[key] = self._format_date_for_storage(val)
            elif isinstance(widget, ttk.Combobox):
                selected_row = self.get_selected_row(key)
                if selected_row:
                    result[key] = copy.deepcopy(selected_row)
                else:
                    result[key] = final_val
            else:
                result[key] = final_val
        return result

    def _clear(self):
        self._form_data = {}
        for key, widget in self.entries.items():
            if isinstance(widget, ttk.Checkbutton):
                self.vars[key].set(False)
            elif isinstance(widget, ttk.Combobox):
                widget.set("")
                self.vars[key].set("")
                setattr(self, f"_selected_key_{key}", None)
            elif isinstance(widget, DateEntry):
                widget.delete(0, "end")
                self.vars[key].set("")
            else:
                widget.delete(0, "end")
                self.vars[key].set("")

    def _clear_widget_value(self, key):
        widget = self.entries.get(key)
        if widget is None:
            return "break"

        if isinstance(widget, ttk.Combobox):
            widget.set("")
            self.vars[key].set("")
            setattr(self, f"_selected_key_{key}", None)
        elif isinstance(widget, ttk.Checkbutton):
            self.vars[key].set(False)  # Décoche la case
        else:
            widget.delete(0, "end")
            self.vars[key].set("")

        return "break"


import tkinter as tk
from tkinter import ttk


class CalculatorPopup(tk.Toplevel):
    def __init__(self, parent, target_var):
        super().__init__(parent)
        self.title("Calculatrice")
        self.target_var = target_var
        self.resizable(False, False)

        self.display = ttk.Entry(self, justify='right')
        self.display.grid(row=0, column=0, columnspan=4, sticky="ew", padx=5, pady=5)

        buttons = [
            '7', '8', '9', '/',
            '4', '5', '6', '*',
            '1', '2', '3', '-',
            'C', '0', '=', '+'
        ]

        row, col = 1, 0
        for btn in buttons:
            ttk.Button(self, text=btn, width=5,
                       command=lambda b=btn: self.on_click(b)).grid(row=row, column=col, padx=2, pady=2)
            col += 1
            if col > 3:
                col = 0
                row += 1

    def on_click(self, char):
        if char == '=':
            try:
                result = eval(self.display.get())
                self.target_var.set(str(result))
                self.destroy()
            except:
                self.display.delete(0, 'end')
                self.display.insert(0, "Erreur")
        elif char == 'C':
            self.display.delete(0, 'end')
        else:
            self.display.insert('end', char)

