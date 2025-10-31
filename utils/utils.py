import os
import sys

def resource_path(relative_path):
    """
    Devuelve la ruta absoluta para recursos, compatible con PyInstaller.
    """
    if getattr(sys, 'frozen', False):
        # Si es exe, busca en la carpeta del exe
        base_path = os.path.dirname(sys.executable)
    else:
        # Si es desarrollo, busca en el proyecto
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
