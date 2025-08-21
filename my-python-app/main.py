import os
import json
import pandas as pd
import questionary

from utils.seleccion_archivo import seleccionar_archivo
from utils.cajas import cargar_cajas, agregar_caja, editar_caja, eliminar_caja
import sys


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


DATA_DIR = "data"
OUTPUT_DIR = "output"
CLIENTES_DIR = "clientes"


def cargar_database():
    path = resource_path(os.path.join(DATA_DIR, "database_db.json"))

    if not os.path.exists(path):
        print(f"❌ No se encontró {path}")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def limpiar_consola():
    os.system('cls' if os.name == 'nt' else 'clear')


def seleccionar_owner(database):
    owners = list(database.get("Owners", {}).keys())
    while True:
        limpiar_consola()
        seleccion = questionary.select(
            "Seleccione Owner (0 para volver):",
            choices=owners + ["Volver", "Salir"]
        ).ask()
        if seleccion in [None, "Salir"]:
            return None
        if seleccion == "Volver":
            return "Volver"
        return seleccion


def seleccionar_cliente(database, owner):
    clientes = database.get("Owners", {}).get(owner, [])
    if not clientes:
        print(f"⚠️ No hay clientes para Owner '{owner}'")
        input("Presione Enter para continuar...")
        return None
    while True:
        limpiar_consola()
        seleccion = questionary.select(
            f"Clientes para Owner '{owner}' (0 para volver):",
            choices=clientes + ["Volver", "Salir"]
        ).ask()
        if seleccion in [None, "Salir"]:
            return None
        if seleccion == "Volver":
            return "Volver"
        return seleccion


def cargar_cliente_module(cliente_name):
    import importlib.util
    path = os.path.join(CLIENTES_DIR, f"{cliente_name.lower()}.py")
    if not os.path.exists(path):
        print(f"❌ No se encontró el módulo para cliente '{cliente_name}' en {path}")
        return None
    spec = importlib.util.spec_from_file_location(cliente_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main_menu():
    while True:
        opcion = questionary.select(
            "\n=== Menú Principal ===",
            choices=[
                "Editar cajas",
                "Seleccionar Owner y cliente para ejecutar proceso",
                "Salir"
            ]
        ).ask()
        if opcion == "Editar cajas":
            menu_editar_cajas()
        elif opcion == "Seleccionar Owner y cliente para ejecutar proceso":
            ejecutar_proceso_cliente()
        elif opcion == "Salir" or opcion is None:
            print("Saliendo...")
            break


def menu_editar_cajas():
    cajas = cargar_cajas()
    while True:
        opcion = questionary.select(
            "\n--- Edición de Cajas ---",
            choices=[
                "Listar cajas",
                "Agregar caja",
                "Editar caja",
                "Eliminar caja",
                "Volver"
            ]
        ).ask()
        if opcion == "Listar cajas":
            if not cajas:
                print("No hay cajas registradas.")
            else:
                print("\nCajas actuales:")
                cajas_ordenadas = sorted(cajas, key=lambda x: x["CódigoCaja"])
                print(f"{'Código':<8} | {'Nombre':<15} | {'Alto':>6} | {'Largo':>6} | {'Ancho':>6}")
                print("-" * 50)
                for c in cajas_ordenadas:
                    print(f"{c['CódigoCaja']:<8} | {c['NombreCaja']:<15} | {c['Alto(cm)']:>6} | {c['Largo(cm)']:>6} | {c['Ancho(cm)']:>6}")
            input("Presione Enter para continuar...")
        elif opcion == "Agregar caja":
            agregar_caja_interactivo(cajas)
        elif opcion == "Editar caja":
            editar_caja_interactivo(cajas)
        elif opcion == "Eliminar caja":
            eliminar_caja_interactivo(cajas)
        elif opcion == "Volver" or opcion is None:
            break


def agregar_caja_interactivo(cajas):
    print("\nAgregar nueva caja:")
    codigo = input("CódigoCaja: ").strip()
    nombre = input("NombreCaja: ").strip()
    try:
        alto = int(input("Alto(cm): "))
        largo = int(input("Largo(cm): "))
        ancho = int(input("Ancho(cm): "))
    except ValueError:
        print("❌ Valores numéricos inválidos.")
        return
    nueva = {
        "CódigoCaja": codigo,
        "NombreCaja": nombre,
        "Alto(cm)": alto,
        "Largo(cm)": largo,
        "Ancho(cm)": ancho
    }
    agregar_caja(cajas, nueva)
    print("✅ Caja agregada.")


def editar_caja_interactivo(cajas):
    codigo = input("Ingrese CódigoCaja a editar: ").strip()
    caja = next((c for c in cajas if c["CódigoCaja"] == codigo), None)
    if not caja:
        print("❌ Caja no encontrada.")
        return
    print(f"Editando caja {codigo}. Dejar vacío para no cambiar.")
    nombre = input(f"NombreCaja [{caja['NombreCaja']}]: ").strip()
    alto = input(f"Alto(cm) [{caja['Alto(cm)']}]: ").strip()
    largo = input(f"Largo(cm) [{caja['Largo(cm)']}]: ").strip()
    ancho = input(f"Ancho(cm) [{caja['Ancho(cm)']}]: ").strip()
    cambios = {}
    if nombre:
        cambios["NombreCaja"] = nombre
    if alto:
        try:
            cambios["Alto(cm)"] = float(alto)
        except ValueError:
            print("❌ Alto inválido, no se cambia.")
    if largo:
        try:
            cambios["Largo(cm)"] = float(largo)
        except ValueError:
            print("❌ Largo inválido, no se cambia.")
    if ancho:
        try:
            cambios["Ancho(cm)"] = float(ancho)
        except ValueError:
            print("❌ Ancho inválido, no se cambia.")
    if cambios:
        editar_caja(cajas, codigo, cambios)
        print("✅ Caja editada.")
    else:
        print("No se hicieron cambios.")


def eliminar_caja_interactivo(cajas):
    codigo = input("Ingrese CódigoCaja a eliminar: ").strip()
    if eliminar_caja(cajas, codigo):
        print("✅ Caja eliminada.")
    else:
        print("❌ Caja no encontrada.")


def ejecutar_proceso_cliente():
    database = cargar_database()
    if not database:
        return
    while True:
        owner = seleccionar_owner(database)
        if owner is None:
            return
        if owner == "Volver":
            continue
        clientes = database.get("Owners", {}).get(owner, [])
        if not clientes:
            print(f"⚠️ No hay clientes para Owner '{owner}'")
            input("Presione Enter para continuar...")
            continue
        while True:
            cliente = seleccionar_cliente(database, owner)
            if cliente is None:
                break
            if cliente == "Volver":
                break
            cliente_mod = cargar_cliente_module(cliente)
            if cliente_mod is None or not hasattr(cliente_mod, "run"):
                print(f"❌ El cliente '{cliente}' no tiene función run(df_wms, df_cajas).")
                input("Presione Enter para continuar...")
                return
            print("\nSeleccione archivo WMS (Excel o CSV):")
            archivo_wms = seleccionar_archivo("excel")
            cajas_list = cargar_cajas()
            if not cajas_list:
                print("❌ No se encontraron cajas en data/cajas.txt")
                input("Presione Enter para continuar...")
                return
            df_cajas = pd.DataFrame(cajas_list).sort_values(by="CódigoCaja").reset_index(drop=True)
            try:
                if archivo_wms.lower().endswith(".csv"):
                    df_wms = pd.read_csv(archivo_wms, sep=",", encoding="latin1")
                else:
                    df_wms = pd.read_excel(archivo_wms)
            except Exception as e:
                print(f"❌ Error leyendo archivo WMS: {e}")
                input("Presione Enter para continuar...")
                return
            print(f"\nEjecutando proceso para cliente '{cliente}'...\n")
            cliente_mod.run(df_wms, df_cajas)
            print("\nProceso finalizado.")
            input("Presione Enter para continuar...")
            limpiar_consola()
            return


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(CLIENTES_DIR, exist_ok=True)
    os.makedirs("utils", exist_ok=True)
    main_menu()