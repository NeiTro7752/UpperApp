# utils/seleccion_archivo.py
from tkinter import Tk, filedialog

def seleccionar_archivo(tipo="excel"):
    """
    Abre un diálogo para seleccionar archivo Excel, CSV o TXT.
    :param tipo: "excel", "csv" o "txt"
    :return: ruta del archivo seleccionado o None
    """
    root = Tk()
    root.withdraw()  # Oculta ventana principal
    root.attributes('-topmost', True)  # Poner ventana sobre otras

    if tipo == "excel":
        archivo = filedialog.askopenfilename(
            title="Selecciona archivo Excel",
            filetypes=[("Archivos Excel", "*.xlsx *.XLSX *.xls *.XLS")]
        )
    elif tipo == "csv":
        archivo = filedialog.askopenfilename(
            title="Selecciona archivo CSV",
            filetypes=[("Archivos CSV", "*.csv *.CSV")]
        )
    elif tipo == "txt":
        archivo = filedialog.askopenfilename(
            title="Selecciona archivo TXT",
            filetypes=[("Archivos de texto", "*.txt *.TXT")]
        )
    else:
        archivo = None

    root.destroy()
    if archivo:
        print(f"📂 Archivo seleccionado: {archivo}")
        return archivo
    else:
        print("❌ No se seleccionó archivo.")
        return None
