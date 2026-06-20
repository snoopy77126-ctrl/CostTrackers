# interfaces_tabs/tabs_compte_editor_data.py
import copy
from tkinter import ttk

from tkcalendar import DateEntry
from interfaces_tabs._tabs_generique_data import BaseFormFrame


class CompteGeneralData(BaseFormFrame):
    def __init__(self, parent, callbacks=None):
        super().__init__(parent, title="Informations du Compte", callbacks=callbacks)
        self.build_widgets()

    def build_widgets(self):
        self.add_combobox("type_compte", "Type de Compte :")
        self.add_combobox_with_action("banque", "Etabl. rattachée :","add_new_banque")
        self.add_entry("nom_du_compte", "Nom du compte (ex: Courant Joint) :")
        self.add_entry("identifiant", "Numéro du compte :")
        self.add_entry("description", "Notes / Description :")
        self.add_date("date_ouverture", "Date Ouverture:")
        self.add_date("date_cloture", "Date Cloture :")
        self.add_checkbox("cache_le_compte", "Masque le compte")

    def set_values(self, data: dict):
        self._snapshot = copy.deepcopy(data)
        data = data.copy()

        banque = data.get("banque")

        # Si 'banque' est un dictionnaire de données du compte (pas la liste d'initialisation)
        if isinstance(banque, dict):
            raw_id = self._object_key(banque)

            if raw_id is not None:
                # On construit proprement l'identifiant attendu ("bank_1", "bank_2"...)
                banque_id = f"bank_{raw_id}"

                # On stocke la clé sélectionnée pour que le moteur générique la retrouve
                setattr(self, "_selected_key_banque", banque_id)

            # On retire momentanément 'banque' de data pour éviter que le comportement par
            # défaut de super().set_values ne vienne casser l'affichage (car pas de clé 'value')
            del data["banque"]

        # Appel au parent pour remplir tous les autres champs (nom, numéro, etc.)
        super().set_values(data)

        # Maintenant que les données brutes de la combobox sont en place dans le composant,
        # on force l'index visuel sur la bonne banque
        selected_key = getattr(self, "_selected_key_banque", None)
        if selected_key:
            self.select_combobox_by_key("banque", selected_key)

        # Synchronisation de la combobox Type de compte
        type_compte_id = data.get("type_compte_id")
        if type_compte_id is not None:
            self.select_combobox_by_key("type_compte", f"type_{type_compte_id}")

    def get_values(self):
        """ Récupère les données de l'UI fusionnées avec le snapshot d'origine """
        ui_data = super().get_values()

        if not hasattr(self, '_snapshot') or self._snapshot is None:
            self._snapshot = {}
        objet_complet = copy.deepcopy(self._snapshot)

        for cle, valeur in ui_data.items():
            if cle == "selected_file":
                continue

            if isinstance(valeur, dict):
                # Récupération de la clé brute (ex: 'bank_1' ou 'type_2')
                raw_key = str(valeur.get('iid_key') or valeur.get('id') or '')

                # Extraction sécurisée de l'ID numérique à la fin de la chaîne
                if "_" in raw_key:
                    parts = raw_key.rsplit("_", 1)
                    valeur_id = int(parts[-1]) if parts[-1].isdigit() else None
                else:
                    valeur_id = int(raw_key) if raw_key.isdigit() else None

                # Mapping direct vers les champs attendus par le CompteTracker
                if cle == "banque":
                    # On passe un dictionnaire simplifié avec l'ID extrait et sa valeur textuelle
                    objet_complet["banque"] = {
                        "id_banque": valeur_id,
                        "label": valeur.get("value")
                    }
                elif cle == "type_compte":
                    objet_complet["type_compte_id"] = valeur_id
            else:
                # Champs standards (textes, dates, booléens)
                objet_complet[cle] = valeur

        return objet_complet


class BanquesoldeData(BaseFormFrame):
    def __init__(self, parent, callbacks=None):
        super().__init__(parent, title="Soldes & Seuils", callbacks=callbacks)
        self.build_widgets()

    def build_widgets(self):
        self.add_entry("solde_init", "Solde initial :")
        self.add_entry("solde_min", "Solde min :")
        self.add_entry("solde_max", "Solde max :")
        self.add_entry("decouvert_autorise", "Solde autorisé :")

    def get_values(self):
        import copy
        # AVANT : result = copy.deepcopy(self._form_data)
        # C'est cette ligne qui embarquait tout le snapshot et causait les écrasements !

        # APRÈS : On repart d'un dictionnaire vide pour ne renvoyer QUE les widgets de cet onglet
        result = {}

        # Si vous avez besoin de conserver absolument l'ID du compte ou des clés cachées :
        if "id_compte" in self._form_data:
            result["id_compte"] = self._form_data["id_compte"]

        for key, var in self.vars.items():
            widget = self.entries.get(key)
            if isinstance(widget, ttk.Checkbutton):
                result[key] = bool(var.get())
                continue

            val = var.get().strip()
            final_val = None if val == "" or val.lower() == "none" else val

            if isinstance(widget, DateEntry):
                result[key] = self._format_date_for_storage(val)
            elif isinstance(widget, ttk.Combobox):
                selected_row = self.get_selected_row(key)
                if isinstance(selected_row, dict):
                    result[key] = copy.deepcopy(selected_row)
                else:
                    selected_key = getattr(self, f"_selected_key_{key}", None)
                    result[key] = selected_key if selected_key is not None else final_val
            else:
                result[key] = final_val

        return result

class BanqueoptionData(BaseFormFrame):
    def __init__(self, parent, callbacks=None):
        super().__init__(parent, title="Options Avancées", callbacks=callbacks)
        self.build_widgets()

    def build_widgets(self):
        self.add_date("date_der_rapprochement", "Dernier rapprochement le :")
        self.add_entry("taux_interet", "Taux d'intérêt Debiteur (%) :")
        self.add_entry("taux_interet", "Taux d'intérêt Créditeur (%) :")
        self.add_checkbox("object_epargne", "", "Inclure dans les objectif d'Epargne")
        self.add_checkbox("compte_favori", "","Ajoute au favori")
        # Vous pouvez rajouter d'autres éléments ici

    def get_values(self):
        import copy
        # AVANT : result = copy.deepcopy(self._form_data)
        # C'est cette ligne qui embarquait tout le snapshot et causait les écrasements !

        # APRÈS : On repart d'un dictionnaire vide pour ne renvoyer QUE les widgets de cet onglet
        result = {}

        # Si vous avez besoin de conserver absolument l'ID du compte ou des clés cachées :
        if "id_compte" in self._form_data:
            result["id_compte"] = self._form_data["id_compte"]

        for key, var in self.vars.items():
            widget = self.entries.get(key)
            if isinstance(widget, ttk.Checkbutton):
                result[key] = bool(var.get())
                continue

            val = var.get().strip()
            final_val = None if val == "" or val.lower() == "none" else val

            if isinstance(widget, DateEntry):
                result[key] = self._format_date_for_storage(val)
            elif isinstance(widget, ttk.Combobox):
                selected_row = self.get_selected_row(key)
                if isinstance(selected_row, dict):
                    result[key] = copy.deepcopy(selected_row)
                else:
                    selected_key = getattr(self, f"_selected_key_{key}", None)
                    result[key] = selected_key if selected_key is not None else final_val
            else:
                result[key] = final_val

        return result
