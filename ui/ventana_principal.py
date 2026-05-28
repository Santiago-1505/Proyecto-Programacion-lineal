import tkinter as tk
from tkinter import messagebox
from ui.panel_entrada import PanelEntrada
from ui.panel_resultado import PanelResultado
from core.gran_m import ConstructorPrimerIteracion
from core.solucionador_simplex import SolucionadorSimplex


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
        panel_derecho = tk.Frame(self, bg=BG_DERECHO)
        panel_derecho.pack(side="right", fill="both", expand=True)

        # Panel de resultados
        self._panel_resultado = PanelResultado(panel_derecho, bg=BG_DERECHO)
        self._panel_resultado.pack(fill="both", expand=True)

        # Panel de controles en la parte inferior
        self._construir_panel_controles(panel_derecho)

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

        # Botón Siguiente
        self._btn_siguiente = tk.Button(
            frame_interior,
            text="Siguiente Iteración  ▶",
            command=self._on_siguiente_iteracion,
            bg=BG_BUTTON,
            fg=FG_BUTTON,
            font=("Consolas", 11, "bold"),
            padx=20,
            pady=8,
            relief="solid",
            borderwidth=1,
            cursor="hand2",
            state="disabled"
        )
        self._btn_siguiente.pack(side="right", padx=5)
        self._btn_siguiente.bind("<Enter>", lambda e: self._btn_siguiente.config(
            bg=BG_BUTTON_HOVER if self._btn_siguiente["state"] == "normal" else BG_BUTTON_DISABLED
        ))
        self._btn_siguiente.bind("<Leave>", lambda e: self._btn_siguiente.config(
            bg=BG_BUTTON if self._btn_siguiente["state"] == "normal" else BG_BUTTON_DISABLED
        ))

    def _on_resolver(self, objetivo: str, tipo_obj: str, restricciones):
        """Callback recibido desde PanelEntrada al pulsar Resolver."""
        try:
            # Mostrar información en consola (para debugging)
            print("=" * 60)
            print(f"Objetivo ({tipo_obj.upper()}): Z = {objetivo}")
            print("Restricciones:")
            for r in restricciones:
                print(f"  {r}")
            print("=" * 60)
            
            # Construir primera iteración
            constructor = ConstructorPrimerIteracion()
            iteracion_inicial = constructor.construir_tableau_inicial(
                objetivo=objetivo,
                tipo_optimizacion=tipo_obj,
                restricciones=restricciones
            )
            
            # Crear solucionador
            es_minimizacion = (tipo_obj.lower() == "min")
            self._solucionador = SolucionadorSimplex(iteracion_inicial, es_minimizacion)
            
            # Mostrar primera iteración
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
                iter_actual = self._solucionador.obtener_iteracion_actual()
                valor_z = iter_actual.terminos_independientes[0]
                
                mensaje = (
                    "✓ Se alcanzó la solución óptima\n\n"
                    f"Valor de Z: {valor_z:.4f}\n\n"
                    "El botón será deshabilitado ahora."
                )
                messagebox.showinfo("Solución óptima alcanzada", mensaje)
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
        except Exception as e:
            messagebox.showerror("Error inesperado", str(e))
            import traceback
            traceback.print_exc()

    def _actualizar_estado_controles(self):
        """Actualiza el estado de los controles según el solucionador."""
        if self._solucionador is None:
            self._btn_siguiente.config(state="disabled")
            self._lbl_info.config(text="")
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
        if self._solucionador.puede_avanzar():
            self._btn_siguiente.config(state="normal", bg=BG_BUTTON)
        else:
            self._btn_siguiente.config(state="disabled", bg=BG_BUTTON_DISABLED)
