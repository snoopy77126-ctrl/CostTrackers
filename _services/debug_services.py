# debug_service.py

import logging
import traceback

DEBUG = True

logger = logging.getLogger("CostTracker_App")


def notifier_erreur(titre, message, exception=None, afficher=None):
    """Gestion centralisée des erreurs (log + debug + affichage)"""

    # 1. LOG (toujours)
    if exception:
        logger.error(f"{titre}: {message}", exc_info=True)
    else:
        logger.error(f"{titre}: {message}")

    # 2. DEBUG → console
    if DEBUG:
        print(f"[ERREUR] {titre} : {message}")
        if exception:
            traceback.print_exc()

    # 3. PROD → affichage UI
    elif afficher:
        afficher(titre, message)

