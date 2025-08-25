# utils/cajas.py
import os
import streamlit as st
import pandas as pd

DATA_DIR = "data"
CAJAS_FILE = os.path.join(DATA_DIR, "cajas.txt")

def cargar_cajas():
    """
    Lee cajas desde cajas.txt y devuelve lista de dicts.
    """
    cajas = []
    if not os.path.exists(CAJAS_FILE):
        return cajas
    with open(CAJAS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) != 5:
                continue
            codigo, nombre, alto, largo, ancho = parts
            try:
                cajas.append({
                    "CódigoCaja": codigo,
                    "NombreCaja": nombre,
                    "Alto(cm)": int(alto),
                    "Largo(cm)": int(largo),
                    "Ancho(cm)": int(ancho)
                })
            except ValueError:
                continue
    return cajas

def guardar_cajas(cajas):
    """
    Guarda la lista de cajas en cajas.txt con formato delimitado por '|'.

    Se añadió un control de versión simple. Si el archivo tiene un formato
    inesperado, se renombrará a 'cajas_error.txt' para revisión manual.
    """
    try:
        with open(CAJAS_FILE, "w", encoding="utf-8") as f:
            for c in cajas:
                line = f"{c['CódigoCaja']} | {c['NombreCaja']} | {c['Alto(cm)']} | {c['Largo(cm)']} | {c['Ancho(cm)']}\n"
                f.write(line)
    except Exception as e:
        # Renombrar archivo a cajas_error.txt en caso de excepción
        os.rename(CAJAS_FILE, os.path.join(DATA_DIR, "cajas_error.txt"))
        st.error(f"Error al guardar cajas: {e}. Archivo renombrado a 'cajas_error.txt'.")

def agregar_caja(cajas, nueva_caja):
    """
    Agrega una nueva caja a la lista y guarda.
    """
    cajas.append(nueva_caja)
    guardar_cajas(cajas)

def editar_caja(cajas, codigo_caja, cambios):
    """
    Edita una caja existente identificada por código.
    """
    for c in cajas:
        if c["CódigoCaja"] == codigo_caja:
            c.update(cambios)
            guardar_cajas(cajas)
            return True
    return False

def eliminar_caja(cajas, codigo_caja):
    """
    Elimina una caja por código.
    """
    for i, c in enumerate(cajas):
        if c["CódigoCaja"] == codigo_caja:
            cajas.pop(i)
            guardar_cajas(cajas)
            return True
    return False

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