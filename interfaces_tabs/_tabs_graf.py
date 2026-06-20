import tkinter as tk
from tkinter import ttk


class TabsGraf(ttk.Frame):
    """Canvas graphique reutilisable pour les sous-formulaires financiers."""

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
        width = max(canvas.winfo_width(), 20)
        height = max(canvas.winfo_height(), self.height)
        pad_left, pad_right, pad_top, pad_bottom = 54, 16, 20, 30

        plot_w = max(width - pad_left - pad_right, 1)
        plot_h = max(height - pad_top - pad_bottom, 1)

        canvas.create_rectangle(0, 0, width, height, fill="#eaf4ff", outline="")
        canvas.create_line(pad_left, pad_top, pad_left, height - pad_bottom, fill="#5d7fa6")
        canvas.create_line(pad_left, height - pad_bottom, width - pad_right, height - pad_bottom, fill="#5d7fa6")

        if not self.points:
            canvas.create_text(width / 2, height / 2, text="Aucune donnee", fill="#365f8f")
            return

        values = [float(value or 0) for _label, value in self.points]
        min_v = min(values + [0])
        max_v = max(values + [0])
        if min_v == max_v:
            min_v -= 1
            max_v += 1

        for index in range(5):
            y = pad_top + index * plot_h / 4
            value = max_v - index * (max_v - min_v) / 4
            canvas.create_line(pad_left, y, width - pad_right, y, fill="#c7d9ef")
            canvas.create_text(pad_left - 8, y, text=f"{value:.0f}", anchor="e", fill="#31557d", font=("Arial", 8))

        coords = []
        step = plot_w / max(len(values) - 1, 1)
        for index, value in enumerate(values):
            x = pad_left + index * step
            y = pad_top + (max_v - value) * plot_h / (max_v - min_v)
            coords.extend([x, y])

        zero_y = pad_top + (max_v - 0) * plot_h / (max_v - min_v)
        area = [pad_left, zero_y] + coords + [pad_left + (len(values) - 1) * step, zero_y]
        canvas.create_polygon(area, fill="#ffc766", outline="#d99000")
        canvas.create_line(coords, fill="#1d4f82", width=2)

        if len(coords) >= 4:
            zero_y = pad_top + (max_v - 0) * plot_h / (max_v - min_v)
            area = [pad_left, zero_y] + coords + [pad_left + (len(values) - 1) * step, zero_y]
            canvas.create_polygon(area, fill="#ffc766", outline="#d99000")
            canvas.create_line(coords, fill="#1d4f82", width=2)

        for index, (label, value) in enumerate(self.points):
            if index % max(len(self.points) // 6, 1) == 0 or index == len(self.points) - 1:
                x = pad_left + index * step
                canvas.create_text(x, height - 12, text=str(label), fill="#31557d", font=("Arial", 8))

