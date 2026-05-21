import tkinter as tk
from tkinter import messagebox
from core.modelo import Restriccion, TipoRestriccion
from ui.widgets.fila_restriccion import FilaRestriccion
from typing import Callable, Optional


# Paleta
BG_PANEL      = "#141e2b"
BG_SECCION    = "#1e2a3a"
BG_HEADER     = "#0f1923"
FG_TITULO     = "#e8edf2"
FG_LABEL      = "#7fb3d3"
FG_TEXTO      = "#e8edf2"
COLOR_BORDE   = "#2d4a6e"
COLOR_ENTRY   = "#0f1923"
COLOR_FOCUS   = "#3d8bcd"
COLOR_ACENTO  = "#2980b9"
COLOR_BTN_ADD = "#1a6b3c"
COLOR_BTN_ADD_HOVER = "#27ae60"
COLOR_BTN_RESOLVER  = "#1a5276"
COLOR_BTN_RESOL_HOVER = "#2471a3"
FONT_TITULO   = ("Georgia", 16, "bold")
FONT_SUBTIT   = ("Georgia", 11, "italic")
FONT_LABEL    = ("Segoe UI", 11)
FONT_MONO     = ("Consolas", 11)
FONT_BTN      = ("Segoe UI", 12, "bold")


def _hover(widget, color_normal, color_hover):
    widget.bind("<Enter>", lambda _: widget.config(bg=color_hover))
    widget.bind("<Leave>", lambda _: widget.config(bg=color_normal))


class PanelEntrada(tk.Frame):
    """
    Panel izquierdo de la ventana principal.
    Contiene:
      - Cabecera con título
      - Sección función objetivo Z
      - Sección restricciones (dinámica)
      - Botón Resolver
    """

    def __init__(self, parent, callback_resolver: Optional[Callable] = None, **kwargs):
        kwargs.setdefault("bg", BG_PANEL)
        super().__init__(parent, **kwargs)

        self._callback_resolver = callback_resolver
        self._filas: list[FilaRestriccion] = []

        self._construir_header()
        self._construir_seccion_objetivo()
        self._construir_seccion_restricciones()
        self._construir_btn_resolver()

    # Construcción UI

    def _construir_header(self):
        frame = tk.Frame(self, bg=BG_HEADER, pady=14)
        frame.pack(fill="x")

        tk.Label(
            frame, text="Programación Lineal",
            font=FONT_TITULO, bg=BG_HEADER, fg=FG_TITULO
        ).pack()

        tk.Label(
            frame, text="Método de la Gran M",
            font=FONT_SUBTIT, bg=BG_HEADER, fg=FG_LABEL
        ).pack()

        # Línea decorativa
        tk.Frame(self, height=2, bg=COLOR_ACENTO).pack(fill="x")

    def _construir_seccion_objetivo(self):
        outer = tk.Frame(self, bg=BG_PANEL, pady=10, padx=14)
        outer.pack(fill="x")

        tk.Label(
            outer, text="FUNCIÓN OBJETIVO",
            font=("Segoe UI", 10, "bold"),
            bg=BG_PANEL, fg=FG_LABEL
        ).pack(anchor="w")

        # Contenedor con borde
        seccion = tk.Frame(outer, bg=BG_SECCION, relief="flat",
                           highlightthickness=1,
                           highlightbackground=COLOR_BORDE)
        seccion.pack(fill="x", pady=(4, 0))

        inner = tk.Frame(seccion, bg=BG_SECCION, padx=12, pady=10)
        inner.pack(fill="x")

        # Fila: Z = [entrada]  [Min/Max]
        fila = tk.Frame(inner, bg=BG_SECCION)
        fila.pack(fill="x")

        tk.Label(
            fila, text="Z  =",
            font=("Consolas", 13, "bold"),
            bg=BG_SECCION, fg="#f0c040", width=5, anchor="w"
        ).pack(side="left")

        self._var_objetivo = tk.StringVar()
        self._entry_objetivo = tk.Entry(
            fila, textvariable=self._var_objetivo,
            font=FONT_MONO, width=24,
            bg=COLOR_ENTRY, fg=FG_TEXTO,
            insertbackground=FG_TEXTO,
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLOR_BORDE,
            highlightcolor=COLOR_FOCUS,
        )
        self._entry_objetivo.pack(side="left", padx=(0, 10), ipady=5)

        # Min / Max radio
        self._var_tipo_obj = tk.StringVar(value="min")
        for valor, etiq in [("min", "Min"), ("max", "Max")]:
            rb = tk.Radiobutton(
                fila, text=etiq, variable=self._var_tipo_obj, value=valor,
                font=FONT_LABEL, bg=BG_SECCION, fg=FG_TEXTO,
                selectcolor=COLOR_ENTRY,
                activebackground=BG_SECCION,
                activeforeground=FG_TEXTO,
            )
            rb.pack(side="left", padx=4)

        tk.Label(
            inner,
            text='Ejemplo: "2x1 + 3x2"  o  "5x1 - x2 + 4x3"',
            font=("Segoe UI", 10), bg=BG_SECCION, fg="#4a6f8a"
        ).pack(anchor="w", pady=(4, 0))

    def _construir_seccion_restricciones(self):
        outer = tk.Frame(self, bg=BG_PANEL, padx=14, pady=6)
        outer.pack(fill="x")

        tk.Label(
            outer, text="RESTRICCIONES",
            font=("Segoe UI", 10, "bold"),
            bg=BG_PANEL, fg=FG_LABEL
        ).pack(anchor="w")

        # Contenedor con scroll para las filas
        self._contenedor_rest = tk.Frame(
            outer, bg=BG_SECCION,
            highlightthickness=1,
            highlightbackground=COLOR_BORDE
        )
        self._contenedor_rest.pack(fill="x", pady=(4, 0))

        # Cabecera de columnas
        cab = tk.Frame(self._contenedor_rest, bg=BG_HEADER, pady=5)
        cab.pack(fill="x")

        for texto, ancho in [("#", 3), ("Lado izquierdo", 22),
                              ("Tipo", 18), ("Lado derecho", 10), ("", 3)]:
            tk.Label(
                cab, text=texto, width=ancho,
                font=("Segoe UI", 10, "bold"),
                bg=BG_HEADER, fg=FG_LABEL, anchor="w"
            ).pack(side="left", padx=(10 if texto == "#" else 2, 2))

        # Frame donde se insertan las filas
        self._frame_filas = tk.Frame(self._contenedor_rest, bg=BG_SECCION)
        self._frame_filas.pack(fill="x", padx=0, pady=(0, 4))

        # Primera restricción por defecto
        self._agregar_fila()

        # Botón "+"
        self._btn_add = tk.Button(
            self._contenedor_rest,
            text="＋  Agregar restricción",
            font=FONT_BTN,
            bg=COLOR_BTN_ADD, fg="white",
            activebackground=COLOR_BTN_ADD_HOVER,
            activeforeground="white",
            relief="flat", cursor="hand2",
            command=self._agregar_fila,
            pady=6,
        )
        self._btn_add.pack(fill="x", padx=12, pady=(4, 10))
        _hover(self._btn_add, COLOR_BTN_ADD, COLOR_BTN_ADD_HOVER)

    def _construir_btn_resolver(self):
        outer = tk.Frame(self, bg=BG_PANEL, padx=14, pady=12)
        outer.pack(fill="x")

        self._btn_resolver = tk.Button(
            outer,
            text="▶  Resolver",
            font=("Segoe UI", 12, "bold"),
            bg=COLOR_BTN_RESOLVER, fg="white",
            activebackground=COLOR_BTN_RESOL_HOVER,
            activeforeground="white",
            relief="flat", cursor="hand2",
            command=self._resolver,
            pady=10,
        )
        self._btn_resolver.pack(fill="x")
        _hover(self._btn_resolver, COLOR_BTN_RESOLVER, COLOR_BTN_RESOL_HOVER)

    # Lógica de restricciones

    def _agregar_fila(self):
        numero = len(self._filas) + 1
        fila = FilaRestriccion(
            self._frame_filas,
            numero=numero,
            on_eliminar=self._eliminar_fila,
        )
        fila.pack(fill="x", pady=1)
        self._filas.append(fila)

    def _eliminar_fila(self, fila: FilaRestriccion):
        if len(self._filas) == 1:
            messagebox.showwarning(
                "Atención",
                "Debe existir al menos una restricción."
            )
            return
        self._filas.remove(fila)
        fila.destroy()
        # Renumerar filas restantes
        for i, f in enumerate(self._filas, start=1):
            f.actualizar_numero(i)

    # API pública

    def obtener_objetivo(self) -> tuple[str, str]:
        """Retorna (expresion_z, 'min' | 'max')."""
        return self._var_objetivo.get().strip(), self._var_tipo_obj.get()

    def obtener_restricciones(self) -> list[Restriccion]:
        """Construye y retorna la lista de objetos Restriccion."""
        resultado = []
        for fila in self._filas:
            resultado.append(
                Restriccion(
                    lado_izquierdo=fila.lado_izquierdo,
                    tipo=fila.tipo,
                    lado_derecho=fila.lado_derecho,
                )
            )
        return resultado

    def _resolver(self):
        # Validación básica
        obj, tipo_obj = self.obtener_objetivo()
        if not obj:
            messagebox.showerror("Error", "La función objetivo Z no puede estar vacía.")
            return

        restricciones = self.obtener_restricciones()
        for i, r in enumerate(restricciones, 1):
            if not r.lado_izquierdo or not r.lado_derecho:
                messagebox.showerror(
                    "Error",
                    f"La restricción R{i} tiene campos vacíos."
                )
                return

        if self._callback_resolver:
            self._callback_resolver(obj, tipo_obj, restricciones)