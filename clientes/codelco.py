# clientes/codelco.py
import json
import os
import re
import pandas as pd
import time
import questionary
from utils.coditem_utils import validar_o_actualizar_material

def run(df_wms, df_cajas):
    """
    Proceso para cliente Codelco.
    Recibe df_wms y df_cajas, interactúa con usuario para ingresar pesos, seleccionar cajas,
    asignar posiciones y materiales, luego genera archivos Excel con resultados.
    """
    print("🟩 Iniciando proceso CODELCO...\n")

    # Cargar base coditem_db una sola vez para usar en todo el proceso
    coditem_db_path = "data/coditem_db.json"
    if os.path.exists(coditem_db_path):
        with open(coditem_db_path, "r", encoding="utf-8") as f:
            coditem_db = json.load(f)
    else:
        coditem_db = {}

    # Obtener CodItems únicos de la OC
    coditems_unicos = df_wms["CodItem"].astype(str).unique().tolist()
    pos_material_por_coditem = {}

    # Preguntar posición y material solo una vez por CodItem
    for coditem in coditems_unicos:
        os.system('cls')
        nomitem = coditem_db.get(coditem, {}).get("NomItem", "")
        material_existente = coditem_db.get(coditem, {}).get("Material", "")
        print(f"CodItem: {coditem} | NomItem: {nomitem}")

        if material_existente:
            print(f"Material encontrado en base: '{material_existente}'")
            material = material_existente
        else:
            # Pedir material al usuario
            while True:
                material = input(f"Ingrese Material para CodItem {coditem} (dejar vacío para usar CodItem): ").strip()
                if not material:
                    material = coditem
                confirm = input(f"¿Es correcto el Material '{material}'? (s/n): ").strip().lower()
                if confirm == "s":
                    break

        pos = input(f"Ingrese Posición (Pos) para CodItem {coditem}: ").strip()
        pos_material_por_coditem[coditem] = {"Pos": pos, "Material": material}

    lleva_pallets = input("¿El pedido lleva pallets? (s/n): ").strip().lower()

    # Cargar base coditem_db una sola vez para usar en todo el proceso
    coditem_db_path = "data/coditem_db.json"
    if os.path.exists(coditem_db_path):
        with open(coditem_db_path, "r", encoding="utf-8") as f:
            coditem_db = json.load(f)
    else:
        coditem_db = {}

    pallets = []
    remaining_lpns = df_wms["LPN"].drop_duplicates().tolist()

    if lleva_pallets == "s":
        pallet_num = 1
        while remaining_lpns:
            os.system('cls')  # Limpiar consola antes de pedir selección de LPNs para pallet
            print(f"\n📦 Selección de LPNs para Pallet {pallet_num}:")

            # Usar questionary checkbox para selección múltiple
            selected_lpns = questionary.checkbox(
                "Selecciona los LPNs para este pallet:",
                choices=remaining_lpns
            ).ask()

            if not selected_lpns:
                print("❌ Debes seleccionar al menos un LPN.")
                continue

            # --- Pedir peso y dimensiones solo una vez por pallet ---
            while True:
                try:
                    peso = float(input(f"⚖️ Peso total del Pallet {pallet_num} (kg): "))
                    alto = float(input(f"📏 Altura del Pallet {pallet_num} (cm): "))
                    largo = float(input(f"📏 Longitud del Pallet {pallet_num} (cm): "))
                    ancho = float(input(f"📏 Ancho del Pallet {pallet_num} (cm): "))
                    break
                except ValueError:
                    print("❌ Ingresa valores válidos.")

            # Para cada LPN seleccionado, pedir Pos y Material para cada item dentro
            posiciones_list_pallet = []
            bulto_num_pallet = 1  # Contador local para bultos dentro del pallet
            for lpn in selected_lpns:
                grupo = df_wms[df_wms["LPN"] == lpn]
                print(f"\n📦 Procesando LPN {lpn} dentro de Pallet {pallet_num} con {len(grupo)} items")

                for idx, row in grupo.iterrows():
                    coditem = str(row["CodItem"])
                    # Usar la info ya pedida al inicio
                    pos = pos_material_por_coditem[coditem]["Pos"]
                    material = pos_material_por_coditem[coditem]["Material"]

                    posiciones_list_pallet.append({
                        "Pos": pos,
                        "Material": material,
                        "Cantidad": row["Unidades"],
                        "Unidad": "UN",
                        "Bulto": bulto_num_pallet
                    })

                bulto_num_pallet += 1

            pallets.append({
                "Pallet": f"Pallet{pallet_num}",
                "LPNs": selected_lpns,
                "Peso (kg)": peso,
                "Alto (cm)": alto,
                "Largo (cm)": largo,
                "Ancho (cm)": ancho,
                "Posiciones": posiciones_list_pallet  # Guardar posiciones para luego agregar
            })

            # Actualizar remaining_lpns removiendo los seleccionados
            remaining_lpns = [lpn for lpn in remaining_lpns if lpn not in selected_lpns]

            if not remaining_lpns or input("¿Más pallets? (s/n): ").strip().lower() != "s":
                break

            pallet_num += 1

    # Procesar LPNs restantes (o todos si no hay pallets)
    lpns_a_procesar = remaining_lpns if lleva_pallets == "s" else df_wms["LPN"].tolist()
    df_filtrado = df_wms[df_wms["LPN"].isin(lpns_a_procesar)]

    # Variables para bultos y posiciones
    pesos, altos, largos, anchos, nombre_caja, lpn_list = [], [], [], [], [], []
    posiciones_list = []

    bulto_num = 1

    # Procesar cada LPN como un bulto (solo los que no están en pallets)
    for lpn in lpns_a_procesar:
        grupo = df_filtrado[df_filtrado["LPN"] == lpn]
        print(f"\n📦 Procesando LPN: {lpn} con {len(grupo)} items")

        while True:
            try:
                peso = float(input(f"⚖️ Peso real (kg) para LPN {lpn}: "))
                break
            except ValueError:
                print("❌ Ingresa un número válido.")

        # Limpiar consola antes de seleccionar caja para mejor experiencia
        os.system('cls')
        print("\n📦 Tipos de caja:")
        for i, caja in df_cajas.iterrows():
            print(f"{i}. {caja['NombreCaja']} - {caja['Alto(cm)']}x{caja['Largo(cm)']}x{caja['Ancho(cm)']}")

        while True:
            try:
                opcion = int(input("Selecciona el número de caja: "))
                caja_sel = df_cajas.iloc[opcion]
                break
            except (ValueError, IndexError):
                print("❌ Selección inválida.")

        pesos.append(peso)
        altos.append(caja_sel["Alto(cm)"])
        largos.append(caja_sel["Largo(cm)"])
        anchos.append(caja_sel["Ancho(cm)"])
        nombre_caja.append(caja_sel["NombreCaja"])
        lpn_list.append(lpn)

        for idx, row in grupo.iterrows():
            coditem = str(row["CodItem"])
            unidades = row["Unidades"]

            pos = pos_material_por_coditem[coditem]["Pos"]
            material = pos_material_por_coditem[coditem]["Material"]

            posiciones_list.append({
                "Pos": pos,
                "Material": material,
                "Cantidad": unidades,
                "Unidad": "UN",
                "Bulto": bulto_num
            })

        bulto_num += 1

    # Agregar posiciones de pallets a posiciones_list y bultos de pallets a df_bultos
    for p in pallets:
        # Agregar posiciones
        posiciones_list.extend(p["Posiciones"])

        # Agregar bultos de pallet al df_bultos
        for i, lpn in enumerate(p["LPNs"], start=1):
            pesos.append(p["Peso (kg)"] / len(p["LPNs"]))  # Distribuir peso entre LPNs
            altos.append(p["Alto (cm)"])
            largos.append(p["Largo (cm)"])
            anchos.append(p["Ancho (cm)"])
            nombre_caja.append("Pallet")
            lpn_list.append(lpn)

    # Crear DataFrame bultos
    df_bultos = pd.DataFrame()
    df_bultos["Bulto"] = range(1, len(pesos) + 1)
    df_bultos["Peso"] = pesos
    df_bultos["Unidad"] = "KG"
    df_bultos["Altura"] = [h / 100 for h in altos]
    df_bultos["Unidad_1"] = "M"
    df_bultos["Longitud"] = [l / 100 for l in largos]
    df_bultos["Unidad_2"] = "M"
    df_bultos["Ancho"] = [a / 100 for a in anchos]
    df_bultos["Unidad_3"] = "M"

    # Crear DataFrame posiciones
    df_posiciones = pd.DataFrame(posiciones_list)

    if "Material" not in df_posiciones.columns or df_posiciones.empty:
        print("❌ No hay datos de posiciones con columna 'Material' para generar la guía.")
        return  # O manejar según convenga

    # Guardar archivos Excel
    with pd.ExcelWriter("output/bultos_codelco.xlsx") as writer:
        df_bultos.to_excel(writer, sheet_name="Bultos", index=False)
    df_posiciones.to_excel("output/posiciones_codelco.xlsx", index=False)

    print("\n✅ Archivos generados: bultos_codelco.xlsx y posiciones_codelco.xlsx")
    time.sleep(1)
    os.system('cls')    

    # Impresión de guía
    respuesta = input("\n¿Desea imprimir el detalle para la creación de guía? (s/n): ").strip().lower()
    if respuesta == "s":
        # print(coditem_db)
        resumen = df_posiciones.groupby("Material").agg({"Cantidad": "sum"}).reset_index()

        print("\nGuía de Bultos:")
        print(f"{'CodItem':<12} {'NomItem':<50} {'Cantidad':>8} {'Unidad':>6}")
        print("-" * 80)
        for _, r in resumen.iterrows():
            material = str(r["Material"])
            cantidad = r["Cantidad"]
            nomitem = r.get("NomItem", "")

            # Obtener nombre desde coditem_db usando material como clave
            if material in coditem_db:
                nomitem = coditem_db[material].get("NomItem", "")
            else:
                # Buscar en valores si no está como clave
                for v in coditem_db.values():
                    if str(v.get("Material", "")) == material:
                        nomitem = v.get("NomItem", "")
                        break

            print(f"{coditem:<12} {nomitem:<50} {cantidad:>8} UN")

        # Mostrar LPNs únicos en la guía, limpiando prefijo SAL0000...
        def limpiar_lpn(lpn):
            if lpn.upper().startswith("SAL"):
                m = re.match(r"(SAL)0*(\d+)", lpn.upper())
                if m:
                    return f"{m.group(1)}{m.group(2)}"
            return lpn

        lpns_usados = list(set(lpn_list))  # Unicos
        lpns_limpios = [limpiar_lpn(lpn) for lpn in lpns_usados]
        print("\nLPNs en la guía:")
        print(" ".join(lpns_limpios))

def pedir_pos_y_material(coditems_unicos, coditem_db):
    pos_material_por_coditem = {}
    for coditem in coditems_unicos:
        os.system('cls')  # Limpiar consola para no saturar
        print(f"Configurando CodItem: {coditem}")
        pos = input(f"Ingrese Posición (Pos) para CodItem {coditem}: ").strip()
        # Usar función existente para validar o actualizar material
        nomitem = coditem_db.get(coditem, {}).get("NomItem", "")
        material = validar_o_actualizar_material(coditem, nomitem)
        pos_material_por_coditem[coditem] = {"Pos": pos, "Material": material}
    return pos_material_por_coditem

def actualizar_coditem_db(df_wms, coditem_db_path="data/coditem_db.json"):
    """
    Actualiza coditem_db.json con nuevos CodItem que aparecen en df_wms pero no están en la base.
    """
    if os.path.exists(coditem_db_path):
        with open(coditem_db_path, "r", encoding="utf-8") as f:
            coditem_db = json.load(f)
    else:
        coditem_db = {}

    # Convert keys to str to avoid int64 keys causing JSON dump error
    coditem_db = {str(k): v for k, v in coditem_db.items()}

    nuevos_coditems = set(df_wms["CodItem"].astype(str).unique()) - set(coditem_db.keys())
    if nuevos_coditems:
        print(f"Se encontraron {len(nuevos_coditems)} nuevos CodItem. Se agregarán a la base.")
        for coditem in nuevos_coditems:
            # Obtener nomitem con la función corregida
            nomitem = new_func(df_wms, coditem)
            coditem_db[coditem] = {"NomItem": nomitem}

        with open(coditem_db_path, "w", encoding="utf-8") as f:
            json.dump(coditem_db, f, indent=2, ensure_ascii=False)
    else:
        print("No se encontraron nuevos CodItem.")

    return coditem_db

def new_func(df_wms, coditem):
    coditem_str = str(coditem)
    filtro = df_wms["CodItem"].astype(str) == coditem_str
    if filtro.any():
        nomitem = df_wms.loc[filtro, "NomItem"].iloc[0]
        if pd.isna(nomitem):
            nomitem = ""
    else:
        nomitem = ""
    return nomitem