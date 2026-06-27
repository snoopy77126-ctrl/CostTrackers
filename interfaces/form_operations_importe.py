import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

from _helpers.operations_import_helpers import OperationsImportHelpers
from _services.debug_services import notifier_erreur
from interfaces_tabs.tabs_operation_import_button import OperationImportButton
from interfaces_tabs.tabs_operation_import_data import OperationImportData
from interfaces_tabs.tabs_operation_import_tree import OperationTree


class OperationsImport(tk.Frame):
    def __init__(self, parent, services=None):
        super().__init__(parent)
        fenetre_principale = parent.winfo_toplevel()
        fenetre_principale.title("OperationsImport - Import bancaire")

        self.services = services or {}
        self.helpers = OperationsImportHelpers(self.services)

        self.callbacks = self.menu_callbacks()

        self.file_rows = {}
        self.file_errors = {}
        self.mapping_vars = {}
        self.mapping_combos = {}
        self.selected_file = None

        self.status_var = tk.StringVar()

        self._build_widgets()
        self.reload()

    def _build_widgets(self):
        # Configuration de la grille principale (self)
        self.rowconfigure(1, weight=1)  # Seul le contenu principal (PanedWindow) s'étire verticalement
        self.columnconfigure(0, weight=1)

        # 1. Barre d'outils (Boutons en haut)
        self.paned_button = OperationImportButton(self, callbacks=self.callbacks)
        self.paned_button.grid(row=0, column=0, sticky="ew", padx=8, pady=8)

        # 2. Zone centrale mobile (PanedWindow)
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        # Injection des sous-sections dans le PanedWindow
        paned.add(self._build_left_side(paned), weight=1)  # Partie gauche (Arbre)
        paned.add(self._build_right_side(paned), weight=2)  # Partie droite (Mapping + Aperçu)

        # 3. Barre d'état (En bas)
        status_bar = ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w", padding=(6, 3))
        status_bar.grid(row=2, column=0, sticky="ew")

    def _build_left_side(self, parent_pane):
        """Crée et retourne le bloc gauche (Arbre des fichiers)"""
        frame = ttk.Frame(parent_pane, padding=(0, 0, 8, 0))
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.files_tree = OperationTree(frame, callbacks=self.callbacks)
        self.files_tree.grid(row=0, column=0, sticky="nsew")
        return frame

    def _build_right_side(self, parent_pane):
        """Crée et retourne le bloc droit (Formulaire + Aperçu)"""
        frame = ttk.Frame(parent_pane)
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)

        # Remplacement de l'ancien _build_mapping_combos par le formulaire
        target_cols = self.helpers.get_target_columns()
        self.mapping_form = OperationImportData(
            frame,
            callbacks=self.callbacks,
            target_columns=target_cols
        )
        self.mapping_form.grid(row=0, column=0, sticky="ew")
        # Section 2 : Aperçu du tableau
        preview_frame = ttk.LabelFrame(frame, text="Aperçu du fichier", padding=8)
        preview_frame.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        preview_frame.rowconfigure(0, weight=1)
        preview_frame.columnconfigure(0, weight=1)

        self.preview_tree = ttk.Treeview(preview_frame, show="headings")
        self.preview_tree.grid(row=0, column=0, sticky="nsew")

        preview_scroll = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview_tree.yview)
        preview_scroll.grid(row=0, column=1, sticky="ns")
        self.preview_tree.configure(yscrollcommand=preview_scroll.set)

        return frame

    def menu_callbacks(self):
        return {
            "on_file_selected": self._on_file_selected_from_tree,
            "test_selected_file": self._test_selected_file,
            "import_selected_file": self._import_selected_file,
        }

    def reload(self):
        nb_saisies, nb_imports = self.helpers.get_status_counters()
        self.status_var.set(f"{nb_saisies} opérations | {nb_imports} lignes bancaires")
        self._load_files()

    def _load_files(self):
        # 1. On vide proprement l'affichage et le cache local
        self.files_tree.clear()
        self.file_rows.clear()

        # On prépare la liste de dictionnaires formatée pour le TreeView générique
        rows_to_insert = []

        for row in self.helpers.list_files():
            path = row["path"]
            status = row["status"]

            # Gestion du nombre de lignes pour éviter l'affichage vide ''
            # Si le parser ou la BDD fournit le nombre de lignes, on l'utilise, sinon on met 0 ou "--"
            nb_lignes = row.get("rows")
            if nb_lignes == "" or nb_lignes is None:
                nb_lignes = "--"  # Plus propre visuellement pour un fichier non encore lu

            # Détermination du statut visuel et du tag de couleur
            tag = "pending"
            label = "À importer"

            if path in self.file_errors:
                tag = "error"
                label = "Erreur"
                row["message"] = self.file_errors[path]
            elif status == "deja_importe":
                tag = "imported"
                label = "Déjà importé"
                # Si le fichier est déjà en BDD, on s'assure d'avoir son vrai compteur
                if row.get("rows"):
                    nb_lignes = row["rows"]

            # On prépare les données attendues par la classe mère FlatTree
            row["iid_key"] = path  # Clé unique (chemin absolu)
            row["filename"] = row["filename"]  # Première colonne principale (Nom du fichier)
            row["label"] = label
            row["format"] = row["format"].upper()
            row["nb_lignes"] = nb_lignes
            row["actif"] = True  # Évite le style grisé par défaut
            row["tags"] = (tag,)  # Applique vos couleurs (error=rouge, imported=vert)
            # Sauvegarde dans le cache local et ajout à la liste d'insertion
            self.file_rows[path] = row
            rows_to_insert.append(row)

        # 2. Injection finale des données dans le TreeView
        self.files_tree.insert_rows(rows_to_insert)

    def _on_file_selected_from_tree(self, row_data):
        selection = self.files_tree.tree.selection()
        if not selection:
            return
        self.selected_file = selection[0]
        self._load_preview(self.selected_file)

    def _load_preview(self, path):
        try:
            preview = self.helpers.preview_file(path)
        except Exception as exc:
            self._mark_file_error(path, str(exc))
            self._clear_mapping()
            self._clear_preview()
            self.status_var.set(f"Erreur lecture : {Path(path).name}")
            return

        self.file_errors.pop(path, None)
        self._set_mapping_columns(preview["columns"], preview["mapping"])
        self._set_preview_rows(preview["columns"], preview["rows"])
        self.status_var.set(f"{preview['filename']} | {preview['row_count']} lignes détectées")

    def _set_mapping_columns(self, columns, mapping):
        values = [""] + list(columns)

        # Stocker la liste complète pour que _refresh_available_columns puisse y accéder
        self.mapping_form._all_columns = values

        if hasattr(self.mapping_form, 'entries'):
            for target, widget in self.mapping_form.entries.items():
                if hasattr(widget, "widgetName") and "combobox" in widget.widgetName:
                    widget["values"] = values

        for target, var in self.mapping_form.vars.items():
            selected = mapping.get(target, "")
            var.set(selected if selected in columns else "")

        # Appliquer le filtre immédiatement avec le mapping initial
        self.mapping_form._refresh_available_columns()

    def _clear_mapping(self):
        for var in self.mapping_form.vars.values():
            var.set("")
        for target, widget in self.mapping_form.entries.items():
            if hasattr(widget, "widgetName") and "combobox" in widget.widgetName:
                widget["values"] = [""]

    def _set_preview_rows(self, columns, rows):
        self._clear_preview()

        if not columns or not rows:
            return

        display_columns = list(columns[:8])
        self.preview_tree["columns"] = display_columns

        for column in display_columns:
            self.preview_tree.heading(column, text=column)
            self.preview_tree.column(column, width=130, stretch=True)

        for row in rows:
            # On s'assure que row est bien un dictionnaire et qu'on récupère les valeurs
            values = [str(row.get(column, "")) for column in display_columns]
            self.preview_tree.insert("", "end", values=values)

    def _clear_preview(self):
        self.preview_tree.delete(*self.preview_tree.get_children())
        self.preview_tree["columns"] = ()

    def _current_mapping(self):
        return {target: var.get() for target, var in self.mapping_form.vars.items() if var.get()}

    def _test_selected_file(self):
        path = self._require_selected_file()
        if not path:
            return
        self._load_preview(path)
        if path not in self.file_errors:
            messagebox.showinfo("Test fichier", "Lecture du fichier OK.")

    def _import_selected_file(self):
        path = self._require_selected_file()
        if not path:
            return
        try:
            # CORRECTION : On passe 'self' en premier argument pour le 'parent_window'
            result = self.helpers.import_file(self, path, self._current_mapping())
        except Exception as exc:
            # 1. On extrait dynamiquement le fichier et la ligne pour enrichir le titre/message
            tb = exc.__traceback__
            while tb.tb_next:
                tb = tb.tb_next  # On descend au niveau le plus profond de l'erreur

            cadre = tb.tb_frame
            nom_fichier = cadre.f_code.co_filename
            num_ligne = tb.tb_lineno
            nom_fonction = cadre.f_code.co_name

            # 2. On centralise via votre service (Log + Print console automatique si DEBUG=True)
            titre_erreur = f"Erreur Import ({nom_fonction})"
            message_erreur = f"{str(exc)}\n\nFichier: {nom_fichier}\nLigne: {num_ligne}"

            notifier_erreur(
                titre=titre_erreur,
                message=message_erreur,
                exception=exc,
                afficher=messagebox.showerror  # Passé en callback pour la PROD (quand DEBUG = False)
            )

            # 3. Mettre à jour l'interface locale si nécessaire
            msg_court = f"{str(exc)} (Ligne {num_ligne})"
            self._mark_file_error(path, msg_court)
            return

        if result.get("errors"):
            msg = "\n".join(result["errors"])
            self._mark_file_error(path, msg)
            messagebox.showerror("Erreur import", msg)
            return

        self.file_errors.pop(path, None)
        self.reload()
        messagebox.showinfo(
            "Importation réussie",
            f"Fichier : {Path(path).name}\n"
            f"Lignes importées : {result.get('rows', 0)}\n"
            f"Lignes ignorées : {result.get('ignored', 0)}"
        )

    def import_folder(self):
        try:
            summary = self.helpers.import_folder()
            for error in summary["errors"]:
                filename = error.split(":", 1)[0]
                for path, row in self.file_rows.items():
                    if row["filename"] == filename:
                        self.file_errors[path] = error
            self.reload()
            messagebox.showinfo("Import terminé",
                                f"Dossier traité.\nFichiers lus : {summary['files']}\nLignes insérées : {summary['rows']}")
        except Exception as exc:
            messagebox.showerror("Erreur dossier", str(exc))

    def _require_selected_file(self):
        selection = self.files_tree.tree.selection()
        return selection[0] if selection else (messagebox.showwarning("Fichier", "Sélectionnez un fichier."), None)[1]

    def _mark_file_error(self, path, message):
        self.file_errors[path] = message

        # 1. Mise à jour du cache de données pour que le prochain reload() soit cohérent
        if path in self.file_rows:
            self.file_rows[path]["label"] = "Erreur"
            self.file_rows[path]["tags"] = ("error",)

        # 2. Mise à jour visuelle du widget TreeView
        if self.files_tree.tree.exists(path):
            # On récupère les valeurs actuelles
            values = list(self.files_tree.tree.item(path, "values"))

            # Index 1 correspond à la colonne 'label' selon votre structure _load_files
            if len(values) >= 2:
                values[1] = "Erreur"

                # Application des nouvelles valeurs et du TAG 'error'
            self.files_tree.tree.item(path, values=tuple(values), tags=("error",))

            # 3. CRUCIAL : Forcer la mise à jour des couleurs liées aux tags
            # Si votre classe OperationTree ne le fait pas, le tag reste ignoré
            self.files_tree.tree.tag_configure("error", foreground="red")