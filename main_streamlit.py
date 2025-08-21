# main_streamlit.py
import os
import json
import pandas as pd
import streamlit as st

from utils.cajas import cargar_cajas
from clientes import tottus, sodimac  # luego agregas los demás clientes

DATA_DIR = "data"
OUTPUT_DIR = "output"

# =====================
# Utilidades
# =====================
def cargar_database():
    path = os.path.join(DATA_DIR, "database_db.json")
    if not os.path.exists(path):
        st.error(f"❌ No se encontró {path}")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_uploaded_file(uploaded_file, subdir="uploads"):
    """Guarda archivo subido y retorna la ruta"""
    upload_dir = os.path.join("data", subdir)
    os.makedirs(upload_dir, exist_ok=True)
    path = os.path.join(upload_dir, uploaded_file.name)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path

# =====================
# Interfaz
# =====================
st.set_page_config(page_title="Logística App", layout="wide")
st.title("📦 Plataforma Logística con Streamlit")

# --- Menú principal ---
menu = st.sidebar.radio("Menú", ["Cajas", "Procesos Clientes", "Resultados"])

# =====================
# Sección: Cajas
# =====================
if menu == "Cajas":
    st.subheader("Gestión de Cajas")
    cajas = cargar_cajas()

    if not cajas:
        st.warning("⚠️ No hay cajas registradas en `data/cajas.txt`")
    else:
        st.dataframe(pd.DataFrame(cajas))

# =====================
# Sección: Procesos por cliente
# =====================
elif menu == "Procesos Clientes":
    st.subheader("Ejecución de Procesos por Cliente")

    database = cargar_database()
    if not database:
        st.stop()

    owners = list(database.get("Owners", {}).keys())
    owner = st.selectbox("Selecciona Owner:", [""] + owners)

    if owner:
        clientes = database.get("Owners", {}).get(owner, [])
        cliente = st.selectbox("Selecciona Cliente:", [""] + clientes)

        if cliente:
            archivo_wms = st.file_uploader("Sube archivo WMS (Excel o CSV)", type=["xlsx", "csv"])
            orden_salida = st.text_input("Número de Orden de Salida")

            if st.button("▶️ Ejecutar Proceso") and archivo_wms:
                path_file = save_uploaded_file(archivo_wms)
                # Cargar DataFrame según extensión
                try:
                    if path_file.endswith(".csv"):
                        df_wms = pd.read_csv(path_file, sep=",", encoding="latin1")
                    else:
                        df_wms = pd.read_excel(path_file)
                except Exception as e:
                    st.error(f"Error leyendo archivo: {e}")
                    st.stop()

                cajas_list = cargar_cajas()
                df_cajas = pd.DataFrame(cajas_list)

                # Ejecutar módulo dinámicamente
                if cliente.lower() == "tottus":
                    tottus.run(df_wms, df_cajas)  # este imprime/guarda en output
                elif cliente.lower() == "sodimac":
                    sodimac.run(df_wms, df_cajas)
                else:
                    st.error("Cliente no implementado todavía.")

                st.success("✅ Proceso ejecutado. Revisa la sección 'Resultados'.")

# =====================
# Sección: Resultados
# =====================
elif menu == "Resultados":
    st.subheader("Archivos Generados")
    output_files = []
    for root, dirs, files in os.walk(OUTPUT_DIR):
        for f in files:
            output_files.append(os.path.join(root, f))

    if not output_files:
        st.info("No hay archivos en output/")
    else:
        for f in output_files:
            with open(f, "rb") as file:
                st.download_button(
                    label=f"📥 Descargar {os.path.relpath(f, OUTPUT_DIR)}",
                    data=file,
                    file_name=os.path.basename(f),
                    mime="application/octet-stream"
                )
