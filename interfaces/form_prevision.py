import tkinter as tk
from datetime import date
from tkinter import ttk, messagebox

from interfaces_tabs.tabs_prevision_button import PrevisionButton
from interfaces_tabs.tabs_prevision_data import PrevisionData



class PrevisionView(tk.Frame):

    def __init__(self, parent, services=None):
        super().__init__(parent)
        parent.winfo_toplevel().title("Périodiques — CostTrackers")

        self.services = services or {}
        self.callbacks = self._build_callbacks()
        self._build_widgets()

    # ── Construction UI ───────────────────────────────────────────────

    def _build_widgets(self):
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)


        # En-tête
        header = ttk.Frame(self, padding=(10, 8))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)

        ttk.Label(header, text="Charges périodiques", font=("Arial", 16, "bold")).grid(row=0, column=0, sticky="w")

        self.paned_button = PrevisionButton(self, callbacks=self.callbacks)
        self.paned_button.grid(row=0, column=0, sticky="ew", padx=8, pady=8)

        # 2. Zone centrale mobile (PanedWindow)
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))


        # Injection des sous-sections dans le PanedWindow
        paned.add(self._build_left_side(paned), weight=1)  # Partie gauche (Arbre)
        paned.add(self._build_right_side(paned), weight=2)  # Partie droite (Mapping + Aperçu)

    def _build_left_side(self, parent_pane):
        self.data_frame = PrevisionData(parent_pane, controller=self.callbacks)
        return self.data_frame

    def _build_right_side(self, parent_pane):
        self.data_frame = PrevisionData(parent_pane, controller=self.callbacks)
        return self.data_frame


    def _build_callbacks(self):
        return {
        }

# ── Test standalone ───────────────────────────────────────────────────
if __name__ == "__main__":
    from _services._bootstrap_services import build_app_services
    root = tk.Tk()
    root.geometry("1100x450")
    services = build_app_services()
    app = PrevisionView(root, services)
    app.pack(fill="both", expand=True)
    root.mainloop()