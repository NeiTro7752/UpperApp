# clientes/collahuasi.py
import json
import os
import pandas as pd
import questionary  # <-- Agregado import de questionary
from utils.comunes import agrupar_cajas, agrupar_unidades_por_coditem


def run(df_wms, df_cajas):
    """
    Proceso para cliente Collahuasi.
    Recibe df_wms y df_cajas, interactúa con usuario para definir pallets y cajas,
    luego genera archivo Excel con resultados.
    """
    print("\n🟦 Iniciando proceso Collahuasi...\n")

    remaining_lpns = df_wms["LPN"].tolist()
    pallets = []
    pallet_num = 1

    lleva_pallets = input("¿El pedido lleva pallets? (s/n): ").strip().lower()
    if lleva_pallets == "s":
        while remaining_lpns:
            print(f"\n📦 Selección de LPNs para Pallet {pallet_num}:")

            # Usar questionary checkbox para selección múltiple de LPNs
            selected_lpns = questionary.checkbox(
                "Selecciona los LPNs para este pallet:",
                choices=remaining_lpns
            ).ask()

            if not selected_lpns:
                print("❌ Debes seleccionar al menos un LPN.")
                continue

            while True:
                try:
                    peso = float(input(f"⚖️ Peso total del Pallet {pallet_num} (kg): "))
                    alto = float(input(f"📏 Altura del Pallet {pallet_num} (cm): "))
                    largo = float(input(f"📏 Longitud del Pallet {pallet_num} (cm): "))
                    ancho = float(input(f"📏 Ancho del Pallet {pallet_num} (cm): "))
                    break
                except ValueError:
                    print("❌ Ingresa valores válidos.")

            pallets.append({
                "Pallet": f"Pallet{pallet_num}",
                "LPNs": selected_lpns,
                "Peso (kg)": peso,
                "Alto (cm)": alto,
                "Largo (cm)": largo,
                "Ancho (cm)": ancho
            })

            # Actualizar remaining_lpns removiendo los seleccionados
            remaining_lpns = [lpn for lpn in remaining_lpns if lpn not in selected_lpns]

            if not remaining_lpns or input("¿Más pallets? (s/n): ").strip().lower() != "s":
                break

            pallet_num += 1

    print("\n🟩 Registro de peso y tipo de caja...\n")

    pesos, altos, largos, anchos, nombre_caja, lpn_list = [], [], [], [], [], []

    lpns_to_process = remaining_lpns if lleva_pallets == "s" else df_wms["LPN"].tolist()
    df_filtrado = df_wms[df_wms["LPN"].isin(lpns_to_process)]

    conteo = df_filtrado["LPN"].value_counts()
    lpn_repetidos = conteo[conteo > 1].index.tolist()
    lpn_unicos = conteo[conteo == 1].index.tolist()

    for lpn in lpn_repetidos:
        grupo = df_filtrado[df_filtrado["LPN"] == lpn]
        print(f"\n🔁 LPN repetido: {lpn} ({len(grupo)} items)")
        print(f"   CodItems: {list(grupo['CodItem'])}")

        while True:
            try:
                peso = float(input("⚖️  Peso total de la caja (kg): "))
                break
            except ValueError:
                print("❌ Número inválido.")

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

    for lpn in lpn_unicos:
        row = df_filtrado[df_filtrado["LPN"] == lpn].iloc[0]
        print(f"\n🔹 LPN único: {lpn} | CodItem: {row['CodItem']} | Unidades: {row['Unidades']}")

        while True:
            try:
                peso = float(input("⚖️  Peso (kg): "))
                break
            except ValueError:
                print("❌ Número inválido.")

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

    df_bultos = pd.DataFrame({
        "LPN": lpn_list,
        "Peso (kg)": pesos,
        "TipoCaja": nombre_caja,
        "Alto (cm)": altos,
        "Largo (cm)": largos,
        "Ancho (cm)": anchos,
    })

    if pallets:
        pallet_rows = []
        for p in pallets:
            for lpn in p["LPNs"]:
                pallet_rows.append({
                    "Pallet": p["Pallet"],
                    "LPN": lpn,
                    "Peso (kg)": p["Peso (kg)"],
                    "Alto (cm)": p["Alto (cm)"],
                    "Largo (cm)": p["Largo (cm)"],
                    "Ancho (cm)": p["Ancho (cm)"]
                })
        df_pallets = pd.DataFrame(pallet_rows)
    else:
        df_pallets = pd.DataFrame()

    with pd.ExcelWriter("output/bultos_pedido_collahuasi.xlsx") as writer:
        if not df_pallets.empty:
            df_pallets.to_excel(writer, sheet_name="Pallets", index=False)
        df_bultos.to_excel(writer, sheet_name="Cajas", index=False)

        df_bultos_unicos = df_bultos[~df_bultos["LPN"].duplicated()]
        df_asn_cajas = agrupar_cajas(df_bultos_unicos)

        if not df_pallets.empty:
            pallets_simple = []
            pallets_df = pd.DataFrame(pallets)
            pallets_df["TipoCaja"] = "Pallet"

            usados = set()
            for i, row in pallets_df.iterrows():
                if i in usados:
                    continue
                grupo = [row]
                usados.add(i)
                for j, row2 in pallets_df.iterrows():
                    if j in usados or i == j:
                        continue
                    if (
                        abs(row["Peso (kg)"] - row2["Peso (kg)"]) <= 0.5 and
                        row["TipoCaja"] == row2["TipoCaja"] and
                        row["Alto (cm)"] == row2["Alto (cm)"] and
                        row["Largo (cm)"] == row2["Largo (cm)"] and
                        row["Ancho (cm)"] == row2["Ancho (cm)"]
                    ):
                        grupo.append(row2)
                        usados.add(j)
                pallets_simple.append({
                    "Tipo": "Pallet",
                    "Unidades": len(grupo),
                    "Peso(kg/unid)": round(sum([x["Peso (kg)"] for x in grupo]) / len(grupo), 2),
                    "Alto(cm/unid)": row["Alto (cm)"],
                    "Ancho(cm/unid)": row["Ancho (cm)"],
                    "Largo(cm/unid)": row["Largo (cm)"]
                })

            df_asn_pallets = pd.DataFrame(pallets_simple)
            df_asn = pd.concat([df_asn_cajas, df_asn_pallets], ignore_index=True)
        else:
            df_asn = df_asn_cajas

        df_asn.to_excel(writer, sheet_name="ASN", index=False)

        # Nueva pestaña detalle con columnas LPN, CodItem, NomItem, Unidades
        columnas_detalle = ["LPN", "CodItem", "NomItem", "Unidades"]
        df_detalle = df_wms[columnas_detalle]
        df_detalle.to_excel(writer, sheet_name="detalle", index=False)

    print("\n✅ Archivo 'bultos_pedido_collahuasi.xlsx' generado.")

    # Preguntar si desea imprimir detalle para creación de guía
    respuesta = input("\n¿Desea imprimir el detalle para la creación de guía? (s/n): ").strip().lower()
    if respuesta == "s":
        coditem_db_path = "data/coditem_db.json"
        if os.path.exists(coditem_db_path):
            with open(coditem_db_path, "r", encoding="utf-8") as f:
                coditem_db = json.load(f)
        else:
            coditem_db = {}

        # Obtener CodItem únicos del detalle
        coditems_unicos = df_detalle[["CodItem", "NomItem"]].drop_duplicates()

        # Para cada CodItem distinto, validar o pedir datos
        for _, row in coditems_unicos.iterrows():
            coditem = str(row["CodItem"])
            nomitem = row["NomItem"]

            if coditem in coditem_db:
                info = coditem_db[coditem]
                nitem = info.get("NItem")
                nroparte = info.get("NroParte")
                nomitem_json = info.get("NomItem", "")

                # Validar que NomItem coincida o actualizarlo
                if nomitem_json != nomitem:
                    coditem_db[coditem]["NomItem"] = nomitem

                if nitem and nroparte:
                    print(f"\nCodItem: {coditem} | NomItem: {nomitem}")
                    print(f"POS/Item: {nitem}")
                    print(f"Nro Parte: {nroparte}")
                    correcto = input("¿Son correctos POS/Item y Nro Parte? (s/n): ").strip().lower()
                    if correcto != "s":
                        nitem = input("Ingrese POS/Item (NItem): ").strip()
                        nroparte = input("Ingrese Nro Parte: ").strip()
                        coditem_db[coditem]["NItem"] = nitem
                        coditem_db[coditem]["NroParte"] = nroparte
                else:
                    print(f"\nCodItem: {coditem} | NomItem: {nomitem}")
                    nitem = input("Ingrese POS/Item (NItem): ").strip()
                    nroparte = input("Ingrese Nro Parte: ").strip()
                    coditem_db[coditem]["NItem"] = nitem
                    coditem_db[coditem]["NroParte"] = nroparte
                    coditem_db[coditem]["NomItem"] = nomitem
            else:
                print(f"\nCodItem: {coditem} | NomItem: {nomitem}")
                nitem = input("Ingrese POS/Item (NItem): ").strip()
                nroparte = input("Ingrese Nro Parte: ").strip()
                coditem_db[coditem] = {
                    "NItem": nitem,
                    "NroParte": nroparte,
                    "NomItem": nomitem
                }

        # Guardar JSON actualizado
        with open(coditem_db_path, "w", encoding="utf-8") as f:
            json.dump(coditem_db, f, indent=2, ensure_ascii=False)

        tiene_pallets = not df_pallets.empty
        tiene_bultos = not df_bultos.empty

        def imprimir_resumen_guia(df_filtro, titulo):
            resumen = agrupar_unidades_por_coditem(df_filtro)
            print(f"\n{titulo}:")
            print(f"{'CodItem':<10} {'NomItem':<30} {'Unidades':>8}")
            print("-" * 50)
            for _, r in resumen.iterrows():
                print(f"{r['CodItem']:<10} {r['NomItem']:<30} {r['Unidades']:>8}")

            coditems_en_resumen = resumen["CodItem"].astype(str).unique()
            nro_partes_set = set()
            for coditem in coditems_en_resumen:
                if coditem in coditem_db and "NroParte" in coditem_db[coditem]:
                    nro_partes_set.add(coditem_db[coditem]["NroParte"])

            if nro_partes_set:
                print("Nro Parte en la guía:", " ".join(sorted(nro_partes_set)))
            else:
                print("No se encontraron Nro Parte para los CodItem en la guía.")

        # Imprimir una guía por cada pallet
        if tiene_pallets:
            for pallet_name in df_pallets["Pallet"].unique():
                df_detalle_pallet = df_detalle[df_detalle["LPN"].isin(df_pallets[df_pallets["Pallet"] == pallet_name]["LPN"])]
                imprimir_resumen_guia(df_detalle_pallet, f"Guía {pallet_name}")

        # Imprimir una guía para todos los bultos juntos
        if tiene_bultos:
            lpn_bultos = df_bultos["LPN"].unique()
            df_detalle_bultos = df_detalle[df_detalle["LPN"].isin(lpn_bultos)]
            imprimir_resumen_guia(df_detalle_bultos, "Guía Bultos")

        if not tiene_pallets and not tiene_bultos:
            print("No hay pallets ni bultos para mostrar en la guía.")

        # Preguntar si desea generar etiquetas para despacho
        generar_etiquetas = input("\n¿Desea generar etiquetas para despacho? (s/n): ").strip().lower()
        if generar_etiquetas == "s":
            numero_referencia = input("Ingrese N° OC (Número de Referencia): ").strip()
            df_etiquetas = generar_etiquetas_despacho(df_wms, df_bultos, coditem_db, numero_referencia, df_pallets)

            os.makedirs("output", exist_ok=True)
            output_path = "output/etiquetas_peq.xlsx"
            df_etiquetas.to_excel(output_path, index=False)
            print(f"\n✅ Etiquetas pequeñas generadas en '{output_path}'")

def generar_etiquetas_despacho(df_wms, df_bultos, coditem_db, numero_referencia, df_pallets=None):
    """
    Genera etiquetas para despacho en formato DataFrame para exportar a Excel (Zebra Designer).
    - df_wms: DataFrame con detalle de items (LPN, CodItem, Unidades, NomItem)
    - df_bultos: DataFrame con info de bultos (LPN)
    - coditem_db: dict con info adicional por CodItem (NItem, NroParte)
    - numero_referencia: string con N° OC (Número de Referencia)
    - df_pallets: DataFrame con info de pallets (opcional)
    
    Retorna un DataFrame con columnas:
    ['N° OC', 'N° ITEM', 'CÓDIGO CLIENTE', 'N° DE PARTE', 'CANTIDAD', 'LPN']
    """
    etiquetas = []

    # Obtener LPNs de pallets si existen
    lpn_pallets = []
    if df_pallets is not None and not df_pallets.empty and "LPN" in df_pallets.columns:
        lpn_pallets = df_pallets["LPN"].unique().tolist()

    # LPNs de bultos
    lpn_bultos = df_bultos["LPN"].unique().tolist()

    # Unión de todos los LPNs a procesar
    lpn_todos = sorted(set(lpn_pallets) | set(lpn_bultos))

    # Agrupar por LPN y CodItem para obtener cantidades por item en cada LPN
    df_lpn_coditem = df_wms.groupby(["LPN", "CodItem", "NomItem"], as_index=False)["Unidades"].sum()

    # Para cada LPN en la unión de pallets y bultos
    for lpn in lpn_todos:
        df_lpn = df_lpn_coditem[df_lpn_coditem["LPN"] == lpn]

        # Caso 1: solo un CodItem en LPN
        if len(df_lpn) == 1:
            row = df_lpn.iloc[0]
            coditem = str(row["CodItem"])
            unidades = int(row["Unidades"])
            nitem = coditem_db.get(coditem, {}).get("NItem", "")
            nroparte = coditem_db.get(coditem, {}).get("NroParte", "")

            # Generar 2 etiquetas iguales para la caja (cantidad total)
            for _ in range(2):
                etiquetas.append({
                    "N° OC": numero_referencia,
                    "N° ITEM": nitem,
                    "CÓDIGO CLIENTE": coditem,
                    "N° DE PARTE": nroparte,
                    "CANTIDAD": unidades,
                    "LPN": lpn
                })

        else:
            # Caso 2: más de un CodItem en LPN
            # Primero 2 etiquetas por cada CodItem con cantidad total
            for _, row in df_lpn.iterrows():
                coditem = str(row["CodItem"])
                unidades = int(row["Unidades"])
                nitem = coditem_db.get(coditem, {}).get("NItem", "")
                nroparte = coditem_db.get(coditem, {}).get("NroParte", "")

                for _ in range(2):
                    etiquetas.append({
                        "N° OC": numero_referencia,
                        "N° ITEM": nitem,
                        "CÓDIGO CLIENTE": coditem,
                        "N° DE PARTE": nroparte,
                        "CANTIDAD": unidades,
                        "LPN": lpn
                    })

            # Luego etiquetas pequeñas cantidad 1 para cada unidad de cada CodItem
            for _, row in df_lpn.iterrows():
                coditem = str(row["CodItem"])
                unidades = int(row["Unidades"])
                nitem = coditem_db.get(coditem, {}).get("NItem", "")
                nroparte = coditem_db.get(coditem, {}).get("NroParte", "")

                for _ in range(unidades):
                    etiquetas.append({
                        "N° OC": numero_referencia,
                        "N° ITEM": nitem,
                        "CÓDIGO CLIENTE": coditem,
                        "N° DE PARTE": nroparte,
                        "CANTIDAD": 1,
                        "LPN": lpn
                    })

    df_etiquetas = pd.DataFrame(etiquetas, columns=["N° OC", "N° ITEM", "CÓDIGO CLIENTE", "N° DE PARTE", "CANTIDAD", "LPN"])
    return df_etiquetas