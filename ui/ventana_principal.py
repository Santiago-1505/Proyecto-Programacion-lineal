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


class VentanaPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Programación Lineal - Método Gran M")
        self.geometry("1700x900")
        self.minsize(1000, 700)
        self.configure(bg=BG_VENTANA)

        # Centrar ventana en pantalla
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 1700) // 2
        y = (self.winfo_screenheight() - 900)  // 2
        self.geometry(f"1700x900+{x}+{y}")

        # Estado del solucionador
        self._solucionador = None

        self._construir_layout()

    def _construir_layout(self):
        # Usar tema 'clam' para renderizado consistente entre X11 y Wayland
        # (evita que el WM de X11 sobreescriba estilos de botones deshabilitados)
        style = ttk.Style()
        style.theme_use('clam')

        # Panel izquierdo: entrada del problema
        self._panel_entrada = PanelEntrada(
            self,
            callback_resolver=self._on_resolver,
            bg="#141e2b",
        )
        self._panel_entrada.pack(side="left", fill="y")

        # Separador vertical
        tk.Frame(self, width=2, bg="#2d4a6e").pack(side="left", fill="y")

        # Panel derecho con layout vertical
        self._panel_container = tk.Frame(self, bg=BG_DERECHO)
        self._panel_container.pack(side="right", fill="both", expand=True)

        # Dividir contenedor en area de contenido (arriba) y controles (abajo)
        self._panel_content = tk.Frame(self._panel_container, bg=BG_DERECHO)
        self._panel_content.pack(side="top", fill="both", expand=True)

        self._panel_controls_holder = tk.Frame(self._panel_container, bg=BG_DERECHO)
        self._panel_controls_holder.pack(side="bottom", fill="x")

        # Panel de resultados inicial dentro del content
        self._panel_resultado = PanelResultado(self._panel_content, bg=BG_DERECHO)
        self._panel_resultado.pack(fill="both", expand=True)

        # Panel de controles en la parte inferior del contenedor (use controls holder)
        self._construir_panel_controles(self._panel_controls_holder)

    def _construir_panel_controles(self, parent):
        """Construye el panel de controles con botones de navegación."""
        panel_controles = tk.Frame(parent, bg="#0a1622", height=80)
        panel_controles.pack(side="bottom", fill="x", padx=10, pady=10)
        panel_controles.pack_propagate(False)

        # Frame interior con más paddings
        frame_interior = tk.Frame(panel_controles, bg="#0a1622")
        frame_interior.pack(fill="both", expand=True, padx=10, pady=10)

        # Fila de información
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

        # Configurar estilos ttk para el botón
        # ttk.Button maneja hover/active/disabled automáticamente
        # sin necesidad de bindings <Enter>/<Leave> manuales,
        # evitando condiciones de carrera en X11.
        style = ttk.Style()
        style.configure('Siguiente.TButton',
            background=BG_BUTTON,
            foreground=FG_BUTTON,
            font=("Consolas", 11, "bold"),
            padding=(20, 8),
            borderwidth=1,
            relief="solid",
        )
        style.map('Siguiente.TButton',
            background=[('active', BG_BUTTON_HOVER), ('disabled', BG_BUTTON_DISABLED)],
            foreground=[('disabled', '#666666')],
        )

        style.configure('SiguienteSolved.TButton',
            background=BG_BUTTON,
            foreground=FG_BUTTON,
            font=("Consolas", 11, "bold"),
            padding=(20, 8),
            borderwidth=1,
            relief="solid",
        )
        style.map('SiguienteSolved.TButton',
            background=[('active', BG_BUTTON_HOVER), ('disabled', BG_BUTTON)],
            foreground=[('disabled', '#888888')],
        )

        self._btn_siguiente = ttk.Button(
            frame_interior,
            text="Siguiente Iteración  ▶",
            command=self._on_siguiente_iteracion,
            style='Siguiente.TButton',
            cursor="hand2",
        )
        self._btn_siguiente.pack(side="right", padx=5)
        self._btn_siguiente.state(['disabled'])

        # Botón para mostrar/ocultar Análisis de Sensibilidad (inicialmente oculto)
        self._sensibilidad_visible = False
        self._sensibilidad_cache = None
        self._btn_sensibilidad = ttk.Button(
            frame_interior,
            text="Mostrar Sensibilidad",
            command=self._on_toggle_sensibilidad,
            style='Siguiente.TButton',
            cursor="hand2",
        )
        self._btn_sensibilidad.pack(side="right", padx=5)
        self._btn_sensibilidad.state(['disabled'])

    def _on_resolver(self, objetivo: str, tipo_obj: str, restricciones, metodo: str = 'gran_m'):
        """Callback recibido desde PanelEntrada al pulsar Resolver."""
        try:
            # Mostrar información en consola (para debugging)
            print("=" * 60)
            print(f"Objetivo ({tipo_obj.upper()}): Z = {objetivo}")
            print("Restricciones:")
            for r in restricciones:
                print(f"  {r}")
            print("=" * 60)
            
            if metodo == 'grafico':
                # Renderizar método gráfico (sólo para 2 variables)
                try:
                    from core.graphical_solver import solve_graphical
                except Exception as e:
                    # Problema con el módulo de resolución gráfica
                    messagebox.showerror("Error", f"No se puede cargar el motor gráfico: {e}")
                    return

                # Validar y resolver (solve_graphical lanzará ValueError si >2)
                try:
                    result = solve_graphical(objetivo, tipo_obj, restricciones, include_nonnegativity=True)
                except ValueError:
                    # Re-lanzar para ser capturado por except ValueError externo
                    raise
                except Exception as e:
                    messagebox.showerror("Error", f"Error al calcular la solución gráfica: {e}")
                    return

                # Intentar importar UI gráfico (matplotlib puede faltar)
                try:
                    from ui.panel_grafico import PanelGrafico
                except ImportError:
                    messagebox.showerror(
                        "Dependencia faltante",
                        "Para usar el método gráfico instale matplotlib: pip install matplotlib"
                    )
                    return

                # destruir contenido previo del content frame y colocar panel gráfico
                for child in list(self._panel_content.winfo_children()):
                    child.destroy()
                self._panel_resultado = PanelGrafico(self._panel_content, bg=BG_DERECHO)
                self._panel_resultado.pack(fill="both", expand=True)
                # render puede lanzar excepciones; manejar para no romper la UI
                try:
                    self._panel_resultado.render(result)
                except Exception as e:
                    messagebox.showerror("Error gráfico", f"Error al renderizar el gráfico: {e}")
                    return
                # Disable simplex controls
                self._solucionador = None
                self._actualizar_estado_controles()
            else:
                # Construir primera iteración y usar SolucionadorSimplex (Gran M)
                constructor = ConstructorPrimerIteracion()
                iteracion_inicial = constructor.construir_tableau_inicial(
                    objetivo=objetivo,
                    tipo_optimizacion=tipo_obj,
                    restricciones=restricciones
                )
                # Crear solucionador
                es_minimizacion = (tipo_obj.lower() == "min")
                self._solucionador = SolucionadorSimplex(iteracion_inicial, es_minimizacion)
                # Mostrar primera iteración (limpiar content frame y crear panel)
                for child in list(self._panel_content.winfo_children()):
                    child.destroy()
                self._panel_resultado = PanelResultado(self._panel_content, bg=BG_DERECHO)
                self._panel_resultado.pack(fill="both", expand=True)
                self._panel_resultado.mostrar_iteracion(iteracion_inicial)
                # Actualizar estado de botón
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
                # Asegurar que el estado visual de los controles se actualice
                self._actualizar_estado_controles()

                # Calcular y mostrar análisis de sensibilidad (no intrusivo en UI)
                try:
                    sensibilidad = calcular_sensibilidad(self._solucionador)
                    self._sensibilidad_cache = sensibilidad
                    self._sensibilidad_visible = True
                    self._panel_resultado.mostrar_sensibilidad(sensibilidad)
                except Exception as e:
                    # Mostrar mensaje no intrusivo si análisis no es aplicable
                    print(f"Análisis de sensibilidad no disponible: {e}")
                return

            # Avanzar a siguiente iteración
            self._solucionador.siguiente_iteracion()

            # Mostrar nueva iteración
            iter_nueva = self._solucionador.obtener_iteracion_actual()
            self._panel_resultado.mostrar_iteracion(iter_nueva)

            # Actualizar controles
            self._actualizar_estado_controles()
            
        except RuntimeError as e:
            messagebox.showerror("Error de resolución", f"Problema: {str(e)}")
            # Asegurar actualización del estado de controles tras error
            self._actualizar_estado_controles()
        except Exception as e:
            messagebox.showerror("Error inesperado", str(e))
            import traceback
            traceback.print_exc()
            # También actualizar controles en caso de excepción inesperada
            self._actualizar_estado_controles()

    def _actualizar_estado_controles(self):
        """Actualiza el estado de los controles según el solucionador."""
        if self._solucionador is None:
            self._btn_siguiente.state(['disabled'])
            self._btn_siguiente.configure(style='Siguiente.TButton')
            self._lbl_info.config(text="")
            self._btn_sensibilidad.state(['disabled'])
            return

        iter_actual = self._solucionador.obtener_iteracion_actual()
        
        # Actualizar etiqueta informativa
        num_iters = len(self._solucionador.iteraciones)
        info_text = (
            f"Iteración {iter_actual.numero_iteracion} | "
            f"{iter_actual.obtener_num_restricciones()} restricciones, "
            f"{iter_actual.obtener_num_variables()} variables"
        )
        self._lbl_info.config(text=info_text)

        # Habilitar/deshabilitar botón según si puede avanzar
        # ttk.Button maneja colores automáticamente via style.map,
        # sin bindings <Enter>/<Leave> que causan race conditions en X11.
        if self._solucionador.puede_avanzar():
            self._btn_siguiente.state(['!disabled'])
            self._btn_siguiente.configure(style='Siguiente.TButton')
            # Mientras no esté resuelto no permitimos togglear sensibilidad
            self._btn_sensibilidad.state(['disabled'])
        else:
            iter_act = self._solucionador.obtener_iteracion_actual()
            fila_z = iter_act.tableau[0]
            tiene_negativos = any(coef < -1e-9 for coef in fila_z)

            if not tiene_negativos and self._solucionador.resuelto:
                self._btn_siguiente.configure(style='SiguienteSolved.TButton')
            else:
                self._btn_siguiente.configure(style='Siguiente.TButton')
            self._btn_siguiente.state(['disabled'])
            # Habilitar botón de sensibilidad si el solucionador no puede avanzar
            # y no está en fase 1 ni es infactible
            if (not self._solucionador.puede_avanzar()) and (not self._solucionador.en_fase_1) and (not self._solucionador.es_infactible):
                self._btn_sensibilidad.state(['!disabled'])
            else:
                self._btn_sensibilidad.state(['disabled'])

    def _on_toggle_sensibilidad(self):
        """Muestra u oculta la vista de sensibilidad (toggle)."""
        if self._solucionador is None:
            return
        # Si no hay cache, intentar calcular
        if not self._sensibilidad_cache:
            try:
                sensibilidad = calcular_sensibilidad(self._solucionador)
                self._sensibilidad_cache = sensibilidad
            except Exception as e:
                messagebox.showwarning("Análisis no disponible", str(e))
                return

        if self._sensibilidad_visible:
            # Ocultar
            try:
                self._panel_resultado.ocultar_sensibilidad()
            except Exception:
                pass
            self._sensibilidad_visible = False
            self._btn_sensibilidad.config(text="Mostrar Sensibilidad")
        else:
            # Mostrar
            try:
                self._panel_resultado.mostrar_sensibilidad(self._sensibilidad_cache)
            except Exception as e:
                messagebox.showwarning("Análisis no disponible", str(e))
                return
            self._sensibilidad_visible = True
            self._btn_sensibilidad.config(text="Ocultar Sensibilidad")
