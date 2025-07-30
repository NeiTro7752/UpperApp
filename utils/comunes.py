# utils/comunes.py
import pandas as pd

def agrupar_cajas(df, tolerancia_peso=0.5):
    """
    Agrupa cajas similares según peso y dimensiones.
    :param df: DataFrame con columnas Peso (kg), TipoCaja, Alto (cm), Largo (cm), Ancho (cm)
    :param tolerancia_peso: diferencia máxima de peso para agrupar
    :return: DataFrame agrupado con columnas Tipo, Unidades, Peso(kg/unid), Alto(cm/unid), Ancho(cm/unid), Largo(cm/unid)
    """
    agrupados = []
    usados = set()

    for i, row in df.iterrows():
        if i in usados:
            continue
        grupo = [row]
        usados.add(i)

        for j, row2 in df.iterrows():
            if j in usados or i == j:
                continue
            if (
                abs(row["Peso (kg)"] - row2["Peso (kg)"]) <= tolerancia_peso and
                row["TipoCaja"] == row2["TipoCaja"] and
                row["Alto (cm)"] == row2["Alto (cm)"] and
                row["Largo (cm)"] == row2["Largo (cm)"] and
                row["Ancho (cm)"] == row2["Ancho (cm)"]
            ):
                grupo.append(row2)
                usados.add(j)

        promedio_peso = sum([x["Peso (kg)"] for x in grupo]) / len(grupo)
        agrupados.append({
            "Tipo": row["TipoCaja"],
            "Unidades": len(grupo),
            "Peso(kg/unid)": round(promedio_peso, 2),
            "Alto(cm/unid)": row["Alto (cm)"],
            "Ancho(cm/unid)": row["Ancho (cm)"],
            "Largo(cm/unid)": row["Largo (cm)"]
        })

    return pd.DataFrame(agrupados)

def validar_numero(valor):
    """
    Intenta convertir valor a float, devuelve None si no es válido.
    """
    try:
        return float(valor)
    except (ValueError, TypeError):
        return None
    

def agrupar_unidades_por_coditem(df):
    """
    Agrupa y suma unidades por CodItem y NomItem.
    :param df: DataFrame con columnas CodItem, NomItem, Unidades
    :return: DataFrame con columnas CodItem, NomItem, Unidades (sumadas)
    """
    agrupado = df.groupby(["CodItem", "NomItem"], as_index=False)["Unidades"].sum()
    return agrupado