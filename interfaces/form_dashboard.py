import tkinter as tk


class Dashboard(tk.Frame):
    def __init__(self, parent, services=None):
        super().__init__(parent)
        fenetre_principale = parent.winfo_toplevel()
        fenetre_principale.title("Dashboard - Gestion Financière")
        self.services = services
        # Construction UI
        self.build_widgets()

    # ------------------- Construction UI -------------------
    def build_widgets(self):
        """Orchestrateur principal de la vue."""
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        frame = tk.Frame(self, bg="#f0f0f0")
        frame.pack(fill="both", expand=True)

        # Titre
        label = tk.Label(
            frame,
            text="Bienvenue",
            font=("Arial", 18, "bold"),
            bg="#f0f0f0"
        )
        label.pack(pady=30)

        # Description
        desc = tk.Label(
            frame,
            text="Sélectionnez une option dans le menu pour commencer.",
            bg="#f0f0f0"
        )
        desc.pack(pady=10)
