from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy import create_engine, text
import pandas as pd
import io
import re

router = APIRouter()
engine = create_engine("sqlite:///./prototipo.db")

def depurar_archivo(df_raw, tipo):
    config = {
        "ventilados":  {"lbl": "VENTILADO", "idx": [77, 1, 3, 21, 78, 79]},
        "enfermeria":  {"lbl": "NOTA ENFERMERIA", "idx": [44, 1, 3, 21, 45, 46]},
        "actividades": {"lbl": "CUIDADOR", "idx": [35, 1, 3, 14, 37, 38]},
        "invasivos":   {"lbl": "MEDIOS INVASIVOS", "idx": [33, 1, 3, 14, 35, 36]},
        "rutero":      {"lbl": "RUTERO", "idx": [13, 17, 1, 16, 10, None]}
    }
    
    if tipo not in config: return pd.DataFrame()
    m = config[tipo]

    df_target = pd.DataFrame(index=df_raw.index, columns=range(11)).fillna("")
    df_target[1] = m["lbl"]
    
    def extract_num(val):
        if pd.isna(val): return ""
        res = re.search(r'(\d+)', str(val))
        return res.group(1) if res else ""

    try: df_target[0] = df_raw.iloc[:, m["idx"][0]].apply(extract_num)
    except: pass
    try: df_target[2] = df_raw.iloc[:, m["idx"][1]].astype(str).str.split(" ").str[0]
    except: pass
    try: df_target[3] = df_raw.iloc[:, m["idx"][2]].apply(extract_num)
    except: pass
    try: df_target[4] = df_raw.iloc[:, m["idx"][3]].fillna("")
    except: pass
    try:
        ubi = df_raw.iloc[:, m["idx"][4]].fillna("").astype(str)
        prox = df_raw.iloc[:, m["idx"][5]].fillna("").astype(str) if m["idx"][5] else ""
        df_target[8] = (ubi + " | " + prox).str.replace('nan', '', case=False).str.strip(' | ')
    except: pass

    df_final = df_target[[0, 1, 2, 3, 4, 8]].copy()
    df_final.columns = ["CC_PROFESIONAL", "SERVICIO", "FECHA", "CC_PACIENTE", "TURNO", "GEOREFERENCIA"]
    return df_final

@router.post("/upload/{seccion}/{tipo}")
async def upload_file(seccion: str, tipo: str, file: UploadFile = File(...)):
    try:
        content = await file.read()
        try: df_raw = pd.read_csv(io.BytesIO(content), sep=';', encoding='utf-8-sig', dtype=str)
        except: df_raw = pd.read_csv(io.BytesIO(content), sep=',', encoding='utf-8-sig', dtype=str)
        
        df_clean = depurar_archivo(df_raw, tipo)
        # Limpiar el nombre de la sección para la BD (ej. NOTAS EYC -> NOTAS_EYC)
        seccion_db = seccion.upper().replace(" ", "_")
        df_clean['SECCION'] = seccion_db
        
        df_clean.to_sql("datos_depurados", con=engine, if_exists='append', index=False)
        return {"status": "ok"}
    except Exception as e:
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