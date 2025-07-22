import json
import os

CODITEM_DB_PATH = "data/coditem_db.json"

def cargar_coditem_db():
    if os.path.exists(CODITEM_DB_PATH):
        with open(CODITEM_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar_coditem_db(db):
    with open(CODITEM_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

def validar_o_actualizar_material(coditem, nomitem):
    """
    Valida si coditem existe en db, si existe pregunta si datos son correctos.
    Si no existe o usuario indica que no es correcto, pide nuevo valor para Material.
    Retorna el valor final de Material guardado.
    """
    db = cargar_coditem_db()
    coditem_str = str(coditem)
    if coditem_str in db:
        info = db[coditem_str]
        material_guardado = info.get("Material", "")
        nomitem_guardado = info.get("NomItem", "")
        if nomitem_guardado != nomitem:
            db[coditem_str]["NomItem"] = nomitem  # Actualiza nombre si cambió
        print(f"\nCodItem: {coditem} | NomItem: {nomitem}")
        print(f"Material guardado: {material_guardado}")
        correcto = input("¿Es correcto el Material? (s/n): ").strip().lower()
        if correcto != "s":
            nuevo_material = input("Ingrese nuevo Material: ").strip()
            db[coditem_str]["Material"] = nuevo_material
            guardar_coditem_db(db)
            return nuevo_material
        else:
            return material_guardado
    else:
        print(f"\nCodItem: {coditem} | NomItem: {nomitem}")
        nuevo_material = input("Ingrese Material: ").strip()
        db[coditem_str] = {
            "Material": nuevo_material,
            "NomItem": nomitem
        }
        guardar_coditem_db(db)
        return nuevo_material