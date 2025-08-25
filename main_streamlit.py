# main_streamlit.py
import os
import json
import pandas as pd
import streamlit as st

from utils.cajas import mostrar_cajas,cargar_cajas
from clientes import tottus, sodimac
import clientes.collahuasi as collahuasi  # módulo Collahuasi adaptado

DATA_DIR = "data"
OUTPUT_DIR = "output"


def cargar_database():
    path = os.path.join(DATA_DIR, "database_db.json")
    if not os.path.exists(path):
        st.error(f"❌ No se encontró {path}")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_uploaded_file(uploaded_file, subdir="uploads"):
    """Guarda archivo subido y retorna la ruta"""
    upload_dir = os.path.join(DATA_DIR, subdir)
    os.makedirs(upload_dir, exist_ok=True)
    path = os.path.join(upload_dir, uploaded_file.name)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path


def proceso_tottus(df_wms, df_cajas):
    st.header("Proceso Tottus")
    orden_salida = st.text_input("Número de Orden de Salida")
    if not orden_salida:
        st.warning("Ingrese el número de orden de salida para continuar.")
        return
    if st.button("Ejecutar Proceso Tottus"):
        try:
            output_file = tottus.run(df_wms, df_cajas, orden_salida=orden_salida)
            if output_file and os.path.exists(output_file):
                with open(output_file, "rb") as f:
                    st.download_button(
                        label="📥 Descargar resultado Tottus",
                        data=f,
                        file_name=os.path.basename(output_file),
                        mime="application/octet-stream"
                    )
                st.success("✅ Proceso Tottus ejecutado correctamente.")
        except Exception as e:
            st.error(f"Error en proceso Tottus: {e}")


def proceso_sodimac(df_wms, df_cajas):
    st.header("Proceso Sodimac")
    orden_salida = st.text_input("Número de Orden de Salida")
    if not orden_salida:
        st.warning("Ingrese el número de orden de salida para continuar.")
        return
    if st.button("Ejecutar Proceso Sodimac"):
        try:
            output_file = sodimac.run(df_wms, df_cajas, orden_salida=orden_salida)
            if output_file and os.path.exists(output_file):
                with open(output_file, "rb") as f:
                    st.download_button(
                        label="📥 Descargar resultado Sodimac",
                        data=f,
                        file_name=os.path.basename(output_file),
                        mime="application/octet-stream"
                    )
                st.success("✅ Proceso Sodimac ejecutado correctamente.")
        except Exception as e:
            st.error(f"Error en proceso Sodimac: {e}")


def proceso_collahuasi(df_wms, df_cajas):
    st.header("Proceso Collahuasi")
    collahuasi.run(df_wms, df_cajas)


def procesos_clientes():
    st.subheader("Ejecución de Procesos por Cliente")

    database = cargar_database()
    if not database:
        st.stop()

    owners = list(database.get("Owners", {}).keys())
    owner = st.selectbox("Selecciona Owner:", [""] + owners)

    if not owner:
        return

    clientes = database.get("Owners", {}).get(owner, [])
    cliente = st.selectbox("Selecciona Cliente:", [""] + clientes)

    if not cliente:
        return

    archivo_wms = st.file_uploader("Sube archivo WMS (Excel o CSV)", type=["xlsx", "csv"])
    if not archivo_wms:
        return

    try:
        if archivo_wms.name.endswith(".csv"):
            df_wms = pd.read_csv(archivo_wms, sep=",", encoding="latin1")
        else:
            df_wms = pd.read_excel(archivo_wms)
    except Exception as e:
        st.error(f"Error leyendo archivo: {e}")
        return

    cajas_list = cargar_cajas()
    df_cajas = pd.DataFrame(cajas_list)

    cliente_lower = cliente.lower()

    if cliente_lower == "tottus":
        proceso_tottus(df_wms, df_cajas)
    elif cliente_lower == "sodimac":
        proceso_sodimac(df_wms, df_cajas)
    elif cliente_lower == "collahuasi":
        proceso_collahuasi(df_wms, df_cajas)
    else:
        st.error("Cliente no implementado todavía.")


def main():
    st.set_page_config(page_title="Logística App", layout="wide")
    st.title("📦 Upper APP")

    menu = st.sidebar.radio("Menú", ["Procesos Clientes", "Cajas"])

    if menu == "Cajas":
        mostrar_cajas()
    elif menu == "Procesos Clientes":
        procesos_clientes()
    # elif menu == "Resultados":
    #     mostrar_resultados()


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    main()
