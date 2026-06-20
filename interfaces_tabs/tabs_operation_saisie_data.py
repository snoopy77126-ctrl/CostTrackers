import tkinter as tk
from tkinter import ttk
from datetime import datetime

from interfaces_tabs._tabs_generique_data import BaseFormFrame


class OperationSaisieData(BaseFormFrame):
    """
    Formulaire de saisie/édition d'une opération (champs métier).

    Suit l'architecture des autres *_data.py (CompteGeneralData,
    CategorieData, EmetteurData, ...) en héritant de BaseFormFrame.

    Ne gère QUE le formulaire (combobox, entries, montants, dates,
    bloc infos import). Les boutons Debit/Credit/Virement et
    Enregistrer/Annuler restent dans mod_operation_saisie.py
    (orchestration / Toplevel).
    """

    def __init__(self, parent, callbacks=None):
        super().__init__(parent, title="", callbacks=callbacks)

        # Dictionnaires de correspondance value -> id pour les combobox
        self.combo_tiers_data = {}
        self.combo_banque_data = {}
        self.combo_categorie_data = {}

        self.build_widgets()

    # ------------------- Construction UI -------------------
    def build_widgets(self):
        # ==== Formulaire principal ====
        self.frame_form = tk.Frame(self)
        self.frame_form.pack(pady=10, padx=10, fill="x")

        # OperationBase
        tk.Label(self.frame_form, text="OperationBase").grid(row=0, column=0, sticky="w")
        self.combo_operation = ttk.Combobox(self.frame_form, values=["", "Op1", "Op2"], width=25)
        self.combo_operation.grid(row=0, column=1, columnspan=2, sticky="w", pady=2)

        # Tiers / Account
        tk.Label(self.frame_form, text="Tiers").grid(row=1, column=0, sticky="w")
        self.combo_tiers = ttk.Combobox(self.frame_form, values=["", "Client1", "Client2"], width=18)
        self.combo_tiers.grid(row=1, column=1, sticky="w", pady=2)

        tk.Label(self.frame_form, text="Account").grid(row=1, column=2, sticky="w", padx=(10, 0))
        self.combo_banque = ttk.Combobox(self.frame_form, values=["", "Banque1", "Banque2"], width=18)
        self.combo_banque.grid(row=1, column=3, sticky="w", pady=2)

        # Note
        tk.Label(self.frame_form, text="Note").grid(row=2, column=0, sticky="w")
        self.entry_note = tk.Entry(self.frame_form, width=55)
        self.entry_note.grid(row=2, column=1, columnspan=3, sticky="w", pady=2)

        # Categories
        tk.Label(self.frame_form, text="Categories").grid(row=3, column=0, sticky="w")
        self.combo_categorie = ttk.Combobox(self.frame_form, values=["", "Cat1", "Cat2"], width=52)
        self.combo_categorie.grid(row=3, column=1, columnspan=3, sticky="w", pady=2)

        # ==== Montants / Dates ====
        self.frame_bottom = tk.Frame(self)
        self.frame_bottom.pack(padx=10, pady=5, fill="x")

        self.lbl_montant = tk.Label(self.frame_bottom, text="Débit:")
        self.lbl_montant.grid(row=0, column=0, sticky="w")
        self.entry_montant = tk.Entry(self.frame_bottom, width=15, fg="red", bg="#f8f0f0", justify="right")
        self.entry_montant.insert(0, "0,00 €")
        self.entry_montant.grid(row=0, column=1, sticky="w")

        tk.Label(self.frame_bottom, text="Solde").grid(row=0, column=2, sticky="w", padx=(30, 0))
        self.entry_solde = tk.Entry(self.frame_bottom, width=10)
        self.entry_solde.insert(0, "0")
        self.entry_solde.grid(row=0, column=3, sticky="w")

        tk.Label(self.frame_bottom, text="Date").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_date = tk.Entry(self.frame_bottom, width=15)
        self.entry_date.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.entry_date.grid(row=1, column=1, sticky="w")

        self.chk_var = tk.IntVar()
        self.chk_periodique = tk.Checkbutton(
            self.frame_bottom, text="OperationBase Periodique", variable=self.chk_var
        )
        self.chk_periodique.grid(row=1, column=2, columnspan=2, sticky="w")

        # ==== Frame Infos Import (dépliable) ====
        self.frame_import_toggle = tk.BooleanVar(value=False)

        self.frame_import_header = tk.Frame(self)
        self.frame_import_header.pack(padx=10, pady=(0, 2), fill="x")

        self.btn_toggle_import = tk.Button(
            self.frame_import_header,
            text="▶  Infos import bancaire",
            anchor="w",
            relief="flat",
            bg="#dce8f5",
            command=self._toggle_import_frame
        )
        self.btn_toggle_import.pack(fill="x")

        self.frame_import = tk.LabelFrame(self, text="Infos import", padx=8, pady=6)
        # Caché par défaut - champs en lecture seule (infos de l'import d'origine)

        tk.Label(self.frame_import, text="Source").grid(row=0, column=0, sticky="w")
        self.lbl_source = tk.Label(self.frame_import, text="", anchor="w", fg="#555")
        self.lbl_source.grid(row=0, column=1, sticky="w")

        tk.Label(self.frame_import, text="Fichier import").grid(row=1, column=0, sticky="w")
        self.lbl_fichier = tk.Label(self.frame_import, text="", anchor="w", fg="#555")
        self.lbl_fichier.grid(row=1, column=1, sticky="w")

        tk.Label(self.frame_import, text="Libellé original").grid(row=2, column=0, sticky="w")
        self.lbl_libelle_orig = tk.Label(self.frame_import, text="", anchor="w", fg="#555")
        self.lbl_libelle_orig.grid(row=2, column=1, sticky="w")

        tk.Label(self.frame_import, text="Clé import").grid(row=3, column=0, sticky="w")
        self.lbl_import_key = tk.Label(self.frame_import, text="", anchor="w", fg="#555")
        self.lbl_import_key.grid(row=3, column=1, sticky="w")

        tk.Label(self.frame_import, text="Date valeur").grid(row=4, column=0, sticky="w")
        self.lbl_date_valeur = tk.Label(self.frame_import, text="", anchor="w", fg="#555")
        self.lbl_date_valeur.grid(row=4, column=1, sticky="w")

    # ------------------- Toggle bloc import -------------------
    def _toggle_import_frame(self):
        if self.frame_import.winfo_ismapped():
            self.frame_import.pack_forget()
            self.btn_toggle_import.config(text="▶  Infos import bancaire")
        else:
            self.frame_import.pack(padx=10, pady=(0, 5), fill="x", before=self.frame_import_header)
            self.btn_toggle_import.config(text="▼  Infos import bancaire")

    def show_import_frame(self, before_widget=None):
        """Affiche le bloc 'Infos import' (appelé depuis le parent avec un widget de référence)."""
        self.frame_import.pack(padx=10, pady=(0, 5), fill="x", before=before_widget or self.frame_import_header)
        self.btn_toggle_import.config(text="▼  Infos import bancaire")

    # ------------------- Chargement combobox -------------------
    def load_combobox_data(self, tiers_data, comptes_data, categories_data):
        """Charge les listes de valeurs dans les combobox depuis des listes de dicts {id, value}."""
        # Tiers
        self.combo_tiers['values'] = [""] + [t['value'] for t in tiers_data]
        self.combo_tiers_data = {t['value']: t['id'] for t in tiers_data}

        # Comptes
        self.combo_banque['values'] = [""] + [c['value'] for c in comptes_data]
        self.combo_banque_data = {c['value']: c['id'] for c in comptes_data}

        # Catégories
        self.combo_categorie['values'] = [""] + [c['value'] for c in categories_data]
        self.combo_categorie_data = {c['value']: c['id'] for c in categories_data}

    # ------------------- Label dynamique Montant -------------------
    def set_montant_label(self, type_operation: str):
        """
        Adapte le libellé (et la couleur) du champ montant selon le type sélectionné.
        type_operation : 'depense' (Debit) | 'revenu' (Credit) | 'virement' (Virement)
        """
        labels = {
            'depense':  ("Débit:",    "red",   "#f8f0f0"),
            'revenu':   ("Crédit:",   "green", "#f0f8f0"),
            'virement': ("Montant:",  "#2f4f7f", "#eef2f8"),
        }
        text, fg, bg = labels.get(type_operation, labels['depense'])
        self.lbl_montant.config(text=text)
        self.entry_montant.config(fg=fg, bg=bg)

    # ------------------- Set / Get valeurs -------------------
    def set_values_from_operation(self, data: dict):
        """Remplit le formulaire avec les données d'une opération."""
        # Libellé (opération)
        self.combo_operation.set(data.get('libelle', ''))

        # Tiers
        self.combo_tiers.set(data.get('tiers_label', ''))

        # Compte
        self.combo_banque.set(data.get('compte_label', ''))

        # Note
        self.entry_note.delete(0, tk.END)
        self.entry_note.insert(0, data.get('commentaire', ''))

        # Catégorie
        self.combo_categorie.set(data.get('categorie_label', ''))

        # Montant
        montant = data.get('montant', 0.0)
        self.entry_montant.delete(0, tk.END)
        self.entry_montant.insert(0, f"{abs(montant):.2f} €")

        # Date
        date_op = data.get('date_operation', '')
        if date_op:
            self.entry_date.delete(0, tk.END)
            self.entry_date.insert(0, date_op)

        # Infos import (lecture seule)
        self.lbl_source.config(text=data.get('source', ''))
        self.lbl_libelle_orig.config(text=data.get('libelle', ''))
        self.lbl_import_key.config(text=data.get('import_key', ''))
        self.lbl_date_valeur.config(text=data.get('date_valeur', ''))

        # Afficher le cadre si l'opération vient d'un import
        if data.get('source') not in ('saisie', '', None):
            self.show_import_frame()

    def get_form_values(self, type_operation: str) -> dict:
        """
        Récupère les valeurs du formulaire.
        :param type_operation: 'depense' | 'revenu' | 'virement' (déterminé par le parent
                                via le type sélectionné Debit/Credit/Virement).
        """
        # Récupération du montant (champ unique réutilisé : Débit / Crédit / Virement)
        montant_text = self.entry_montant.get().replace('€', '').replace(',', '.').strip()
        try:
            montant = float(montant_text) if montant_text else 0.0
            if type_operation == 'depense':
                montant = -abs(montant)
            else:
                montant = abs(montant)
        except ValueError:
            montant = 0.0

        # Récupération des IDs depuis les combobox
        tiers_value = self.combo_tiers.get()
        tiers_id = self.combo_tiers_data.get(tiers_value) if tiers_value else None

        compte_value = self.combo_banque.get()
        compte_id = self.combo_banque_data.get(compte_value) if compte_value else None

        categorie_value = self.combo_categorie.get()
        categorie_id = self.combo_categorie_data.get(categorie_value) if categorie_value else None

        return {
            'libelle': self.combo_operation.get(),
            'type_operation': type_operation,
            'montant': montant,
            'tiers_id': tiers_id,
            'compte_id': compte_id,
            'categorie_id': categorie_id,
            'commentaire': self.entry_note.get(),
            'date_operation': self.entry_date.get(),
        }

    def _clear(self):
        """Réinitialise le formulaire (valeurs par défaut)."""
        self.combo_operation.set("")
        self.combo_tiers.set("")
        self.combo_banque.set("")
        self.entry_note.delete(0, tk.END)
        self.combo_categorie.set("")

        self.entry_montant.delete(0, tk.END)
        self.entry_montant.insert(0, "0,00 €")
        self.set_montant_label('depense')

        self.entry_solde.delete(0, tk.END)
        self.entry_solde.insert(0, "0")

        self.entry_date.delete(0, tk.END)
        self.entry_date.insert(0, datetime.now().strftime("%d/%m/%Y"))

        self.chk_var.set(0)

        if self.frame_import.winfo_ismapped():
            self.frame_import.pack_forget()
            self.btn_toggle_import.config(text="▶  Infos import bancaire")
