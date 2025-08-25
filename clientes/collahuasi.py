# clientes/collahuasi_streamlit.py
import streamlit as st
import pandas as pd
import os
import json
from utils.comunes import agrupar_cajas, agrupar_unidades_por_coditem  # según tu código original


def input_numero_st(label, entero=False):
    if entero:
        return st.number_input(label, min_value=0, step=1)
    else:
        return st.number_input(label, min_value=0.0, format="%.2f")


def input_no_espacios_st(label):
    val = st.text_input(label)
    if " " in val:
        st.error("No se permiten espacios.")
        return None
    return val.strip() if val else None


def seleccionar_opcion_st(label, opciones):
    return st.selectbox(label, opciones)


def run(df_wms, df_cajas):
    st.title("🟦 Proceso Collahuasi")

    remaining_lpns = df_wms["LPN"].tolist()
    pallets = []
    pallet_num = 1

    lleva_pallets = seleccionar_opcion_st("¿El pedido lleva pallets?", ["", "Sí", "No"])
    if lleva_pallets == "":
        st.info("Selecciona si el pedido lleva pallets para continuar.")
        return
    if lleva_pallets == "No":
        remaining_lpns = df_wms["LPN"].tolist()

    if lleva_pallets == "Sí":
        while remaining_lpns:
            st.markdown(f"### 📦 Selección de LPNs para Pallet {pallet_num}")
            selected_lpns = st.multiselect("Selecciona los LPNs para este pallet:", remaining_lpns)
            if not selected_lpns:
                st.warning("Debes seleccionar al menos un LPN para continuar.")
                break

            peso = input_numero_st(f"⚖️ Peso total del Pallet {pallet_num} (kg):")
            alto = input_numero_st(f"📏 Altura del Pallet {pallet_num} (cm):")
            largo = input_numero_st(f"📏 Longitud del Pallet {pallet_num} (cm):")
            ancho = input_numero_st(f"📏 Ancho del Pallet {pallet_num} (cm):")

            if st.button(f"Agregar Pallet {pallet_num}"):
                pallets.append({
                    "Pallet": f"Pallet{pallet_num}",
                    "LPNs": selected_lpns,
                    "Peso (kg)": peso,
                    "Alto (cm)": alto,
                    "Largo (cm)": largo,
                    "Ancho (cm)": ancho
                })
                remaining_lpns = [lpn for lpn in remaining_lpns if lpn not in selected_lpns]
                pallet_num += 1
                st.rerun()

            if not remaining_lpns:
                st.success("Todos los LPNs asignados a pallets.")
                break

            mas_pallets = seleccionar_opcion_st("¿Más pallets?", ["", "Sí", "No"])
            if mas_pallets == "No":
                break
            elif mas_pallets == "":
                st.info("Selecciona si deseas agregar más pallets para continuar.")
                break

    st.markdown("## 🟩 Registro de peso y tipo de caja")

    pesos, altos, largos, anchos, nombre_caja, lpn_list = [], [], [], [], [], []

    lpns_to_process = remaining_lpns if lleva_pallets == "Sí" else df_wms["LPN"].tolist()
    df_filtrado = df_wms[df_wms["LPN"].isin(lpns_to_process)]

    conteo = df_filtrado["LPN"].value_counts()
    lpn_repetidos = conteo[conteo > 1].index.tolist()
    lpn_unicos = conteo[conteo == 1].index.tolist()

    def seleccionar_caja_st(df_cajas):
        opciones_cajas = [
            f"{i}. {row['NombreCaja']} - {row['Alto(cm)']}x{row['Largo(cm)']}x{row['Ancho(cm)']}"
            for i, row in df_cajas.iterrows()
        ]
        opcion = st.selectbox("Selecciona el tipo de caja:", opciones_cajas)
        if opcion:
            idx = int(opcion.split(".")[0])
            return df_cajas.iloc[idx]
        return None

    for lpn in lpn_repetidos:
        st.markdown(f"### 🔁 LPN repetido: {lpn} ({len(df_filtrado[df_filtrado['LPN'] == lpn])} items)")
        peso = input_numero_st("⚖️  Peso total de la caja (kg):")
        caja_sel = seleccionar_caja_st(df_cajas)
        if caja_sel is None:
            st.warning("Selecciona un tipo de caja para continuar.")
            return

        pesos.append(peso)
        altos.append(caja_sel["Alto(cm)"])
        largos.append(caja_sel["Largo(cm)"])
        anchos.append(caja_sel["Ancho(cm)"])
        nombre_caja.append(caja_sel["NombreCaja"])
        lpn_list.append(lpn)

    for lpn in lpn_unicos:
        row = df_filtrado[df_filtrado["LPN"] == lpn].iloc[0]
        st.markdown(f"### 🔹 LPN único: {lpn} | CodItem: {row['CodItem']} | Unidades: {row['Unidades']}")
        peso = input_numero_st("⚖️  Peso (kg):")
        caja_sel = seleccionar_caja_st(df_cajas)
        if caja_sel is None:
            st.warning("Selecciona un tipo de caja para continuar.")
            return

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

    output_path = "output/bultos_pedido_collahuasi.xlsx"
    os.makedirs("output", exist_ok=True)
    with pd.ExcelWriter(output_path) as writer:
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

        columnas_detalle = ["LPN", "CodItem", "NomItem", "Unidades"]
        df_detalle = df_wms[columnas_detalle]
        df_detalle.to_excel(writer, sheet_name="detalle", index=False)

    st.success(f"✅ Archivo '{output_path}' generado.")

    # Aquí puedes agregar más interactividad para imprimir guías o generar etiquetas,
    # adaptando el resto del código con inputs y selectboxes de Streamlit.

# Para usarlo en tu app Streamlit:
# import clientes.collahuasi_streamlit as collahuasi
# collahuasi.run(df_wms, df_cajas)