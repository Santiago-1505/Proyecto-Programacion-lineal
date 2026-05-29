import tkinter as tk
from tkinter import messagebox
from typing import Optional
import math

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
            # Draw objective line passing through optimum: c1*x + c2*y = Z*
            if getattr(result, 'obj_vec', None) is not None and result.optimum_value is not None:
                c1, c2 = result.obj_vec
                z = result.optimum_value
                # Determine plotting bounds that cover the polygon/vertices
                xs_all = []
                ys_all = []
                if result.polygon:
                    xs_all += [p[0] for p in result.polygon]
                    ys_all += [p[1] for p in result.polygon]
                if result.feasible_vertices:
                    xs_all += [p[0] for p in result.feasible_vertices]
                    ys_all += [p[1] for p in result.feasible_vertices]
                if result.optimum_point:
                    xs_all.append(result.optimum_point[0]); ys_all.append(result.optimum_point[1])

                if xs_all and ys_all:
                    xmin, xmax = min(xs_all), max(xs_all)
                    ymin, ymax = min(ys_all), max(ys_all)
                    dx = max(1.0, (xmax - xmin) * 0.25)
                    dy = max(1.0, (ymax - ymin) * 0.25)
                    x0, x1 = xmin - dx, xmax + dx
                    y0, y1 = ymin - dy, ymax + dy
                else:
                    x0, x1 = self._ax.get_xlim() if self._ax.has_data() else (ox - 5, ox + 5)
                    y0, y1 = self._ax.get_ylim() if self._ax.has_data() else (oy - 5, oy + 5)

                # handle vertical objective (c2 ~ 0)
                if abs(c2) < 1e-12 and abs(c1) > 0:
                    x_line = z / c1
                    ys = [y0, y1]
                    xs = [x_line, x_line]
                else:
                    # compute xs across extended x-range and corresponding ys
                    xs = [x0, x1]
                    ys = [ (z - c1 * xv) / c2 for xv in xs ]

                # draw the line so that it visibly crosses the polygon (on top)
                self._ax.plot(xs, ys, color='green', linestyle='-', linewidth=2.0, zorder=9)

                # annotate with equation placed in the top-right corner of the axes
                eq = f"{c1:.3g}x1 {'+' if c2>=0 else '-'} {abs(c2):.3g}x2 = {z:.3g}"
                self._ax.text(
                    0.98, 0.98, eq,
                    transform=self._ax.transAxes,
                    ha='right', va='top', color='green', fontsize=9,
                    bbox=dict(facecolor='white', alpha=0.8, edgecolor='none')
                )

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
