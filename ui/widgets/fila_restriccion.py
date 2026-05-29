import tkinter as tk
from tkinter import ttk
from core.modelo import TipoRestriccion


# Paleta de colores
BG_FILA       = "#1e2a3a"
BG_FILA_ALT   = "#1a2433"
FG_TEXTO      = "#ffffff"
FG_TEXTO_COMBO_BOX = "#000000"
FG_LABEL      = "#7fb3d3"
COLOR_BORDE   = "#2d4a6e"
COLOR_ENTRY   = "#0f1923"
COLOR_FOCUS   = "#3d8bcd"
COLOR_ELIMINAR = "#c0392b"
COLOR_ELIM_HOVER = "#e74c3c"
FONT_MONO     = ("Consolas", 12)
FONT_LABEL    = ("Segoe UI", 10)


class FilaRestriccion(tk.Frame):
    """
    Fila compuesta por:
      [  Lado izquierdo  ]  [ DropBox tipo ]  [  Lado derecho  ]  [ ✕ ]
    """

    def __init__(self, parent, numero: int, on_eliminar=None, **kwargs):
        kwargs.setdefault("bg", BG_FILA if numero % 2 == 0 else BG_FILA_ALT)
        super().__init__(parent, **kwargs)

        self.numero = numero
        self.on_eliminar = on_eliminar
        bg = kwargs["bg"]

        # Número de restricción
        self._lbl_num = tk.Label(
            self, text=f"R{numero}", width=3,
            font=("Consolas", 11, "bold"),
            bg=bg, fg=FG_LABEL
        )
        self._lbl_num.pack(side="left", padx=(10, 4))

        # Lado izquierdo
        self._var_izq = tk.StringVar()
        self._entry_izq = tk.Entry(
            self, textvariable=self._var_izq,
            font=FONT_MONO, width=22,
            bg=COLOR_ENTRY, fg=FG_TEXTO,
            insertbackground=FG_TEXTO,
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLOR_BORDE,
            highlightcolor=COLOR_FOCUS,
        )
        self._entry_izq.pack(side="left", padx=(0, 8), ipady=5)

        # DropBox tipo de restricción
        self._var_tipo = tk.StringVar()
        opciones = TipoRestriccion.opciones_display()
        self._var_tipo.set(opciones[2])  # "≤" por defecto

        style_name = f"Restriccion{numero}.TCombobox"
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            style_name,
            fieldbackground=COLOR_ENTRY,
            background=COLOR_ENTRY,
            foreground=FG_TEXTO_COMBO_BOX,
            arrowcolor=FG_LABEL,
            bordercolor=COLOR_BORDE,
            lightcolor=COLOR_BORDE,
            darkcolor=COLOR_BORDE,
            selectbackground=COLOR_FOCUS,
            selectforeground=FG_TEXTO,
            font=FONT_MONO,
        )

        self._combo_tipo = ttk.Combobox(
            self, textvariable=self._var_tipo,
            values=opciones,
            state="readonly",
            width=18,
            style=style_name,
            font=FONT_MONO,
        )
        self._combo_tipo.pack(side="left", padx=(0, 8), ipady=4)

        # Lado derecho
        self._var_der = tk.StringVar()
        self._entry_der = tk.Entry(
            self, textvariable=self._var_der,
            font=FONT_MONO, width=10,
            bg=COLOR_ENTRY, fg=FG_TEXTO,
            insertbackground=FG_TEXTO,
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLOR_BORDE,
            highlightcolor=COLOR_FOCUS,
        )
        self._entry_der.pack(side="left", padx=(0, 10), ipady=5)

        # Botón eliminar
        self._btn_elim = tk.Button(
            self, text="✕", width=2,
            font=("Segoe UI", 11, "bold"),
            bg=COLOR_ELIMINAR, fg="white",
            activebackground=COLOR_ELIM_HOVER,
            activeforeground="white",
            relief="flat", cursor="hand2",
            command=self._eliminar,
        )
        self._btn_elim.pack(side="left", padx=(0, 10), ipady=2)

    # API pública

    def actualizar_numero(self, nuevo_num: int):
        """Actualiza la etiqueta del número de restricción."""
        self.numero = nuevo_num
        self._lbl_num.config(text=f"R{nuevo_num}")
        nuevo_bg = BG_FILA if nuevo_num % 2 == 0 else BG_FILA_ALT
        self.config(bg=nuevo_bg)
        self._lbl_num.config(bg=nuevo_bg)

    @property
    def lado_izquierdo(self) -> str:
        return self._var_izq.get().strip()

    @property
    def tipo(self) -> TipoRestriccion:
        return TipoRestriccion.desde_display(self._var_tipo.get())

    @property
    def lado_derecho(self) -> str:
        return self._var_der.get().strip()

    # Internos

    def _eliminar(self):
        if self.on_eliminar:
            self.on_eliminar(self)
