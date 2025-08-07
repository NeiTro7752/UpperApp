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
            lpn_pallets = df_pallets["LPN"].unique()
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


    print("\n✅ Archivo 'bultos_pedido_collahuasi.xlsx' generado.")