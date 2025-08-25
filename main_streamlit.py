# main_streamlit.py
import os
import json
import pandas as pd
import streamlit as st

from utils.cajas import cargar_cajas, agregar_caja, editar_caja, eliminar_caja
from clientes import tottus, sodimac
import clientes.collahuasi as collahuasi  # Importa el módulo Collahuasi adaptado

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


def mostrar_cajas():
    st.subheader("Gestión de Cajas")
    cajas = cargar_cajas()

    if not cajas:
        st.warning("⚠️ No hay cajas registradas en `data/cajas.txt`")
    else:
        df_cajas = pd.DataFrame(cajas)
        st.dataframe(df_cajas)

    st.markdown("---")
    st.write("### Agregar nueva caja")
    with st.form("form_agregar_caja", clear_on_submit=True):
        codigo = st.text_input("Código Caja")
        nombre = st.text_input("Nombre Caja")
        alto = st.number_input("Alto (cm)", min_value=1, step=1)
        largo = st.number_input("Largo (cm)", min_value=1, step=1)
        ancho = st.number_input("Ancho (cm)", min_value=1, step=1)
        submitted = st.form_submit_button("Agregar Caja")
        if submitted:
            if not codigo or not nombre:
                st.error("Código y Nombre son obligatorios.")
            else:
                nueva_caja = {
                    "CódigoCaja": codigo,
                    "NombreCaja": nombre,
                    "Alto(cm)": alto,
                    "Largo(cm)": largo,
                    "Ancho(cm)": ancho
                }
                agregar_caja(cajas, nueva_caja)
                st.success(f"Caja '{codigo}' agregada.")
                st.session_state["reload"] = not st.session_state.get("reload", False)
                st.rerun()

    st.markdown("---")
    st.write("### Editar o Eliminar caja existente")
    if cajas:
        codigos = [c["CódigoCaja"] for c in cajas]
        codigo_seleccionado = st.selectbox("Selecciona Código de Caja", [""] + codigos)
        if codigo_seleccionado:
            caja_sel = next((c for c in cajas if c["CódigoCaja"] == codigo_seleccionado), None)
            if caja_sel:
                with st.form("form_editar_caja"):
                    nombre = st.text_input("Nombre Caja", value=caja_sel["NombreCaja"])
                    alto = st.number_input("Alto (cm)", min_value=1, step=1, value=caja_sel["Alto(cm)"])
                    largo = st.number_input("Largo (cm)", min_value=1, step=1, value=caja_sel["Largo(cm)"])
                    ancho = st.number_input("Ancho (cm)", min_value=1, step=1, value=caja_sel["Ancho(cm)"])
                    editar = st.form_submit_button("Guardar Cambios")
                    eliminar = st.form_submit_button("Eliminar Caja")
                    if editar:
                        cambios = {
                            "NombreCaja": nombre,
                            "Alto(cm)": alto,
                            "Largo(cm)": largo,
                            "Ancho(cm)": ancho
                        }
                        if editar_caja(cajas, codigo_seleccionado, cambios):
                            st.success(f"Caja '{codigo_seleccionado}' actualizada.")
                            st.rerun()
                        else:
                            st.error("Error al actualizar la caja.")
                    if eliminar:
                        if eliminar_caja(cajas, codigo_seleccionado):
                            st.success(f"Caja '{codigo_seleccionado}' eliminada.")
                            st.rerun()
                        else:
                            st.error("Error al eliminar la caja.")


def procesos_clientes():
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
                if not orden_salida.strip():
                    st.error("Debe ingresar el número de orden de salida.")
                    st.stop()
                path_file = save_uploaded_file(archivo_wms)
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

                output_file = None  # inicializar

                cliente_lower = cliente.lower()
                if cliente_lower == "tottus":
                    output_file = tottus.run(df_wms, df_cajas, orden_salida=orden_salida)
                elif cliente_lower == "sodimac":
                    output_file = sodimac.run(df_wms, df_cajas, orden_salida=orden_salida)
                elif cliente_lower == "collahuasi":
                    # Ejecutar proceso Collahuasi integrado
                    collahuasi.run(df_wms, df_cajas)
                    output_file = None  # Collahuasi maneja su propio output y UI
                else:
                    st.error("Cliente no implementado todavía.")

                if output_file and os.path.exists(output_file):
                    with open(output_file, "rb") as f:
                        st.download_button(
                            label=f"📥 Descargar resultado",
                            data=f,
                            file_name=os.path.basename(output_file),
                            mime="application/octet-stream"
                        )

                if output_file:
                    st.success("✅ Proceso ejecutado. Revisa la sección 'Resultados'.")


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
