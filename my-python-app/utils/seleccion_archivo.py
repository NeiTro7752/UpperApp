def seleccionar_archivo(tipo_archivo):
    import questionary
    import os

    if tipo_archivo == "excel":
        extensions = [".xlsx", ".xls", ".csv"]
    else:
        extensions = []

    archivo = questionary.select(
        "Seleccione un archivo:",
        choices=[f for f in os.listdir() if os.path.splitext(f)[1] in extensions]
    ).ask()

    return archivo if archivo else None