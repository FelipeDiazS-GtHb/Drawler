import io
import traceback
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy import text
from .database import engine
from .utils import get_col, clean_str

router = APIRouter()

HEADERS_RUTERO = ["FECHA", "DOCUMENTO PROFESIONAL", "PROFESIONAL", "ASUNTO", "DOCUMENTO PACIENTE", "PACIENTE", "TIPO", "ESTADO"]
HOMOLOGACION_TIPO = { "CUIDADOR 10 HORAS": "CUIDADOR 10 HORAS", "CUIDADOR 12 HORAS DÍA": "CUIDADOR 12 HORAS DÍA" } # Mantén tu dict aquí

def proc_rutero(df_raw):
    df_target = pd.DataFrame(index=df_raw.index, columns=HEADERS_RUTERO)
    try: df_target["FECHA"] = pd.to_datetime(get_col(df_raw, "FECHA", 17), errors='coerce', dayfirst=True).dt.strftime('%d/%m/%Y')
    except: pass
    try: df_target["DOCUMENTO PROFESIONAL"] = clean_str(get_col(df_raw, "DOCUMENTO PROFESIONAL", 13)).str.extract(r'(\d+)', expand=False)
    except: pass
    try: df_target["PROFESIONAL"] = clean_str(get_col(df_raw, "PROFESIONAL", 14))
    except: pass
    try: df_target["ASUNTO"] = clean_str(get_col(df_raw, "ASUNTO", 16))
    except: pass
    try: df_target["DOCUMENTO PACIENTE"] = clean_str(get_col(df_raw, "DOCUMENTO PACIENTE", 1)).str.extract(r'(\d+)', expand=False)
    except: pass
    if "PACIENTE" in [str(c).strip().upper() for c in df_raw.columns]: df_target["PACIENTE"] = clean_str(get_col(df_raw, "PACIENTE"))
    else:
        try: df_target["PACIENTE"] = (clean_str(get_col(df_raw, "PRIMER NOMBRE", 2)) + " " + clean_str(get_col(df_raw, "SEGUNDO NOMBRE", 3)) + " " + clean_str(get_col(df_raw, ["APELLIDOS", "APELLIDO"], 4))).str.replace(r'\s+', ' ', regex=True).str.strip()
        except: pass
    try: df_target["TIPO"] = clean_str(get_col(df_raw, "TIPO", 15)).map(HOMOLOGACION_TIPO).fillna(clean_str(get_col(df_raw, "TIPO", 15)))
    except: pass
    try: df_target["ESTADO"] = clean_str(get_col(df_raw, "ESTADO", 19))
    except: pass
    return df_target.fillna("")

@router.post("/upload/rutero")
async def upload_rutero(file: UploadFile = File(...)):
    try:
        content = await file.read()
        df_raw = None
        for enc in ['utf-8-sig', 'utf-8', 'latin-1']:
            for sep in [';', ',', '\t']:
                try:
                    temp_df = pd.read_csv(io.BytesIO(content), sep=sep, encoding=enc, dtype=str, on_bad_lines='skip')
                    if len(temp_df.columns) > 3:
                        df_raw = temp_df
                        break
                except: continue
            if df_raw is not None: break
        if df_raw is None: raise ValueError("Formato de CSV no reconocido.")

        df_clean = proc_rutero(df_raw)
        df_clean.to_sql("rutero", con=engine, if_exists='append', index=False)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/data/rutero")
async def get_rutero():
    try: return pd.read_sql("SELECT * FROM rutero ORDER BY rowid DESC", con=engine).fillna('').to_dict(orient='records')
    except: return []

@router.delete("/clear/rutero")
async def clear_rutero():
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS rutero"))
        conn.commit()
    return {"status": "ok"}