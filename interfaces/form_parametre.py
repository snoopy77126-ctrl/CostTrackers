import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from _services.debug_services import notifier_erreur
from config.config import cfg
from databases.database_manager import DatabaseManager


class Parametrage(tk.Frame):
    def __init__(self, parent, services=None):
        super().__init__(parent)
        self.services = services or {}

        # aligné avec ConfigManager
        self.parametres = [
            ("SRC_DIRECTORY", "Répertoire Source (Vrac)", "str"),
            ("DATABASE_DIRECTORY", "Dossier Base de Données", "str"),
            ("DATABASE_NAME", "Nom Base de Données", "str"),
            ("BACKUP_DIRECTORY", "Répertoire de Sauvegarde", "str"),
        ]

        self.entries = {}
        self.vars_bool = {}

        self.build_widgets()

    # =========================
    # UI BUILD
    # =========================
    def build_widgets(self):
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._build_directory_frame(self).grid(column=0, row=0, rowspan=2, sticky="nsew", padx=5, pady=5)
        self._build_btn_maj_frame(self).grid(column=1, row=0, sticky="new", padx=5, pady=5)
        self._build_btn_frame(self).grid(column=1, row=1, sticky="sew", padx=5, pady=10)

    # =========================
    # DIRECTORY FRAME
    # =========================
    def _build_directory_frame(self, parent):
        frame = ttk.LabelFrame(parent, text="Configuration")

        for i, (cle, label, typ) in enumerate(self.parametres):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", padx=10, pady=5)

            entry = ttk.Entry(frame, state="readonly")
            entry.grid(row=i, column=1, sticky="ew", padx=5)
            self.entries[cle] = entry

            ttk.Button(
                frame,
                text="📂",
                width=3,
                command=lambda c=cle, e=entry: self.choisir_dossier(e, c)
            ).grid(row=i, column=2, padx=5)

        frame.columnconfigure(1, weight=1)
        self.after(100, lambda: self._charger_valeurs())
        return frame

    # =========================
    # MAINTENANCE DB
    # =========================
    def _build_btn_maj_frame(self, parent):
        frame = ttk.LabelFrame(parent, text="Maintenance Base")

        ttk.Button(
            frame,
            text="🔄 Sync DB",
            command=self._sync_db
        ).pack(fill="x", padx=10, pady=5)

        ttk.Button(
            frame,
            text="🔄 Init DB",
            command=self._init_db
        ).pack(fill="x", padx=10, pady=5)

        return frame

    # =========================
    # ACTION BUTTONS
    # =========================
    def _build_btn_frame(self, parent):
        frame = ttk.LabelFrame(parent, text="Actions")
        ttk.Button(frame, text="💾 Sauvegarder", command=self._sauvegarder).pack(fill="x", padx=10, pady=5)
        ttk.Button(frame, text="🔄 Recharger", command=self._charger_valeurs).pack(fill="x", padx=10, pady=5)
        return frame

    def _sync_db(self):
        try:
            db_manager = DatabaseManager(cfg)
            db_manager.init_database()
            messagebox.showinfo("Succès", "Structure de la base synchronisée.")
        except Exception as e:
            notifier_erreur("Erreur Sync DB", "Impossible de synchroniser la base", e)

    def _init_db(self):
        """Réinitialise uniquement la table des fichiers après confirmation."""
        confirm = messagebox.askyesno(
            "Confirmation",
            "Cette action va supprimer tous les fichiers référencés en base.\n"
            "Les documents sur disque ne seront pas supprimés.\n\n"
            "Continuer ?"
        )
        if not confirm:
            return

        try:
            db_manager = DatabaseManager(cfg)
            with db_manager.get_connection() as conn:
                conn.execute("DELETE FROM fichiers")
                conn.commit()

            messagebox.showinfo("Succès", "Table fichiers réinitialisée.")
        except Exception as e:
            notifier_erreur("Erreur Init DB", "Impossible de réinitialiser la table fichiers", e)

    # =========================
    # SAVE CONFIG
    # =========================
    def _sauvegarder(self):
        try:
            for cle, _, _ in self.parametres:
                val = self.entries[cle].get().strip()
                cfg.set(cle, val)

            db_dir = cfg.get("DATABASE_DIRECTORY", "")
            db_name = cfg.get("DATABASE_NAME", "")
            if db_dir and db_name:
                cfg.set("DATABASE_DB", os.path.normpath(os.path.join(db_dir, db_name)))

            cfg.save()
            cfg.load()

            messagebox.showinfo("Succès", "Configuration enregistrée.")

        except Exception as e:
            notifier_erreur("Erreur sauvegarde", "Impossible d'écrire la config", e)

    # =========================
    # LOAD CONFIG
    # =========================
    def _charger_valeurs(self):
        try:
            for cle, _, _ in self.parametres:
                val = cfg.get(cle, "")

                entry = self.entries.get(cle)
                if entry:
                    entry.config(state="normal")
                    entry.delete(0, tk.END)
                    entry.insert(0, str(val))
                    entry.config(state="readonly")

        except Exception as e:
            print(f"Erreur chargement config : {e}")

    # =========================
    # ACTIONS
    # =========================
    def choisir_dossier(self, entry_widget, config_key):
        init_dir = cfg.get("DATABASE_DIRECTORY", os.getcwd()) if config_key == "DATABASE_NAME" else os.getcwd()

        if config_key == "DATABASE_NAME":
            path = filedialog.asksaveasfilename(
                title=config_key,
                initialdir=init_dir,
                initialfile=cfg.get("DATABASE_NAME", "GEDviaGPT.db"),
                defaultextension=".db",
                filetypes=[("SQLite DB", "*.db")]
            )
        else:
            path = filedialog.askdirectory(title=config_key, initialdir=init_dir)

        if path:
            path = os.path.normpath(path)
            value = os.path.basename(path) if config_key == "DATABASE_NAME" else path
            entry_widget.config(state="normal")
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, value)
            entry_widget.config(state="readonly")

            if config_key == "DATABASE_NAME":
                db_dir_entry = self.entries.get("DATABASE_DIRECTORY")
                if db_dir_entry:
                    db_dir_entry.config(state="normal")
                    db_dir_entry.delete(0, tk.END)
                    db_dir_entry.insert(0, os.path.dirname(path))
                    db_dir_entry.config(state="readonly")
