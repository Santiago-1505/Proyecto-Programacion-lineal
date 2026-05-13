import tkinter as tk
from ui.panel_entrada import PanelEntrada


BG_VENTANA   = "#0f1923"
BG_DERECHO   = "#141e2b"
FG_PLACEHOLDER = "#2d4a6e"


class VentanaPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Programación Lineal")
        self.geometry("1100x680")
        self.minsize(900, 560)
        self.configure(bg=BG_VENTANA)

        # Centrar ventana en pantalla
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 1100) // 2
        y = (self.winfo_screenheight() - 680)  // 2
        self.geometry(f"1100x680+{x}+{y}")

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

        # Panel derecho: resultados (placeholder) 
        self._panel_resultado = tk.Frame(self, bg=BG_DERECHO)
        self._panel_resultado.pack(side="right", fill="both", expand=True)

        self._lbl_placeholder = tk.Label(
            self._panel_resultado,
            text="Los pasos de resolución\naparecerán aquí",
            font=("Georgia", 14, "italic"),
            bg=BG_DERECHO, fg=FG_PLACEHOLDER,
            justify="center",
        )
        self._lbl_placeholder.place(relx=0.5, rely=0.5, anchor="center")

    def _on_resolver(self, objetivo: str, tipo_obj: str, restricciones):
        """Callback recibido desde PanelEntrada al pulsar Resolver."""
        # Por ahora imprimimos en consola; aquí se conectará el solver
        print("=" * 50)
        print(f"Objetivo ({tipo_obj.upper()}): Z = {objetivo}")
        print("Restricciones:")
        for r in restricciones:
            print(f"  {r}")
        print("=" * 50)
        # TODO: llamar a SolverGranM y mostrar pasos en panel_resultado