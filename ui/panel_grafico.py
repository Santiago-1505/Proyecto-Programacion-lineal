import tkinter as tk
from tkinter import messagebox
from typing import Optional

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as patches

from core.graphical_solver import GraphicalResult


class PanelGrafico(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._fig = Figure(figsize=(5, 4), dpi=100)
        self._ax = self._fig.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(self._fig, master=self)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

    def render(self, result: GraphicalResult):
        self._ax.clear()

        if result.infeasible:
            self._ax.text(0.5, 0.5, "Región factible vacía (infactible)", ha='center', va='center', transform=self._ax.transAxes)
            self._canvas.draw()
            return

        if not result.is_bounded:
            # show explicit message for unbounded (or unknown boundedness)
            self._ax.text(0.02, 0.98, "Región no acotada / puede ser no acotada",
                          ha='left', va='top', transform=self._ax.transAxes, color='red')

        # Draw lines
        xs = []
        ys = []
        for line in result.lines:
            a, b, c = line.a, line.b, line.c
            # plot line over a range
            # handle vertical
            if abs(b) < 1e-12 and abs(a) > 0:
                x = c / a
                ys = [0, max(1.0, max((p[1] for p in result.feasible_vertices), default=1.0) * 1.2)]
                xs = [x, x]
            else:
                xlim = self._ax.get_xlim() if self._ax.has_data() else (0, 5)
                x0, x1 = xlim
                # pick a sensible range if no data
                if x0 == x1:
                    x0, x1 = 0, 5
                xvals = [x0 - 1.0, x1 + 1.0]
                xs = xvals
                ys = [(c - a * xv) / b if abs(b) > 1e-12 else 0 for xv in xvals]
            self._ax.plot(xs, ys, color='#333333', linewidth=1)

        # Draw polygon (region factible)
        if result.polygon:
            poly = patches.Polygon(result.polygon, closed=True, facecolor='orange', alpha=0.3, edgecolor='orange')
            self._ax.add_patch(poly)

        # Draw feasible vertices
        if result.feasible_vertices:
            vx = [p[0] for p in result.feasible_vertices]
            vy = [p[1] for p in result.feasible_vertices]
            self._ax.scatter(vx, vy, color='blue', zorder=5)

        # Draw optimum
        if result.optimum_point:
            ox, oy = result.optimum_point
            self._ax.scatter([ox], [oy], color='red', s=80, zorder=10)
            self._ax.annotate(f"Optimo: ({ox:.3f}, {oy:.3f})\nZ={result.optimum_value:.3f}", (ox, oy), textcoords="offset points", xytext=(10,10))

        # Draw recession rays when unbounded and rays provided
        if result.rays:
            # draw rays starting from centroid of polygon or from optimum point
            if result.optimum_point:
                sx, sy = result.optimum_point
            elif result.polygon:
                sx = sum(p[0] for p in result.polygon) / len(result.polygon)
                sy = sum(p[1] for p in result.polygon) / len(result.polygon)
            else:
                sx, sy = 0.0, 0.0
            for dx, dy in result.rays:
                self._ax.arrow(sx, sy, dx * 5.0, dy * 5.0, head_width=0.1, head_length=0.2, fc='red', ec='red', linestyle='--')

        # labels and grid
        self._ax.set_xlabel('x1')
        self._ax.set_ylabel('x2')
        self._ax.grid(True, linestyle='--', alpha=0.5)

        # autoscale
        try:
            self._ax.relim()
            self._ax.autoscale_view()
        except Exception:
            pass

        self._canvas.draw()
