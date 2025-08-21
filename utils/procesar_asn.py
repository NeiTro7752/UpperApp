import pandas as pd
import os

def procesar_asn(file_path=None):
    # Si no se pasa ruta, usar archivo en escritorio "x.xlsx"
    if file_path is None:
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        file_path = os.path.join(desktop_path, "x.xlsx")

    df = pd.read_excel(file_path)

    def split_units(row, unit_limit):
        unidades = row['Unidades a despachar']
        if unidades > unit_limit and unidades % unit_limit == 0:
            n = unidades // unit_limit
            rows = []
            for _ in range(n):
                new_row = row.copy()
                new_row['Unidades a despachar'] = unit_limit
                rows.append(new_row)
            return rows
        else:
            if unidades > unit_limit:
                n = unidades // unit_limit
                remainder = unidades % unit_limit
                rows = []
                for _ in range(n):
                    new_row = row.copy()
                    new_row['Unidades a despachar'] = unit_limit
                    rows.append(new_row)
                if remainder > 0:
                    new_row = row.copy()
                    new_row['Unidades a despachar'] = remainder
                    rows.append(new_row)
                return rows
            else:
                return [row]

    new_rows = []
    for _, row in df.iterrows():
        sku = row['SKU']
        if sku == 3650138:
            processed_rows = split_units(row, 2)
            new_rows.extend(processed_rows)
        elif sku == 7641117:
            processed_rows = split_units(row, 8)
            new_rows.extend(processed_rows)
        else:
            new_rows.append(row)

    df_new = pd.DataFrame(new_rows)
    df_final = df_new.copy()

    # Evitar SettingWithCopyWarning: asignar con .loc y asegurarse que columnas existan
    if 'Unidades dimensión logística' in df.columns:
        df_final.loc[:, 'Unidades dimensión logística'] = df['Unidades dimensión logística'].astype(float)
    if 'CantidadSolicitada' in df_final.columns and 'Unidades dimensión logística' in df_final.columns:
        df_final.loc[:, 'Bultos'] = df_final['CantidadSolicitada'] / df_final['Unidades dimensión logística']

    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    output_path = os.path.join(desktop_path, "x_processed.xlsx")
    df_final.to_excel(output_path, index=False)

    print(f"Archivo procesado guardado como: {output_path}")