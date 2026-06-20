import tkinter as tk
from datetime import date
from tkinter import ttk

from _helpers.operation_view_helpers import OperationsViewHelpers
from interfaces_mod.mod_operation_saisie import OperationSaisie
from interfaces_tabs._tabs_graf import TabsGraf
from interfaces_tabs.tabs_operation_view_data import CompteFiltreData
from interfaces_tabs.tabs_operation_view_tree import OperationTree



class OperationsView(tk.Frame):
    def __init__(self, parent, services=None):
        super().__init__(parent)
        fenetre_principale = parent.winfo_toplevel()
        fenetre_principale.title("Livre de comptes - Gestion Financière")

        self.services = services or {}
        self.helpers = OperationsViewHelpers(self.services)

        self.callbacks = self.menu_callback()

        self.helpers.initialise()
        self.build_widgets()
        self.refresh()

    def build_widgets(self):
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)

        header = ttk.Frame(self, padding=(10, 8))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)
        ttk.Label(header, text="Livre de comptes", font=("Arial", 16, "bold")).grid(row=0, column=0, sticky="w")

        self.filtre_frame = CompteFiltreData(header, callbacks=self.callbacks)
        self.filtre_frame.grid(row=0, column=0, sticky="w")

        ttk.Button(header, text="Actualiser", command=self.refresh).grid(row=0, column=2, sticky="e")

        self.graph = TabsGraf(self, title="Evolution du solde", height=160)
        self.graph.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))

        self.operation_tree = OperationTree(
            self,
            callbacks=self.callbacks
        )
        self.operation_tree.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 8))

        footer = ttk.Frame(self, padding=(10, 0, 10, 10))
        footer.grid(row=3, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        self.total_label = ttk.Label(footer, text="")
        self.total_label.grid(row=0, column=1, sticky="e")

    # ---- Centralisation des appels conforme à vos autres formulaires ----
    def menu_callback(self):
        """Aiguille l'action demandée par les boutons vers la bonne méthode interne."""
        return {
            "on_operation_selected": self._on_operation_selected,
            "on_operation_opened": self._on_operation_opened,
            "on_compte_change": self.refresh,
            "on_periode_change": self.refresh,
        }

    def _on_operation_opened(self, row):
        """Action par défaut au double-clic (ex: ouvrir le document)."""
        selected_key = row["iid_key"]
        editor_modal = OperationSaisie(
            self,
            self.services,
            selected_key=selected_key,
            on_save_callback=lambda: self.refresh_operation_tree(selected_key=None)
        )

        # 2. On attend que la fenêtre soit détruite
        self.wait_window(editor_modal)

        # 3. Une fois fermée, on rafraîchit l'arbre des fichiers
        # On utilise 'tous' ou la clé actuellement sélectionnée si tu l'as stockée
        self.refresh()

    def refresh(self, row=None):

        if not hasattr(self, "_filtres_init"):
            self._init_filtres()

        filtre = self.filtre_frame.get_values()
        compte_data = filtre.get("compte", {})
        periode_data = filtre.get("periode", {})

        selected_compte_key = compte_data.get("iid_key") if isinstance(compte_data, dict) else "tlc"
        selected_compte_value = compte_data.get("value") if isinstance(compte_data, dict) else "Tous les comptes"
        selected_periode_key = periode_data.get("iid_key") if isinstance(periode_data, dict) else "mois_courant"

        rows_objets = self.helpers.get_filtered_rows(
            compte_key=selected_compte_key,
            compte_value=selected_compte_value,
            periode_key=selected_periode_key
        )
        rows_dicts = []
        for obj in rows_objets:
            # On récupère le dict depuis l'objet
            d = obj.to_dict() if hasattr(obj, 'to_dict') else vars(obj)

            # On ajoute la clé pour le Treeview si elle manque
            d["iid_key"] = getattr(obj, 'id_import_ligne', None)
            d["objet"] = obj  # Indispensable pour garder l'objet en mémoire
            rows_dicts.append(d)

        self.operation_tree.insert_rows(rows_dicts)

        points = self.helpers.tresorerie_points(rows=rows_dicts)
        self.graph.set_points(points)

        somme_filtree = sum(float(row["objet"].montant or 0) for row in rows_dicts)

        if selected_compte_key == "tlc" and selected_periode_key != "tous":
            texte = f"Mouvement sur la période : {self.helpers.money(somme_filtree)}"
        else:
            # Idéalement, ici tu devrais afficher le vrai solde du compte sélectionné
            texte = f"Mouvement total : {self.helpers.money(somme_filtree)}"

        self.total_label.config(text=texte)

    def _init_filtres(self):
        periodes = [
            {"iid_key": "toutesdates", "value": "Toutes les dates"},
            {"iid_key": "mois_courant", "value": "Mois en cours"},
            {"iid_key": "mois_precedent", "value": "Mois précédent"},
            {"iid_key": "3_mois", "value": "3 derniers mois"},
            {"iid_key": "annee_courante", "value": "Année en cours"},
            {"iid_key": "annee_precedente", "value": "Année précédente"},
        ]
        comptes = [{"iid_key": "tlc", "value": "Tous les comptes"}] + self.helpers.compte_rows()

        self.filtre_frame.set_values({"compte": comptes, "periode": periodes})
        self.filtre_frame.select_combobox_by_key("compte", "tlc")
        self.filtre_frame.select_combobox_by_key("periode", "mois_courant")
        self._filtres_init = True

    def _on_operation_selected(self, row):
        print(f'[DEBUG]OperationView:_on_operation_selected')
        print(f'[DEBUG]row: {row}')
