# -*- coding: utf-8 -*-
import logging
import os
import tkinter as tk

from PIL import Image, ImageTk

from _services._bootstrap_services import build_app_services
from config.config import cfg
from interfaces_tabs._tabs_menu_bar import MenuBar


# =========================
# BOOTSTRAP GLOBAL HELPERS
# =========================

def save_last_form(cfg, form_path: str):
    try:
        cfg.enable_writes() # <--- Ajoutez cette ligne pour déverrouiller
        cfg.set("LAST_FORM", form_path)
        cfg.save()
        cfg.disable_writes() # <--- Re-verrouillez après pour la sécurité
    except Exception as e:
        print(f"Erreur lors de la sauvegarde : {e}")

def load_last_form(cfg) -> str:
    try:
        return cfg.get("LAST_FORM", "")
    except Exception:
        return ""


logger = logging.getLogger("CostTracker_App")


# =========================
# APPLICATION PRINCIPALE
# =========================
class MainApp(tk.Tk):
    def __init__(self, services):
        super().__init__()
        self.services = services

        self.title("CostTrackers - Compte&Budget")
        self.geometry("1100x400")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.menu_bar = MenuBar(self, services)

        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)
        self.frame = None

        # Splash... (votre code actuel)
        _splash_dir = os.path.join(cfg.get("RACINE_DIRECTORY"), "assets", "backgrounds")
        _splash_name = "splash.png" if os.path.exists(os.path.join(_splash_dir, "splash.png")) else "nordeos_splash.png"
        splash_path = os.path.join(_splash_dir, _splash_name)
        self.show_splash_screen(splash_path)

        # Restauration du dernier formulaire (Code unique et propre)
        self.hide_var = tk.BooleanVar(value=cfg.get("HIDE_ON_START", False))

        last_form = load_last_form(cfg)
        success = False
        if last_form:
            try:
                # IMPORTANT: Vérifiez que votre MenuBar sait interpréter 'last_form'
                self.menu_bar.menu_callback(last_form)
                success = True
            except Exception as e:
                print(f"Erreur ouverture dernier form : {e}")

        if not success:
            self.show_default_form()

    # =========================
    # SPLASH SCREEN
    # =========================
    def show_splash_screen(self, image_path):
        splash = tk.Toplevel(self)
        splash.overrideredirect(True)

        try:
            img = Image.open(image_path)

            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()

            max_w = sw * 0.5
            max_h = sh * 0.5

            w, h = img.size

            if w > max_w or h > max_h:
                ratio = min(max_w / w, max_h / h)
                w, h = int(w * ratio), int(h * ratio)
                img = img.resize((w, h), Image.Resampling.LANCZOS)

            tk_img = ImageTk.PhotoImage(img)

            label = tk.Label(splash, image=tk_img)
            label.image = tk_img
            label.pack()

            x = int((sw - w) / 2)
            y = int((sh - h) / 2)

            splash.geometry(f"{w}x{h}+{x}+{y}")

            self.withdraw()
            splash.after(2000, lambda: self.finish_splash(splash))

        except Exception as e:
            print(f"Splash error: {e}")
            splash.destroy()
            self.deiconify()

    def finish_splash(self, splash):
        splash.destroy()
        self.deiconify()

    # =========================
    # NAVIGATION
    # =========================
    def show_frame(self, frame_class):
        """Détruit l'ancienne frame et affiche la nouvelle avec injection de services."""
        if self.frame:
            self.frame.destroy()

        # Vider les caches des services pour forcer la relecture des dernières infos
        self.clear_all_services_caches()																					 
        # On passe self.tiers_helpers (qui contient vos services) au constructeur de la frame
        # frame_class attend (parent, services)
        frame = frame_class(self.container, self.services)
        frame.pack(fill="both", expand=True)
        self.frame = frame

        # Sauvegarde pour la réouverture automatique au prochain lancement
        save_last_form(
            cfg,
            f"{frame_class.__module__}:{frame_class.__name__}"
        )

    # =========================
    # DEFAULT SCREEN
    # =========================
    def show_default_form(self):
        if self.frame:
            self.frame.destroy()

        frame = tk.Frame(self.container, bg="#f0f0f0")
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            text="Bienvenue dans CostTracker",
            font=("Arial", 18, "bold"),
            bg="#f0f0f0"
        ).pack(pady=30)

        tk.Label(
            frame,
            text="Sélectionnez une option dans le menu",
            bg="#f0f0f0"
        ).pack()

        def toggle_hide():
            val = self.hide_var.get()
            cfg.set("HIDE_ON_START", val)

        tk.Checkbutton(
            frame,
            text="Masquer à l'ouverture",
            variable=self.hide_var,
            command=toggle_hide,
            bg="#f0f0f0"
        ).pack(pady=20)

        self.frame = frame

    def clear_all_services_caches(self):
        """Parcourt le dictionnaire de services pour vider les trackers."""
        # On parcourt les valeurs du dictionnaire (f_tracker, emt_tracker, etc.)
        for service in self.services.values():
            # On vérifie si ce service a la méthode de nettoyage
            if hasattr(service, 'clear_cache'):
                service.clear_cache()										

    def on_close(self):
        self.destroy()


# =========================
# ENTRY POINT (BOOTSTRAP)
# =========================
if __name__ == "__main__":
    helpers = build_app_services()
    app = MainApp(helpers)
    app.mainloop()

