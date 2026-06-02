import tkinter as tk
from tkinter import ttk, messagebox
from ui.panel_entrada import PanelEntrada
from ui.panel_resultado import PanelResultado
from core.gran_m import ConstructorPrimerIteracion
from core.solucionador_simplex import SolucionadorSimplex
from core.analisis_sensibilidad import calcular_sensibilidad


BG_VENTANA   = "#0f1923"
BG_DERECHO   = "#141e2b"
FG_PLACEHOLDER = "#2d4a6e"
BG_BUTTON    = "#1a3a52"
BG_BUTTON_HOVER = "#2d5a7a"
FG_BUTTON    = "#e8edf2"
BG_BUTTON_DISABLED = "#0a1622"


def _hover(widget, color_normal, color_hover):
    """Bindings Enter/Leave para efecto hover, respetando estado disabled."""
    def on_enter(e):
        if str(widget.cget('state')) != 'disabled':
            widget.config(bg=color_hover)
    def on_leave(e):
        if str(widget.cget('state')) != 'disabled':
            widget.config(bg=color_normal)
    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)


class VentanaPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Programación Lineal - Método Gran M")
        self.geometry("1700x900")
        self.minsize(1000, 700)
        self.configure(bg=BG_VENTANA)

        # Centrar ventana en pantalla, sin exceder la resolución disponible
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        w = min(1700, screen_w - 80)
        h = min(900, screen_h - 80)
        x = (screen_w - w) // 2
        y = (screen_h - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        # Estado del solucionador
        self._solucionador = None

        self._construir_layout()

    def _construir_layout(self):
        # Única llamada a theme_use en toda la app.
        # fila_restriccion.py NO debe llamar theme_use (causa re-render global en X11).
        style = ttk.Style()
        style.theme_use('clam')

        # Panel izquierdo
        self._panel_entrada = PanelEntrada(
            self,
            callback_resolver=self._on_resolver,
            bg="#141e2b",
        )
        self._panel_entrada.pack(side="left", fill="y")

        # Separador vertical
        tk.Frame(self, width=2, bg="#2d4a6e").pack(side="left", fill="y")

        # Contenedor derecho
        self._panel_container = tk.Frame(self, bg=BG_DERECHO)
        self._panel_container.pack(side="right", fill="both", expand=True)

        # ── FIX X11: declarar side="bottom" ANTES que side="top" ──────────────
        # En tkinter/pack el espacio se asigna en orden de declaración.
        # Si "top" con expand=True se declara primero, consume todo el espacio
        # vertical y el frame "bottom" queda con altura 0 en X11.
        # Declarando "bottom" primero queda anclado con altura garantizada.
        self._panel_controls_holder = tk.Frame(
            self._panel_container,
            bg=BG_DERECHO,
            height=100,          # altura mínima garantizada
        )
        self._panel_controls_holder.pack(side="bottom", fill="x")
        self._panel_controls_holder.pack_propagate(False)  # no ceder espacio al contenido

        # Separador visual entre tabla y controles
        tk.Frame(self._panel_container, height=1, bg="#2d4a6e").pack(
            side="bottom", fill="x"
        )

        # Content ocupa el resto (top + expand=True), crece hacia arriba
        self._panel_content = tk.Frame(self._panel_container, bg=BG_DERECHO)
        self._panel_content.pack(side="top", fill="both", expand=True)
        # ── fin FIX ────────────────────────────────────────────────────────────

        # Panel de resultados inicial
        self._panel_resultado = PanelResultado(self._panel_content, bg=BG_DERECHO)
        self._panel_resultado.pack(fill="both", expand=True)

        # Construir controles dentro del holder ya anclado
        self._construir_panel_controles(self._panel_controls_holder)

    def _construir_panel_controles(self, parent):
        """Construye el panel de controles con botones de navegación."""
        panel_controles = tk.Frame(parent, bg="#0a1622", height=80)
        panel_controles.pack(fill="both", expand=True, padx=10, pady=10)
        panel_controles.pack_propagate(False)

        # Frame interior
        frame_interior = tk.Frame(panel_controles, bg="#0a1622")
        frame_interior.pack(fill="both", expand=True, padx=10, pady=10)

        # Etiqueta informativa
        lbl_info = tk.Label(
            frame_interior,
            text="",
            bg="#0a1622",
            fg="#7fb3d3",
            font=("Consolas", 10)
        )
        lbl_info.pack(side="left", padx=5)
        self._lbl_info = lbl_info

        # Espaciador
        tk.Frame(frame_interior, bg="#0a1622").pack(side="left", expand=True)

        # Botón Siguiente Iteración — tk.Button (no ttk) para evitar bug X11
        self._btn_siguiente = tk.Button(
            frame_interior,
            text="Siguiente Iteración  ▶",
            command=self._on_siguiente_iteracion,
            font=("Consolas", 11, "bold"),
            bg=BG_BUTTON_DISABLED,
            fg=FG_BUTTON,
            disabledforeground='#666666',
            activebackground=BG_BUTTON_HOVER,
            activeforeground=FG_BUTTON,
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8,
        )
        self._btn_siguiente.pack(side="right", padx=5)
        self._btn_siguiente.config(state='disabled')
        _hover(self._btn_siguiente, BG_BUTTON, BG_BUTTON_HOVER)

        # Botón Análisis de Sensibilidad
        self._sensibilidad_visible = False
        self._sensibilidad_cache = None
        self._btn_sensibilidad = tk.Button(
            frame_interior,
            text="Mostrar Sensibilidad",
            command=self._on_toggle_sensibilidad,
            font=("Consolas", 11, "bold"),
            bg=BG_BUTTON_DISABLED,
            fg=FG_BUTTON,
            disabledforeground='#666666',
            activebackground=BG_BUTTON_HOVER,
            activeforeground=FG_BUTTON,
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8,
        )
        self._btn_sensibilidad.pack(side="right", padx=5)
        self._btn_sensibilidad.config(state='disabled')
        _hover(self._btn_sensibilidad, BG_BUTTON, BG_BUTTON_HOVER)

    def _on_resolver(self, objetivo: str, tipo_obj: str, restricciones, metodo: str = 'gran_m'):
        """Callback recibido desde PanelEntrada al pulsar Resolver."""
        try:
            print("=" * 60)
            print(f"Objetivo ({tipo_obj.upper()}): Z = {objetivo}")
            print("Restricciones:")
            for r in restricciones:
                print(f"  {r}")
            print("=" * 60)

            if metodo == 'grafico':
                try:
                    from core.graphical_solver import solve_graphical
                except Exception as e:
                    messagebox.showerror("Error", f"No se puede cargar el motor gráfico: {e}")
                    return

                try:
                    result = solve_graphical(objetivo, tipo_obj, restricciones, include_nonnegativity=True)
                except ValueError:
                    raise
                except Exception as e:
                    messagebox.showerror("Error", f"Error al calcular la solución gráfica: {e}")
                    return

                try:
                    from ui.panel_grafico import PanelGrafico
                except ImportError:
                    messagebox.showerror(
                        "Dependencia faltante",
                        "Para usar el método gráfico instale matplotlib: pip install matplotlib"
                    )
                    return

                for child in list(self._panel_content.winfo_children()):
                    child.destroy()
                self._panel_resultado = PanelGrafico(self._panel_content, bg=BG_DERECHO)
                self._panel_resultado.pack(fill="both", expand=True)
                try:
                    self._panel_resultado.render(result)
                except Exception as e:
                    messagebox.showerror("Error gráfico", f"Error al renderizar el gráfico: {e}")
                    return
                self._solucionador = None
                self._actualizar_estado_controles()
            else:
                constructor = ConstructorPrimerIteracion()
                iteracion_inicial = constructor.construir_tableau_inicial(
                    objetivo=objetivo,
                    tipo_optimizacion=tipo_obj,
                    restricciones=restricciones
                )
                es_minimizacion = (tipo_obj.lower() == "min")
                self._solucionador = SolucionadorSimplex(iteracion_inicial, es_minimizacion)

                for child in list(self._panel_content.winfo_children()):
                    child.destroy()
                self._panel_resultado = PanelResultado(self._panel_content, bg=BG_DERECHO)
                self._panel_resultado.pack(fill="both", expand=True)
                self._panel_resultado.mostrar_iteracion(iteracion_inicial)
                self._actualizar_estado_controles()

        except ValueError as e:
            messagebox.showerror("Error de validación", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error al resolver: {str(e)}")
            print(f"Traceback completo: {e}")
            import traceback
            traceback.print_exc()

    def _on_siguiente_iteracion(self):
        """Manejador para botón 'Siguiente Iteración'."""
        if self._solucionador is None:
            messagebox.showwarning("Advertencia", "Primero debes resolver un problema")
            return

        try:
            if not self._solucionador.puede_avanzar():
                valor_z = self._solucionador.obtener_valor_objetivo()
                mensaje = (
                    "✓ Se alcanzó la solución óptima\n\n"
                    f"Valor de Z: {valor_z:.4f}\n\n"
                    "El botón será deshabilitado ahora."
                )
                messagebox.showinfo("Solución óptima alcanzada", mensaje)
                self._actualizar_estado_controles()
                try:
                    sensibilidad = calcular_sensibilidad(self._solucionador)
                    self._sensibilidad_cache = sensibilidad
                    self._sensibilidad_visible = True
                    self._panel_resultado.mostrar_sensibilidad(sensibilidad)
                except Exception as e:
                    print(f"Análisis de sensibilidad no disponible: {e}")
                return

            self._solucionador.siguiente_iteracion()
            iter_nueva = self._solucionador.obtener_iteracion_actual()
            self._panel_resultado.mostrar_iteracion(iter_nueva)
            self._actualizar_estado_controles()

        except RuntimeError as e:
            messagebox.showerror("Error de resolución", f"Problema: {str(e)}")
            self._actualizar_estado_controles()
        except Exception as e:
            messagebox.showerror("Error inesperado", str(e))
            import traceback
            traceback.print_exc()
            self._actualizar_estado_controles()

    def _actualizar_estado_controles(self):
        """Actualiza el estado visual de los botones según el solucionador."""
        if self._solucionador is None:
            self._btn_siguiente.config(state='disabled', bg=BG_BUTTON_DISABLED, disabledforeground='#666666')
            self._lbl_info.config(text="")
            self._btn_sensibilidad.config(state='disabled', bg=BG_BUTTON_DISABLED, disabledforeground='#666666')
            return

        iter_actual = self._solucionador.obtener_iteracion_actual()
        info_text = (
            f"Iteración {iter_actual.numero_iteracion} | "
            f"{iter_actual.obtener_num_restricciones()} restricciones, "
            f"{iter_actual.obtener_num_variables()} variables"
        )
        self._lbl_info.config(text=info_text)

        if self._solucionador.puede_avanzar():
            self._btn_siguiente.config(state='normal', bg=BG_BUTTON, fg=FG_BUTTON)
            self._btn_sensibilidad.config(state='disabled', bg=BG_BUTTON_DISABLED, disabledforeground='#666666')
        else:
            iter_act = self._solucionador.obtener_iteracion_actual()
            fila_z = iter_act.tableau[0]
            tiene_negativos = any(coef < -1e-9 for coef in fila_z)

            if not tiene_negativos and self._solucionador.resuelto:
                self._btn_siguiente.config(state='disabled', bg=BG_BUTTON, disabledforeground='#888888')
            else:
                self._btn_siguiente.config(state='disabled', bg=BG_BUTTON_DISABLED, disabledforeground='#666666')

            if (not self._solucionador.puede_avanzar()) and (not self._solucionador.en_fase_1) and (not self._solucionador.es_infactible):
                self._btn_sensibilidad.config(state='normal', bg=BG_BUTTON, fg=FG_BUTTON)
            else:
                self._btn_sensibilidad.config(state='disabled', bg=BG_BUTTON_DISABLED, disabledforeground='#666666')

    def _on_toggle_sensibilidad(self):
        """Muestra u oculta la vista de sensibilidad (toggle)."""
        if self._solucionador is None:
            return
        if not self._sensibilidad_cache:
            try:
                sensibilidad = calcular_sensibilidad(self._solucionador)
                self._sensibilidad_cache = sensibilidad
            except Exception as e:
                messagebox.showwarning("Análisis no disponible", str(e))
                return

        if self._sensibilidad_visible:
            try:
                self._panel_resultado.ocultar_sensibilidad()
            except Exception:
                pass
            self._sensibilidad_visible = False
            self._btn_sensibilidad.config(text="Mostrar Sensibilidad")
        else:
            try:
                self._panel_resultado.mostrar_sensibilidad(self._sensibilidad_cache)
            except Exception as e:
                messagebox.showwarning("Análisis no disponible", str(e))
                return
            self._sensibilidad_visible = True
            self._btn_sensibilidad.config(text="Ocultar Sensibilidad")