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
    for idx, p in enumerate(pallets, start=1):
        # Agregar posiciones
        posiciones_list.extend(p["Posiciones"])

        # Agregar un solo bulto por pallet con peso total y dimensiones
        pesos.append(p["Peso (kg)"])
        altos.append(p["Alto (cm)"])
        largos.append(p["Largo (cm)"])
        anchos.append(p["Ancho (cm)"])
        nombre_caja.append("Pallet")
        lpn_list.append(f"Pallet{idx}")  # o cualquier identificador único para el pallet

    # Separar datos para pallets y bultos
    # Crear DataFrames separados para pallets y bultos
    # Pallets: bultos y posiciones
    pesos_pallets, altos_pallets, largos_pallets, anchos_pallets, nombre_caja_pallets, lpn_list_pallets = [], [], [], [], [], []
    posiciones_pallets = []

    # Bultos: bultos y posiciones
    pesos_bultos, altos_bultos, largos_bultos, anchos_bultos, nombre_caja_bultos, lpn_list_bultos = [], [], [], [], [], []
    posiciones_bultos = []

    # LPNs de pallets
    lpns_pallets_set = set()
    for p in pallets:
        lpns_pallets_set.update(p["LPNs"])

    # Distribuir bultos y posiciones según LPN
    for i, lpn in enumerate(lpn_list):
        peso = pesos[i]
        alto = altos[i]
        largo = largos[i]
        ancho = anchos[i]
        nombre = nombre_caja[i]

        if lpn in lpns_pallets_set:
            pesos_pallets.append(peso)
            altos_pallets.append(alto)
            largos_pallets.append(largo)
            anchos_pallets.append(ancho)
            nombre_caja_pallets.append(nombre)
            lpn_list_pallets.append(lpn)
        else:
            pesos_bultos.append(peso)
            altos_bultos.append(alto)
            largos_bultos.append(largo)
            anchos_bultos.append(ancho)
            nombre_caja_bultos.append(nombre)
            lpn_list_bultos.append(lpn)

    # Separar posiciones
    for pos in posiciones_list:
        # Para cada posición, verificar si su LPN está en pallets o bultos
        # Como posiciones_list no tiene LPN, usamos bulto para relacionar con lpn_list
        bulto_idx = pos["Bulto"] - 1  # índice base 0
        if 0 <= bulto_idx < len(lpn_list):
            lpn_pos = lpn_list[bulto_idx]
            if lpn_pos in lpns_pallets_set:
                posiciones_pallets.append(pos)
            else:
                posiciones_bultos.append(pos)
        else:
            # Si no se puede determinar, asignar a bultos por defecto
            posiciones_bultos.append(pos)

    # Crear DataFrames para pallets
    df_bultos_pallets = pd.DataFrame()
    df_bultos_pallets["Bulto"] = range(1, len(pesos_pallets) + 1)
    df_bultos_pallets["Peso"] = pesos_pallets
    df_bultos_pallets["Unidad"] = "KG"
    df_bultos_pallets["Altura"] = [h / 100 for h in altos_pallets]
    df_bultos_pallets["Unidad_1"] = "M"
    df_bultos_pallets["Longitud"] = [l / 100 for l in largos_pallets]
    df_bultos_pallets["Unidad_2"] = "M"
    df_bultos_pallets["Ancho"] = [a / 100 for a in anchos_pallets]
    df_bultos_pallets["Unidad_3"] = "M"

    # Agrupar posiciones de cada pallet sumando cantidades y asignando Bulto correcto
    posiciones_pallets_agrupadas = []
    for idx, p in enumerate(pallets, start=1):
        # Agrupar posiciones por Pos, Material y Unidad sumando Cantidad
        df_pos = pd.DataFrame(p["Posiciones"])
        if df_pos.empty:
            continue
        df_pos_grouped = df_pos.groupby(["Pos", "Material", "Unidad"], as_index=False)["Cantidad"].sum()
        # Asignar número de bulto según pallet (1, 2, 3, ...)
        df_pos_grouped["Bulto"] = idx
        posiciones_pallets_agrupadas.append(df_pos_grouped)

    # Concatenar todas las posiciones agrupadas de pallets
    if posiciones_pallets_agrupadas:
        df_posiciones_pallets = pd.concat(posiciones_pallets_agrupadas, ignore_index=True)
    else:
        df_posiciones_pallets = pd.DataFrame(columns=["Pos", "Material", "Cantidad", "Unidad", "Bulto"])

    df_posiciones_pallets = pd.DataFrame(posiciones_pallets)

    # Crear DataFrame de bultos de pallets con un bulto por pallet
    df_bultos_pallets = pd.DataFrame({
        "Bulto": range(1, len(pallets) + 1),
        "Peso": [p["Peso (kg)"] for p in pallets],
        "Unidad": "KG",
        "Altura": [p["Alto (cm)"] / 100 for p in pallets],
        "Unidad_1": "M",
        "Longitud": [p["Largo (cm)"] / 100 for p in pallets],
        "Unidad_2": "M",
        "Ancho": [p["Ancho (cm)"] / 100 for p in pallets],
        "Unidad_3": "M"
    })

    # Crear DataFrames para bultos
    df_bultos_bultos = pd.DataFrame()
    df_bultos_bultos["Bulto"] = range(1, len(pesos_bultos) + 1)
    df_bultos_bultos["Peso"] = pesos_bultos
    df_bultos_bultos["Unidad"] = "KG"
    df_bultos_bultos["Altura"] = [h / 100 for h in altos_bultos]
    df_bultos_bultos["Unidad_1"] = "M"
    df_bultos_bultos["Longitud"] = [l / 100 for l in largos_bultos]
    df_bultos_bultos["Unidad_2"] = "M"
    df_bultos_bultos["Ancho"] = [a / 100 for a in anchos_bultos]
    df_bultos_bultos["Unidad_3"] = "M"

    df_posiciones_bultos = pd.DataFrame(posiciones_bultos)

    # Crear carpeta de salida específica
    output_folder = "output/agunsa"
    os.makedirs(output_folder, exist_ok=True)

    # Guardar archivos Excel separados para pallets
    path_bultos_pallets = os.path.join(output_folder, "pallet_bultos.xlsx")
    path_posiciones_pallets = os.path.join(output_folder, "pallet_posiciones.xlsx")

    df_bultos_pallets.to_excel(path_bultos_pallets, index=False)
    df_posiciones_pallets.to_excel(path_posiciones_pallets, index=False)

    # Guardar archivos Excel separados para bultos
    path_bultos_bultos = os.path.join(output_folder, "bultos_bultos.xlsx")
    path_posiciones_bultos = os.path.join(output_folder, "bultos_posiciones.xlsx")

    df_bultos_bultos.to_excel(path_bultos_bultos, index=False)
    df_posiciones_bultos.to_excel(path_posiciones_bultos, index=False)

    print("\n✅ Archivos generados en carpeta 'output/agunsa':")
    print(f" - {path_bultos_pallets}")
    print(f" - {path_posiciones_pallets}")
    print(f" - {path_bultos_bultos}")
    print(f" - {path_posiciones_bultos}")

    time.sleep(1)
    os.system('cls')    

    # Impresión de guía
    respuesta = input("\n¿Desea imprimir el detalle para la creación de guía? (s/n): ").strip().lower()
    if respuesta == "s":
        # Obtener LPNs de pallets y bultos
        lpns_pallets = set()
        for p in pallets:
            lpns_pallets.update(p["LPNs"])
        lpns_bultos = set(lpn_list) - lpns_pallets

        # Para pallets, obtener posiciones sumando desde df_wms filtrando por LPNs pallets
        posiciones_pallets = []
        for lpn in lpns_pallets:
            grupo = df_wms[df_wms["LPN"] == lpn]
            for idx, row in grupo.iterrows():
                coditem = str(row["CodItem"])
                pos = pos_material_por_coditem[coditem]["Pos"]
                material = pos_material_por_coditem[coditem]["Material"]
                posiciones_pallets.append({
                    "Pos": pos,
                    "Material": material,
                    "Cantidad": row["Unidades"],
                    "Unidad": "UN"
                })

        # Para bultos, obtener posiciones filtrando df_wms por LPNs bultos
        posiciones_bultos = []
        for lpn in lpns_bultos:
            grupo = df_wms[df_wms["LPN"] == lpn]
            for idx, row in grupo.iterrows():
                coditem = str(row["CodItem"])
                pos = pos_material_por_coditem[coditem]["Pos"]
                material = pos_material_por_coditem[coditem]["Material"]
                posiciones_bultos.append({
                    "Pos": pos,
                    "Material": material,
                    "Cantidad": row["Unidades"],
                    "Unidad": "UN"
                })

        def imprimir_guia(tipo_envio, posiciones):
            resumen = {}
            for pos in posiciones:
                mat = pos["Material"]
                cant = pos["Cantidad"]
                resumen[mat] = resumen.get(mat, 0) + cant

            print(f"\nGuía de {tipo_envio}:")
            print(f"{'CodItem':<12} {'NomItem':<50} {'Cantidad':>8} {'Unidad':>6}")
            print("-" * 80)
            for material, cantidad in resumen.items():
                nomitem = ""
                # Buscar NomItem en coditem_db usando material
                if material in coditem_db:
                    nomitem = coditem_db[material].get("NomItem", "")
                else:
                    for v in coditem_db.values():
                        if str(v.get("Material", "")) == material:
                            nomitem = v.get("NomItem", "")
                            break
                print(f"{material:<12} {nomitem:<50} {cantidad:>8} UN")

            # Mostrar LPNs únicos en la guía, limpiando prefijo SAL0000...
            def limpiar_lpn(lpn):
                if lpn.upper().startswith("SAL"):
                    m = re.match(r"(SAL)0*(\d+)", lpn.upper())
                    if m:
                        return f"{m.group(1)}{m.group(2)}"
                return lpn

            # LPNs para este tipo de envío
            if tipo_envio == "Pallets":
                lpns = lpns_pallets
            else:
                lpns = lpns_bultos

            lpns_limpios = [limpiar_lpn(lpn) for lpn in sorted(lpns)]
            print("\nLPNs en la guía:")
            print(" ".join(lpns_limpios))

        # Imprimir guía para pallets y bultos
        if posiciones_pallets:
            imprimir_guia("Pallets", posiciones_pallets)
        if posiciones_bultos:
            imprimir_guia("Bultos", posiciones_bultos)
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