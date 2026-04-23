import io
import traceback
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy import text
from .database import engine
from .utils import get_col, clean_str

router = APIRouter()

HEADERS_INVASIVOS = ["CC PROFESIONAL", "FECHA", "CC PACIENTE", "JORNADA", "FECHA CREACION", "LIDER", "COORDINADOR", "GEOREFERENCIA", "ESTADO"]

def proc_invasivos(df_raw):
    df_target = pd.DataFrame(index=df_raw.index, columns=HEADERS_INVASIVOS)
    try: df_target["CC PROFESIONAL"] = clean_str(get_col(df_raw, ["CC PROFESIONAL", "DOCUMENTO PROFESIONAL"], 33)).str.extract(r'(\d+)', expand=False)
    except: pass
    try: df_target["FECHA"] = pd.to_datetime(get_col(df_raw, "FECHA", 1), errors='coerce', dayfirst=True).dt.strftime('%d/%m/%Y')
    except: pass
    try: df_target["FECHA CREACION"] = pd.to_datetime(get_col(df_raw, "FECHA CREACION", 39), errors='coerce', dayfirst=True).dt.strftime('%d/%m/%Y %H:%M')
    except: pass
    try: df_target["CC PACIENTE"] = clean_str(get_col(df_raw, ["CC PACIENTE", "DOCUMENTO PACIENTE"], 3)).str.extract(r'(\d+)', expand=False)
    except: pass
    try: df_target["JORNADA"] = clean_str(get_col(df_raw, "JORNADA", 14))
    except: pass
    try: df_target["GEOREFERENCIA"] = clean_str(get_col(df_raw, "GEOREFERENCIA", 37))
    except: pass
    try: df_target["ESTADO"] = clean_str(get_col(df_raw, "ESTADO", 38))
    except: pass
    return df_target.fillna("")

@router.post("/upload/invasivos")
async def upload_invasivos(file: UploadFile = File(...)):
    try:
        content = await file.read()
        df_raw = None
        for enc in ['utf-8-sig', 'latin-1', 'cp1252']:
            for sep in [';', ',', '\t']:
                try:
                    temp_df = pd.read_csv(io.BytesIO(content), sep=sep, encoding=enc, dtype=str, on_bad_lines='skip')
                    if len(temp_df.columns) > 3:
                        df_raw = temp_df
                        break
                except: continue
            if df_raw is not None: break
                
        if df_raw is None: raise ValueError("Formato de CSV no reconocido.")

        df_clean = proc_invasivos(df_raw)
        df_clean.to_sql("medios_invasivos", con=engine, if_exists='append', index=False)
        return {"status": "ok"}
    except Exception as e:
        print(f"ERROR INVASIVOS: {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/data/invasivos")
async def get_invasivos():
    try: return pd.read_sql("SELECT * FROM medios_invasivos ORDER BY rowid DESC", con=engine).fillna('').to_dict(orient='records')
    except: return []

@router.delete("/clear/invasivos")
async def clear_invasivos():
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS medios_invasivos"))
        conn.commit()
    return {"status": "ok"}