# utils/cajas.py
import os

DATA_DIR = "data"
CAJAS_FILE = os.path.join(DATA_DIR, "cajas.txt")

def cargar_cajas():
    """
    Lee cajas desde cajas.txt y devuelve lista de dicts.
    """
    cajas = []
    if not os.path.exists(CAJAS_FILE):
        return cajas
    with open(CAJAS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) != 5:
                continue
            codigo, nombre, alto, largo, ancho = parts
            try:
                cajas.append({
                    "CódigoCaja": codigo,
                    "NombreCaja": nombre,
                    "Alto(cm)": int(alto),
                    "Largo(cm)": int(largo),
                    "Ancho(cm)": int(ancho)
                })
            except ValueError:
                # Ignorar líneas con datos inválidos
                continue
    return cajas

def guardar_cajas(cajas):
    """
    Guarda la lista de cajas en cajas.txt con formato delimitado por '|'.
    """
    with open(CAJAS_FILE, "w", encoding="utf-8") as f:
        for c in cajas:
            line = f"{c['CódigoCaja']} | {c['NombreCaja']} | {c['Alto(cm)']} | {c['Largo(cm)']} | {c['Ancho(cm)']}\n"
            f.write(line)

def agregar_caja(cajas, nueva_caja):
    """
    Agrega una nueva caja a la lista y guarda.
    :param cajas: lista actual de cajas
    :param nueva_caja: dict con claves CódigoCaja, NombreCaja, Alto(cm), Largo(cm), Ancho(cm)
    """
    cajas.append(nueva_caja)
    guardar_cajas(cajas)

def editar_caja(cajas, codigo_caja, cambios):
    """
    Edita una caja existente identificada por código.
    :param cajas: lista actual de cajas
    :param codigo_caja: código de caja a editar
    :param cambios: dict con campos a modificar
    :return: True si editado, False si no encontrado
    """
    for c in cajas:
        if c["CódigoCaja"] == codigo_caja:
            c.update(cambios)
            guardar_cajas(cajas)
            return True
    return False

def eliminar_caja(cajas, codigo_caja):
    """
    Elimina una caja por código.
    :param cajas: lista actual de cajas
    :param codigo_caja: código de caja a eliminar
    :return: True si eliminado, False si no encontrado
    """
    for i, c in enumerate(cajas):
        if c["CódigoCaja"] == codigo_caja:
            cajas.pop(i)
            guardar_cajas(cajas)
            return True
    return False