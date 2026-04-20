from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy import create_engine, text
import pandas as pd
import io
import re
import traceback

router = APIRouter()
engine = create_engine("sqlite:///./prototipo.db")

def depurar_archivo(df_raw, tipo):
    # AJUSTADO CON LOS ÍNDICES REALES DE PROCESAR_DATOS.PY
    # Estructura de idx: [CC PROFESIONAL, FECHA, CC PACIENTE, REGISTRO/TURNO, UBI1, UBI2]
    config = {
        "ventilados":  {"lbl": "VENTILADO", "idx": [77, 1, 3, 21, 78, 79]},
        "enfermeria":  {"lbl": "NOTA ENFERMERIA", "idx": [44, 1, 3, 21, 45, 46]},
        "actividades": {"lbl": "CUIDADOR", "idx": [35, 1, 3, 14, 39, 40]}, # CORREGIDO UBI
        "invasivos":   {"lbl": "MEDIOS INVASIVOS", "idx": [33, 1, 3, 14, 37, 38]}, # CORREGIDO UBI
        "rutero":      {"lbl": "RUTERO", "idx": [13, 17, 1, 16, 10, None]}
    }
    
    if tipo not in config: 
        raise ValueError(f"Tipo de archivo '{tipo}' no soportado.")
    m = config[tipo]

    df_target = pd.DataFrame(index=df_raw.index, columns=range(11)).fillna("")
    df_target[1] = m["lbl"]
    
    def extract_num(val):
        if pd.isna(val) or str(val).strip() == "": return ""
        res = re.search(r'(\d+)', str(val))
        return res.group(1) if res else ""

    def safe_extract(df, idx, apply_func=None, split_space=False):
        if idx is None or idx >= len(df.columns):
            return pd.Series([""] * len(df))
        col = df.iloc[:, idx].astype(str).replace('nan', '')
        if apply_func: col = col.apply(apply_func)
        if split_space: col = col.str.split(" ").str[0]
        return col

    # Extracción de CC PACIENTE (Ahora con validación estricta)
    # En tu script procesar_datos.py, el CC_PACIENTE siempre es el índice 3 para clínicas
    # Pero el rutero usa el índice 1
    df_target[3] = safe_extract(df_raw, m["idx"][2], apply_func=extract_num) # CC PACIENTE
    
    # Validar que si la longitud del "CC PACIENTE" es muy corta (ej: edad 40, 15), es porque las columnas se rodaron
    # A veces los CSV exportan mal la estructura y se rueda una columna a la izquierda
    mascara_erronea = df_target[3].str.len() <= 3
    if mascara_erronea.any() and tipo != "rutero":
        # Intentar extraer del índice 4 (si el 3 era la edad por el desfase)
        posible_cc = safe_extract(df_raw, 4, apply_func=extract_num)
        df_target.loc[mascara_erronea, 3] = posible_cc[mascara_erronea]

    df_target[0] = safe_extract(df_raw, m["idx"][0], apply_func=extract_num) # CC PROF
    df_target[2] = safe_extract(df_raw, m["idx"][1], split_space=True)       # FECHA
    df_target[4] = safe_extract(df_raw, m["idx"][3])                         # TURNO
    
    ubi = safe_extract(df_raw, m["idx"][4])
    prox = safe_extract(df_raw, m["idx"][5]) if m["idx"][5] is not None else pd.Series([""] * len(df_raw))
    df_target[8] = (ubi + " | " + prox).str.strip(" | ")

    df_final = df_target[[0, 1, 2, 3, 4, 8]].copy()
    df_final.columns = ["CC_PROFESIONAL", "SERVICIO", "FECHA", "CC_PACIENTE", "TURNO", "GEOREFERENCIA"]
    
    # Limpiar registros donde el CC Paciente esté vacío
    return df_final[df_final["CC_PACIENTE"] != ""]

@router.post("/upload/{seccion}/{tipo}")
async def upload_file(seccion: str, tipo: str, file: UploadFile = File(...)):
    try:
        content = await file.read()
        df_raw = None
        
        # Intentar múltiples codificaciones porque el portal exporta en diferentes formatos
        for enc in ['utf-8-sig', 'latin-1', 'cp1252', 'utf-8']:
            try:
                for sep in [';', ',']:
                    try:
                        temp_df = pd.read_csv(io.BytesIO(content), sep=sep, encoding=enc, dtype=str, on_bad_lines='skip')
                        if len(temp_df.columns) > 5: # Validar que sí se separaron las columnas
                            df_raw = temp_df
                            break
                    except Exception:
                        continue
                if df_raw is not None: break
            except Exception:
                continue
                
        if df_raw is None or df_raw.empty:
            raise ValueError("Formato irreconocible. Verifique que el archivo sea un CSV válido.")

        df_clean = depurar_archivo(df_raw, tipo)
        
        if df_clean.empty:
            raise ValueError("No se extrajeron datos.")

        seccion_db = seccion.upper().replace(" ", "_")
        df_clean['SECCION'] = seccion_db
        
        df_clean.to_sql("datos_depurados", con=engine, if_exists='append', index=False)
        return {"status": "ok", "filas_procesadas": len(df_clean)}
        
    except Exception as e:
        print(f"ERROR EN BACKEND: {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/data/{seccion}")
async def get_data(seccion: str):
    try:
        seccion_db = seccion.upper().replace(" ", "_")
        query = f"SELECT * FROM datos_depurados WHERE SECCION = '{seccion_db}' ORDER BY rowid DESC"
        df = pd.read_sql(query, con=engine)
        return df.fillna('').to_dict(orient='records')
    except: return []

@router.delete("/clear/{seccion}")
async def clear_data(seccion: str):
    with engine.connect() as conn:
        seccion_db = seccion.upper().replace(" ", "_")
        conn.execute(text(f"DELETE FROM datos_depurados WHERE SECCION = '{seccion_db}'"))
        conn.commit()
    return {"status": "ok"}