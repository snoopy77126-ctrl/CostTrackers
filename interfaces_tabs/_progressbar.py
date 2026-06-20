"""
Projet : CostTracker
Fichier : tiers_helpers/_progressbar.py
  - ProgressBarAuto : se ferme automatiquement à 100%.
  - ProgressBarConfirm : nécessite une confirmation après 100% avec affichage d'informations.

Utilisation depuis un autre module :
-----------------------------------
from utils.progress_bar_module import ProgressBarAuto, ProgressBarConfirm

# Exemple ProgressBarAuto
auto = ProgressBarAuto(title="Chargement en cours", max_value=100)
auto.start()
for i in range(101):
    auto.update_progress(i)

# Exemple ProgressBarConfirm
confirm = ProgressBarConfirm(title="Traitement de données", max_value=100)
confirm.start()
for i in range(101):
    confirm.update_progress(i)
"""
import threading
import time
import tkinter as tk
from tkinter import ttk


class ProgressBarAuto:
    def __init__(self, title="Progression", max_value=100):
        self.root = tk.Toplevel()
        self.root.title(title)
        self.root.geometry("400x100")
        self.root.resizable(False, False)

        ttk.Label(self.root, text=title, font=("Arial", 10, "bold")).pack(pady=10)

        self.progress = ttk.Progressbar(self.root, length=300, mode="determinate", maximum=max_value)
        self.progress.pack(pady=10)

        self.max_value = max_value
        self.value = 0

    def start(self):
        self.root.update()

    def update_progress(self, value):
        self.value = value
        self.progress["value"] = value
        self.root.update_idletasks()
        if value >= self.max_value:
            self.close()

    def close(self):
        self.root.destroy()


class ProgressBarConfirm:
    def __init__(self, title="Progression avec confirmation", max_value=100,
                 info_message="Opération terminée avec succès."):
        self.root = tk.Toplevel()
        self.root.title(title)
        self.root.geometry("400x150")
        self.root.resizable(False, False)

        ttk.Label(self.root, text=title, font=("Arial", 10, "bold")).pack(pady=10)

        self.progress = ttk.Progressbar(self.root, length=300, mode="determinate", maximum=max_value)
        self.progress.pack(pady=10)

        self.info_label = ttk.Label(self.root, text="", foreground="green")
        self.info_label.pack(pady=5)

        self.confirm_button = ttk.Button(self.root, text="Fermer", command=self.close, state="disabled")
        self.confirm_button.pack(pady=5)

        self.max_value = max_value
        self.value = 0
        self.info_message = info_message

    def start(self):
        self.root.update()

    def update_progress(self, value):
        self.value = value
        self.progress["value"] = value
        self.root.update_idletasks()

        if value >= self.max_value:
            self.show_confirmation()

    def show_confirmation(self):
        self.info_label.config(text=self.info_message)
        self.confirm_button.config(state="normal")
        self.root.update()

    def close(self):
        self.root.destroy()


# Exemple exécution directe pour test
if __name__ == "__main__":
    def run_auto():
        auto = ProgressBarAuto(title="Chargement automatique", max_value=100)
        auto.start()
        for i in range(101):
            time.sleep(0.02)
            auto.update_progress(i)


    def run_confirm():
        confirm = ProgressBarConfirm(title="Chargement avec confirmation", max_value=100)
        confirm.start()
        for i in range(101):
            time.sleep(0.02)
            confirm.update_progress(i)


    root = tk.Tk()
    root.withdraw()

    threading.Thread(target=run_auto).start()
    time.sleep(3)
    threading.Thread(target=run_confirm).start()

    root.mainloop()

