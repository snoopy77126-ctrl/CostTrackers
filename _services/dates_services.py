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


    @staticmethod
    def get_date_bounds(periode_key):
        """Retourne un tuple (date_debut, date_fin) au format ISO YYYY-MM-DD.
        Retourne (None, None) pour 'toutesdates' ou clé inconnue (pas de filtre date)."""
        today = date.today()

        def iso(d):
            return d.strftime("%Y-%m-%d")

        if periode_key in ("toutesdates", "tous", None):
            return None, None

        if periode_key == "mois_courant":
            debut = today.replace(day=1)
            return iso(debut), iso(today)

        if periode_key == "mois_precedent":
            # Premier jour du mois précédent
            if today.month == 1:
                debut = date(today.year - 1, 12, 1)
                fin   = date(today.year - 1, 12, 31)
            else:
                import calendar
                debut = date(today.year, today.month - 1, 1)
                last  = calendar.monthrange(today.year, today.month - 1)[1]
                fin   = date(today.year, today.month - 1, last)
            return iso(debut), iso(fin)

        if periode_key == "3_mois":
            # Les 3 derniers mois glissants
            month = today.month - 3
            year  = today.year
            if month <= 0:
                month += 12
                year  -= 1
            debut = date(year, month, 1)
            return iso(debut), iso(today)

        if periode_key == "annee_courante":
            debut = date(today.year, 1, 1)
            return iso(debut), iso(today)

        if periode_key == "annee_precedente":
            debut = date(today.year - 1, 1, 1)
            fin   = date(today.year - 1, 12, 31)
            return iso(debut), iso(fin)

        return None, None
