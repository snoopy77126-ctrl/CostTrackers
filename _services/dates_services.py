from datetime import datetime, date


class DatesManager:
    """Classe pour gérer et convertir les dates."""

    @staticmethod
    def iso_to_fr(chaine_iso):
        """
        Convertit une date ISO (YYYY-MM-DD ou YYYY-MM-DD HH:MM) en format français JJ/MM/AAAA.
        Retourne '(inconnue)' si la chaîne est vide.
        Retourne la chaîne d'origine si le format est inconnu.
        """
        if not chaine_iso:
            return "(inconnue)"

        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                date_obj = datetime.strptime(chaine_iso, fmt)
                return date_obj.strftime("%d/%m/%Y")
            except ValueError:
                continue

        return chaine_iso

    @staticmethod
    def fr_to_iso(chaine_fr):
        """
        Convertit une date au format JJ/MM/AAAA ou JJ/MM/AA vers YYYY-MM-DD.
        Retourne None si la chaîne est vide ou invalide.
        """
        if not chaine_fr:
            return None

        formats_acceptes = ["%d/%m/%Y", "%d/%m/%y"]
        for fmt in formats_acceptes:
            try:
                date_obj = datetime.strptime(chaine_fr, fmt)
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                continue

        return None

    @staticmethod
    def date_courante(format_long=False):
        """
        Renvoie la date du jour formatée en français.
        format_long=False => 'JJ/MM/AAAA'
        format_long=True  => '09 août 2025'
        """
        maintenant = datetime.now()
        if format_long:
            return maintenant.strftime("%d %B %Y")
        return maintenant.strftime("%d/%m/%Y")

    @staticmethod
    def periode_filter():
        today = date.today()
        mois_prec = (today.month - 2) % 12 + 1
        annee_prec_mois = today.year if today.month > 1 else today.year - 1

        filtres = {
            "mois_courant": lambda d: d.year == today.year and d.month == today.month,
            "mois_precedent": lambda d: d.year == annee_prec_mois and d.month == mois_prec,
            "3_mois": lambda d: (today.year - d.year) * 12 + (today.month - d.month) < 3,
            "annee_courante": lambda d: d.year == today.year,
            "annee_precedente": lambda d: d.year == today.year - 1,
        }


