import sys
import os

# Asegurar que el directorio raíz esté en el path para imports relativos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.ventana_principal import VentanaPrincipal

if __name__ == "__main__":
    app = VentanaPrincipal()
    app.mainloop()