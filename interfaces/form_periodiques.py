# -*- coding: utf-8 -*-
####################################
# Projet : CostTracker
# Fichier : interfaces/form_periodiques.py
# Description : Vue principale des charges périodiques avec suivi des échéances
# Date : 23/06/2026     Etat : Stable
####################################

import tkinter as tk
from datetime import date
from tkinter import ttk, messagebox

from _helpers.periodique_helpers import PeriodiqueHelpers
from interfaces_tabs.tabs_periodique_tree import PeriodiqueTree


class PeriodiquesView(tk.Frame):
    def __init__(self, parent, services=None):
        super().__init__(parent)
        parent.winfo_toplevel().title("Périodiques — CostTrackers")

        self.services = services or {}
        self.helpers  = PeriodiqueHelpers(services)
        self.helpers.initialise()

        self._build_widgets()
        self.refresh()

    # ── Construction UI ───────────────────────────────────────────────

    def _build_widgets(self):
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # En-tête
        header = ttk.Frame(self, padding=(10, 8))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)

        ttk.Label(header, text="Charges périodiques", font=("Arial", 16, "bold")).grid(row=0, column=0, sticky="w")

        btn_frame = ttk.Frame(header)
        btn_frame.grid(row=0, column=2, sticky="e")

        ttk.Button(btn_frame, text="🔄 Actualiser",        command=self.refresh).pack(side="left", padx=3)
        ttk.Button(btn_frame, text="✏️ Gérer les charges", command=self._ouvrir_editeur).pack(side="left", padx=3)
        ttk.Button(btn_frame, text="⚡ Générer échéances", command=self._generer_echeances).pack(side="left", padx=3)

        # Arbre principal
        self.tree = PeriodiqueTree(self, callbacks=self._build_callbacks())
        self.tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 8))

        # Pied de page
        footer = ttk.Frame(self, padding=(10, 0, 10, 10))
        footer.grid(row=2, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        self.summary_label = ttk.Label(footer, text="")
        self.summary_label.grid(row=0, column=0, sticky="w")

    def _build_callbacks(self) -> dict:
        return {
            "on_periodique_selected": self._on_select,
            "on_periodique_opened":   self._ouvrir_editeur,
        }

    # ── Chargement ───────────────────────────────────────────────────

    def refresh(self):
        self.helpers.initialise()
        rows = self.helpers.fetch_rows()
        self.tree.insert_rows(rows)

        dues = self.helpers.get_echeances_dues()
        total = len(rows)
        self.summary_label.config(
            text=f"{total} charge(s) — {len(dues)} échéance(s) à traiter"
        )

    # ── Callbacks ─────────────────────────────────────────────────────

    def _on_select(self, row):
        pass  # Sélection simple : pas d'action immédiate

    def _ouvrir_editeur(self, row=None):
        from interfaces_mod.mod_periodique_editor import PeriodiqueEditor
        editor = PeriodiqueEditor(self, services=self.services)
        editor.protocol("WM_DELETE_WINDOW", lambda: self._fermer_editeur(editor))

    def _fermer_editeur(self, editor):
        editor.destroy()
        self.refresh()

    def _generer_echeances(self):
        dues = self.helpers.get_echeances_dues()
        if not dues:
            messagebox.showinfo("Échéances", "Aucune échéance à traiter pour aujourd'hui.")
            return

        noms = "\n".join(f"  • {p.libelle} — {p.date_prochaine}" for p in dues[:10])
        if len(dues) > 10:
            noms += f"\n  … et {len(dues) - 10} autre(s)"

        ok = messagebox.askyesno(
            "Générer les échéances",
            f"{len(dues)} échéance(s) à traiter :\n\n{noms}\n\nAvancer les dates de prochaine échéance ?"
        )
        if not ok:
            return

        for p in dues:
            self.helpers.avancer_echeance(p.id_periodique)

        messagebox.showinfo("Échéances", f"{len(dues)} échéance(s) avancée(s).")
        self.refresh()


# ── Test standalone ───────────────────────────────────────────────────
if __name__ == "__main__":
    from _services._bootstrap_services import build_app_services
    root = tk.Tk()
    root.geometry("1100x450")
    services = build_app_services()
    app = PeriodiquesView(root, services)
    app.pack(fill="both", expand=True)
    root.mainloop()
