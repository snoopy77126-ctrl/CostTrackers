import json
import logging
import os
import tkinter as tk
import traceback
import importlib  # <--- Correction : Ajout de l'import manquant ici
from tkinter import Menu, messagebox

# DEBUG SERVICE (ton module fig�)
from _services.debug_services import notifier_erreur

logger = logging.getLogger("CostTracker_App")

# Utilisation d'un chemin absolu plus robuste
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, "config", "menu_structure.json")


def load_menu_structure():
    """Charge la structure du menu depuis le fichier JSON."""
    try:
        if os.path.exists(JSON_PATH):
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                logger.info("Menu JSON charg� avec succ�s")
                return json.load(f)
        else:
            logger.warning(f"Menu JSON introuvable : {JSON_PATH}")
    except Exception as e:
        logger.error("Erreur lecture JSON menu", exc_info=True)
        notifier_erreur("JSON Menu", "Erreur lors du chargement du menu", e)
    return {}


class MenuBar(Menu):
    def __init__(self, master, services):
        super().__init__(master)
        self.master = master
        self.services = services
        self.menu_structure = load_menu_structure()
        self.build_menu()
                                                                            
        master.config(menu=self)
        logger.info("MenuBar initialis�e")

    def build_menu(self):
        """Construit les menus dynamiquement."""
        try:
            for category, items in self.menu_structure.items():
                cat_menu = Menu(self, tearoff=0)

                for item_name, action in items.items():
                    if action is None:
                        cat_menu.add_separator()
                    else:
                        cat_menu.add_command(
                            label=item_name,
                            command=lambda a=action: self.menu_callback(a)
                        )

                self.add_cascade(label=category, menu=cat_menu)

            logger.info("Menu construit avec succ�s")

        except Exception as e:
            logger.error("Erreur build_menu", exc_info=True)
            notifier_erreur("Menu", "Erreur construction menu", e)

    def menu_callback(self, action):
        """Import dynamique avec logs + debug service."""
        if not action or ":" not in action:
            logger.warning(f"Action invalide : {action}")
            print(f"?? Action invalide : {action}")
            return

        try:
            # On vide les caches avant de charger le nouveau module
            if hasattr(self.master, "clear_all_services_caches"):
                self.master.clear_all_services_caches()

            logger.info(f"Ouverture module : {action}")
            module_path, class_name = action.split(":")

            # Import dynamique stable
            module = importlib.import_module(module_path)
            importlib.reload(module)
            cls = getattr(module, class_name)

            # FRAME
            if issubclass(cls, tk.Frame):
                if hasattr(self.master, "show_frame"):
                    self.master.show_frame(cls)
                else:
                    self._fallback_show_frame(cls)

                logger.info(f"Frame affich� : {class_name}")

            # TOPLEVEL
            elif issubclass(cls, tk.Toplevel):
                cls(self.master, services=self.services, selected_key=None)
                logger.info(f"Toplevel ouvert : {class_name}")

            else:
                logger.warning(f"Type non support� : {class_name}")
                messagebox.showwarning(
                    "Type invalide",
                    f"La classe {class_name} n'est pas support�e."
                )

        except Exception as e:
            logger.error(f"Erreur ouverture menu : {action}", exc_info=True)

            print("\n" + "#" * 40)
            print("? ERREUR LORS DE L'EX�CUTION DU MENU")
            print(f"Action : {action}")
            print("-" * 40)
            traceback.print_exc()
            print("#" * 40 + "\n")

            notifier_erreur(
                "Erreur Menu",
                f"Impossible d'ouvrir : {action}",
                e
            )

    def _fallback_show_frame(self, cls):
        """Fallback si show_frame absent."""
        try:
            for child in self.master.winfo_children():
                if isinstance(child, tk.Frame) and child.winfo_name() != "!menubar":
                    child.destroy()

            frame = cls(self.master)
            frame.pack(fill="both", expand=True)

            logger.info(f"Fallback frame affich� : {cls.__name__}")

        except Exception as e:
            logger.error("Erreur fallback frame", exc_info=True)
            notifier_erreur("Frame", "Erreur affichage frame", e)

    def _on_nav_click(self, form_class, form_path):
        print(f'_on_nav_click')
        """M�thode appel�e lors d'un clic sur un bouton du menu."""
        # 1. On demande � l'application principale de vider les caches
        if hasattr(self.master, "clear_all_services_caches"):
            self.master.clear_all_services_caches()

        # 2. On change d'onglet
        if hasattr(self.master, "show_frame"):
            self.master.show_frame(form_class, form_path)

