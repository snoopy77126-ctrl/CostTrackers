import tkinter as tk
from tkinter import ttk
from datetime import datetime, date
from calendar import monthrange


class TabsGraf(ttk.Frame):
    """Canvas graphique courbe réutilisable."""

    def __init__(self, parent, title="Graphique", height=220):
        super().__init__(parent)
        self.title = title
        self.points = []
        self.height = height

        self.frame = ttk.LabelFrame(self, text=title, padding=6)
        self.frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(self.frame, height=height, bg="#eaf4ff", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _event: self._draw())

    def set_points(self, points):
        self.points = list(points or [])
        self._draw()

    def _draw(self):
        canvas = self.canvas
        canvas.delete("all")
        width  = max(canvas.winfo_width(),  20)
        height = max(canvas.winfo_height(), self.height)
        pl, pr, pt, pb = 54, 16, 20, 30
        plot_w = max(width - pl - pr, 1)
        plot_h = max(height - pt - pb, 1)

        canvas.create_rectangle(0, 0, width, height, fill="#eaf4ff", outline="")
        canvas.create_line(pl, pt,       pl,       height - pb, fill="#5d7fa6")
        canvas.create_line(pl, height - pb, width - pr, height - pb, fill="#5d7fa6")

        if not self.points:
            canvas.create_text(width / 2, height / 2, text="Aucune donnée", fill="#365f8f")
            return

        values = [float(v or 0) for _, v in self.points]
        min_v  = min(values + [0])
        max_v  = max(values + [0])
        if min_v == max_v:
            min_v -= 1; max_v += 1
        span = max_v - min_v

        for i in range(5):
            y   = pt + i * plot_h / 4
            val = max_v - i * span / 4
            canvas.create_line(pl, y, width - pr, y, fill="#c7d9ef")
            canvas.create_text(pl - 8, y, text=f"{val:.0f}", anchor="e",
                               fill="#31557d", font=("Arial", 8))

        step   = plot_w / max(len(values) - 1, 1)
        coords = []
        for i, v in enumerate(values):
            x = pl + i * step
            y = pt + (max_v - v) * plot_h / span
            coords.extend([x, y])

        zero_y = pt + max_v * plot_h / span
        area   = [pl, zero_y] + coords + [pl + (len(values) - 1) * step, zero_y]
        canvas.create_polygon(area, fill="#ffc766", outline="#d99000")
        canvas.create_line(coords, fill="#1d4f82", width=2)

        step_lbl = max(len(self.points) // 6, 1)
        for i, (label, _) in enumerate(self.points):
            if i % step_lbl == 0 or i == len(self.points) - 1:
                x = pl + i * step
                canvas.create_text(x, height - 12, text=str(label),
                                   fill="#31557d", font=("Arial", 8))


# ══════════════════════════════════════════════════════════════════════════════
#  TabsGrafBaton  —  deux séries (dépenses / revenus) par mois
#  set_points attend une liste de tuples : (mois_str, depenses, revenus)
#  avec mois_str au format "MM/YY"
#  Les mois manquants sont automatiquement espacés sur l'axe temporel.
# ══════════════════════════════════════════════════════════════════════════════

class TabsGrafBaton(ttk.Frame):

    PAD_LEFT   = 68
    PAD_RIGHT  = 16
    PAD_TOP    = 24
    PAD_BOTTOM = 38

    COLOR_BG       = "#eaf4ff"
    COLOR_AXIS     = "#5d7fa6"
    COLOR_GRID     = "#c7d9ef"
    COLOR_LABEL    = "#31557d"
    COLOR_ZERO     = "#8aaac8"
    COLOR_DEPENSE  = "#cc3333"   # rouge  — dépenses (valeur absolue, barre arrière)
    COLOR_REVENU   = "#2e8b57"   # vert   — revenus  (barre avant si plus petite)
    COLOR_EMPTY    = "#dde8f5"   # mois sans donnée

    def __init__(self, parent, title="Graphique", height=220, **kwargs):
        super().__init__(parent, **kwargs)
        self.title  = title
        self.height = height
        self._points_raw = []   # [(mois_str, dep, rev), ...]

        self.frame = ttk.LabelFrame(self, text=title, padding=6)
        self.frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.frame, height=height,
                                bg=self.COLOR_BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _e: self._draw())

    # ------------------------------------------------------------------ #
    #  API publique
    #  points : list[(mois "MM/YY", depenses float>=0, revenus float>=0)]
    # ------------------------------------------------------------------ #
    def set_points(self, points):
        self._points_raw = list(points or [])
        self._draw()

    # ------------------------------------------------------------------ #
    #  Construction de l'axe temporel complet (avec trous)
    # ------------------------------------------------------------------ #
    def _build_timeline(self):
        """
        Retourne une liste ordonnée de tous les mois entre le premier
        et le dernier mois des données, y compris les mois vides.
        Format : [("MM/YY", dep, rev), ...]  — dep=rev=None si mois absent.
        """
        if not self._points_raw:
            return []

        # Index des données existantes
        data_by_month = {p[0]: p for p in self._points_raw}

        # Convertit "MM/YY" → date du 1er du mois
        def to_date(s):
            mm, yy = s.split("/")
            return date(2000 + int(yy), int(mm), 1)

        keys_sorted = sorted(data_by_month.keys(), key=to_date)
        start = to_date(keys_sorted[0])
        end   = to_date(keys_sorted[-1])

        timeline = []
        y, m = start.year, start.month
        while (y, m) <= (end.year, end.month):
            key = f"{m:02d}/{y % 100:02d}"
            if key in data_by_month:
                _, dep, rev = data_by_month[key]
                timeline.append((key, float(dep or 0), float(rev or 0)))
            else:
                timeline.append((key, None, None))   # mois vide
            m += 1
            if m > 12:
                m = 1; y += 1

        return timeline

    # ------------------------------------------------------------------ #
    #  Dessin
    # ------------------------------------------------------------------ #
    def _draw(self):
        c = self.canvas
        c.delete("all")

        W = max(c.winfo_width(),  20)
        H = max(c.winfo_height(), self.height)
        pl, pr, pt, pb = self.PAD_LEFT, self.PAD_RIGHT, self.PAD_TOP, self.PAD_BOTTOM
        plot_w = max(W - pl - pr, 1)
        plot_h = max(H - pt - pb, 1)

        c.create_rectangle(0, 0, W, H, fill=self.COLOR_BG, outline="")

        timeline = self._build_timeline()

        if not timeline:
            c.create_text(W / 2, H / 2, text="Aucune donnée", fill=self.COLOR_LABEL)
            self._draw_axes(c, W, H, pl, pr, pt, pb)
            return

        # Calcul de l'échelle Y (on ignore les mois vides)
        all_vals = []
        for _, dep, rev in timeline:
            if dep is not None: all_vals.append(dep)
            if rev is not None: all_vals.append(rev)

        max_v = max(all_vals + [0])
        if max_v == 0:
            max_v = 1

        zero_y = pt + plot_h   # zéro toujours en bas (tout est >= 0)

        # ---- Grille horizontale + valeurs Y ----------------------------- #
        nb_grid = 4
        for i in range(nb_grid + 1):
            val = max_v * i / nb_grid
            y   = zero_y - (val / max_v) * plot_h
            c.create_line(pl, y, W - pr, y, fill=self.COLOR_GRID, dash=(2, 4))
            c.create_text(pl - 6, y, text=self._fmt(val),
                          anchor="e", fill=self.COLOR_LABEL, font=("Arial", 8))

        # Ligne zéro (trait plein)
        c.create_line(pl, zero_y, W - pr, zero_y, fill=self.COLOR_ZERO, width=1)

        # ---- Barres ----------------------------------------------------- #
        nb    = len(timeline)
        step  = plot_w / nb
        bar_w = max(step * 0.6, 3)

        for i, (label, dep, rev) in enumerate(timeline):
            cx = pl + (i + 0.5) * step
            x0 = cx - bar_w / 2
            x1 = cx + bar_w / 2

            if dep is None:
                # Mois vide : petit tiret discret
                c.create_line(cx, zero_y - 3, cx, zero_y, fill=self.COLOR_EMPTY)
                # Label quand même
                self._draw_month_label(c, cx, H, pb, label, i, nb)
                continue

            h_dep = (dep / max_v) * plot_h
            h_rev = (rev / max_v) * plot_h

            # Règle : la plus grande barre est dessinée EN PREMIER (derrière)
            # la plus petite EST DESSINÉE EN SECOND (devant), légèrement plus étroite
            bar_w_front = max(bar_w * 0.65, 2)

            if dep >= rev:
                # Dépense derrière (rouge, pleine largeur)
                self._bar(c, x0, x1, zero_y, h_dep, self.COLOR_DEPENSE)
                # Revenu devant (vert, plus étroit, centré)
                xf0 = cx - bar_w_front / 2
                xf1 = cx + bar_w_front / 2
                self._bar(c, xf0, xf1, zero_y, h_rev, self.COLOR_REVENU)
            else:
                # Revenu derrière (vert, pleine largeur)
                self._bar(c, x0, x1, zero_y, h_rev, self.COLOR_REVENU)
                # Dépense devant (rouge, plus étroite, centrée)
                xf0 = cx - bar_w_front / 2
                xf1 = cx + bar_w_front / 2
                self._bar(c, xf0, xf1, zero_y, h_dep, self.COLOR_DEPENSE)

            self._draw_month_label(c, cx, H, pb, label, i, nb)

        # ---- Légende ---------------------------------------------------- #
        self._draw_legend(c, W, pt)

        # ---- Axes (par-dessus tout) ------------------------------------- #
        self._draw_axes(c, W, H, pl, pr, pt, pb)

    # ------------------------------------------------------------------ #
    #  Helpers dessin
    # ------------------------------------------------------------------ #

    def _bar(self, c, x0, x1, zero_y, h, color):
        """Dessine une barre vers le haut depuis zero_y."""
        y0 = zero_y - h
        y1 = zero_y
        c.create_rectangle(x0, y0, x1, y1, fill=color, outline="")
        # Reflet léger
        c.create_rectangle(x0, y0, x0 + max((x1 - x0) * 0.3, 1), y1,
                           fill=self._lighten(color), outline="")

    def _draw_month_label(self, c, cx, H, pb, label, i, nb):
        step_lbl = max(nb // 10, 1)
        if i % step_lbl == 0 or i == nb - 1:
            c.create_text(cx, H - pb + 5, text=str(label),
                          fill=self.COLOR_LABEL, font=("Arial", 8), anchor="n")

    def _draw_legend(self, c, W, pt):
        """Petite légende en haut à droite."""
        items = [
            (self.COLOR_REVENU,  "Revenus"),
            (self.COLOR_DEPENSE, "Dépenses"),
        ]
        x = W - self.PAD_RIGHT - 2
        y = pt - 4
        for color, label in reversed(items):
            text_w = len(label) * 6 + 16
            c.create_rectangle(x - text_w, y, x - text_w + 10, y + 9,
                               fill=color, outline="")
            c.create_text(x - text_w + 13, y + 4, text=label, anchor="w",
                          fill=self.COLOR_LABEL, font=("Arial", 8))
            x -= text_w + 6

    def _draw_axes(self, c, W, H, pl, pr, pt, pb):
        c.create_line(pl, pt,      pl,      H - pb, fill=self.COLOR_AXIS, width=1)
        c.create_line(pl, H - pb,  W - pr,  H - pb, fill=self.COLOR_AXIS, width=1)

    @staticmethod
    def _fmt(val):
        if abs(val) >= 1_000_000: return f"{val/1_000_000:.1f}M"
        if abs(val) >= 1_000:     return f"{val/1_000:.0f}k"
        return f"{val:.0f}"

    @staticmethod
    def _lighten(hex_color):
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"#{min(255,r+45):02x}{min(255,g+45):02x}{min(255,b+45):02x}"
