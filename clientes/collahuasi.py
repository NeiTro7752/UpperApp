# clientes/collahuasi_streamlit.py
import streamlit as st
import pandas as pd
import os
from utils.comunes import agrupar_cajas, agrupar_unidades_por_coditem  # según tu código original


def input_numero_st(label, entero=False, key=None):
    if entero:
        return st.number_input(label, min_value=0, step=1, key=key)
    else:
        return st.number_input(label, min_value=0.0, format="%.2f", key=key)


def seleccionar_opcion_st(label, opciones, key=None):
    return st.selectbox(label, opciones, key=key)


def seleccionar_caja_st(df_cajas, key_prefix=""):
    opciones_cajas = [
        f"{i}. {row['NombreCaja']} - {row['Alto(cm)']}x{row['Largo(cm)']}x{row['Ancho(cm)']}"
        for i, row in df_cajas.iterrows()
    ]
    opcion = st.selectbox("Selecciona el tipo de caja:", opciones_cajas, key=f"select_caja_{key_prefix}")
    if opcion:
        idx = int(opcion.split(".")[0])
        return df_cajas.iloc[idx]
    return None



def run(df_wms, df_cajas):
    st.title("🟦 Proceso Collahuasi")

    # Inicializar session_state para pallets y bultos
    if "lleva_pallets" not in st.session_state:
        st.session_state.lleva_pallets = None
    if "pallets" not in st.session_state:
        st.session_state.pallets = []
    if "pallet_num" not in st.session_state:
        st.session_state.pallet_num = 1
    if "remaining_lpns" not in st.session_state:
        st.session_state.remaining_lpns = df_wms["LPN"].unique().tolist()  # Únicos LPNs
    if "bultos" not in st.session_state:
        st.session_state.bultos = []
    if "bulto_idx" not in st.session_state:
        st.session_state.bulto_idx = 0
    if "archivo_generado" not in st.session_state:
        st.session_state.archivo_generado = None

    # Paso 1: Preguntar si lleva pallets
    if st.session_state.lleva_pallets is None:
        lleva_pallets = seleccionar_opcion_st("¿El pedido lleva pallets?", ["", "Sí", "No"])
        if lleva_pallets == "":
            st.info("Selecciona si el pedido lleva pallets para continuar.")
            return
        st.session_state.lleva_pallets = lleva_pallets
        st.rerun()

    # Paso 2: Si lleva pallets, seleccionar LPNs para pallet actual
    if st.session_state.lleva_pallets == "Sí":
        if st.session_state.remaining_lpns:
            st.markdown(f"### 📦 Selección de LPNs para Pallet {st.session_state.pallet_num}")
            selected_lpns = st.multiselect(
                "Selecciona los LPNs para este pallet:",
                st.session_state.remaining_lpns,
                key=f"select_lpns_pallet_{st.session_state.pallet_num}"
            )
            peso = input_numero_st(f"⚖️ Peso total del Pallet {st.session_state.pallet_num} (kg):", key=f"peso_pallet_{st.session_state.pallet_num}")
            alto = input_numero_st(f"📏 Altura del Pallet {st.session_state.pallet_num} (cm):", key=f"alto_pallet_{st.session_state.pallet_num}")
            largo = input_numero_st(f"📏 Longitud del Pallet {st.session_state.pallet_num} (cm):", key=f"largo_pallet_{st.session_state.pallet_num}")
            ancho = input_numero_st(f"📏 Ancho del Pallet {st.session_state.pallet_num} (cm):", key=f"ancho_pallet_{st.session_state.pallet_num}")

            if st.button(f"Agregar Pallet {st.session_state.pallet_num}"):
                if not selected_lpns:
                    st.warning("Debes seleccionar al menos un LPN para continuar.")
                else:
                    st.session_state.pallets.append({
                        "Pallet": f"Pallet{st.session_state.pallet_num}",
                        "LPNs": selected_lpns,
                        "Peso (kg)": peso,
                        "Alto (cm)": alto,
                        "Largo (cm)": largo,
                        "Ancho (cm)": ancho
                    })
                    # Quitar LPNs asignados
                    st.session_state.remaining_lpns = [lpn for lpn in st.session_state.remaining_lpns if lpn not in selected_lpns]
                    st.session_state.pallet_num += 1
                    st.rerun()

            mas_pallets = seleccionar_opcion_st("¿Deseas agregar más pallets?", ["", "Sí", "No"], key="mas_pallets")
            if mas_pallets == "No":
                # Terminar pallets y pasar a bultos
                st.session_state.lleva_pallets = "Finalizado"
                st.rerun()
            elif mas_pallets == "":
                st.info("Selecciona si deseas agregar más pallets para continuar.")
                return
            return
        else:
            st.success("Todos los LPNs asignados a pallets.")
            st.session_state.lleva_pallets = "Finalizado"
            st.rerun()

    # Paso 3: Procesar bultos (solo LPNs no asignados a pallets)
    if st.session_state.lleva_pallets in ["No", "Finalizado"]:
        lpns_bultos = st.session_state.remaining_lpns if st.session_state.lleva_pallets == "Finalizado" else df_wms["LPN"].unique().tolist()
        if st.session_state.bulto_idx >= len(lpns_bultos):
            st.success("✅ Todos los bultos procesados.")

            # Generar DataFrames y archivo Excel con pallets y bultos
            pesos, altos, largos, anchos, nombre_caja, lpn_list = [], [], [], [], [], []
            for bulto in st.session_state.bultos:
                pesos.append(bulto["Peso (kg)"])
                altos.append(bulto["Alto (cm)"])
                largos.append(bulto["Largo (cm)"])
                anchos.append(bulto["Ancho (cm)"])
                nombre_caja.append(bulto["TipoCaja"])
                lpn_list.append(bulto["LPN"])

            df_bultos = pd.DataFrame({
                "LPN": lpn_list,
                "Peso (kg)": pesos,
                "TipoCaja": nombre_caja,
                "Alto (cm)": altos,
                "Largo (cm)": largos,
                "Ancho (cm)": anchos,
            })

            if st.session_state.pallets:
                pallet_rows = []
                for p in st.session_state.pallets:
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

                # Agrupar cajas para ASN
                df_bultos_unicos = df_bultos[~df_bultos["LPN"].duplicated()]
                df_asn_cajas = agrupar_cajas(df_bultos_unicos)

                if not df_pallets.empty:
                    pallets_simple = []
                    pallets_df = pd.DataFrame(st.session_state.pallets)
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

                # Guardar ASN
                df_asn.to_excel(writer, sheet_name="ASN", index=False)

                # Guardar detalle
                columnas_detalle = ["LPN", "CodItem", "NomItem", "Unidades"]
                df_detalle = df_wms[columnas_detalle]
                df_detalle.to_excel(writer, sheet_name="detalle", index=False)

            st.session_state.archivo_generado = output_path
            st.success(f"✅ Archivo '{output_path}' generado.")

            # Mostrar botón de descarga
            with open(output_path, "rb") as f:
                st.download_button(
                    label="📥 Descargar archivo generado",
                    data=f,
                    file_name=os.path.basename(output_path),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            return

        # Procesar bulto actual
        lpn_actual = lpns_bultos[st.session_state.bulto_idx]
        st.markdown(f"### Procesando bulto {st.session_state.bulto_idx + 1} de {len(lpns_bultos)}: LPN {lpn_actual}")

        # Ver si LPN está repetido
        df_filtrado = df_wms[df_wms["LPN"] == lpn_actual]
        conteo = df_wms["LPN"].value_counts()
        es_repetido = conteo[lpn_actual] > 1

        if es_repetido:
            st.markdown(f"LPN repetido: {lpn_actual}")
        else:
            row = df_filtrado.iloc[0]
            st.markdown(f"CodItem: {row['CodItem']} | Unidades: {row['Unidades']}")

        caja_sel = seleccionar_caja_st(df_cajas, key_prefix=f"bulto_{st.session_state.bulto_idx}")
        if caja_sel is None:
            st.warning("Selecciona un tipo de caja para continuar.")
            return

        peso = input_numero_st("⚖️ Peso (kg):", key=f"peso_bulto_{st.session_state.bulto_idx}")

        if st.button("Guardar bulto"):
            st.session_state.bultos.append({
                "LPN": lpn_actual,
                "Peso (kg)": peso,
                "TipoCaja": caja_sel["NombreCaja"],
                "Alto (cm)": caja_sel["Alto(cm)"],
                "Largo (cm)": caja_sel["Largo(cm)"],
                "Ancho (cm)": caja_sel["Ancho(cm)"]
            })
            st.session_state.bulto_idx += 1
            st.rerun()