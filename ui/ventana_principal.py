import tkinter as tk
from tkinter import messagebox
from ui.panel_entrada import PanelEntrada
from ui.panel_resultado import PanelResultado
from core.gran_m import ConstructorPrimerIteracion
from core.solucionador_simplex import SolucionadorSimplex


BG_VENTANA   = "#0f1923"
BG_DERECHO   = "#141e2b"
FG_PLACEHOLDER = "#2d4a6e"


class VentanaPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Programación Lineal - Método Gran M")
        self.geometry("1100x680")
        self.minsize(900, 560)
        self.configure(bg=BG_VENTANA)

        # Centrar ventana en pantalla
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 1100) // 2
        y = (self.winfo_screenheight() - 680)  // 2
        self.geometry(f"1100x680+{x}+{y}")

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

        # Panel derecho: resultados
        self._panel_resultado = PanelResultado(self, bg=BG_DERECHO)
        self._panel_resultado.pack(side="right", fill="both", expand=True)

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
            self._solucionador = SolucionadorSimplex(iteracion_inicial)
            
            # Mostrar primera iteración
            self._panel_resultado.mostrar_iteracion(iteracion_inicial)
            
            # Actualizar estado de botones (TODO: cuando tengamos el botón de siguiente paso)
            
        except ValueError as e:
            messagebox.showerror("Error de validación", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error al resolver: {str(e)}")
            print(f"Traceback completo: {e}")
            import traceback
            traceback.print_exc()