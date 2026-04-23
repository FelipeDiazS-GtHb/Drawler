import io
import traceback
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy import text
from .database import engine
from .utils import get_col, clean_str

router = APIRouter()

HEADERS_RUTERO = ["FECHA", "DOCUMENTO PROFESIONAL", "PROFESIONAL", "ASUNTO", "DOCUMENTO PACIENTE", "PACIENTE", "TIPO", "ESTADO"]

HOMOLOGACION_TIPO = {
    "CUIDADOR 10 HORAS": "CUIDADOR 10 HORAS", "CUIDADOR 12 HORAS DÃ\x8dA": "CUIDADOR 12 HORAS DÍA",
    "CUIDADOR 12 HORAS DÍA": "CUIDADOR 12 HORAS DÍA", "CUIDADOR 12 HORAS NOCHE": "CUIDADOR 12 HORAS NOCHE",
    "CUIDADOR 6 HORAS": "CUIDADOR 6 HORAS", "CUIDADOR 8 HORAS": "CUIDADOR 8 HORAS", "CUIDADOR 9 HORAS": "CUIDADOR 9 HORAS",
    "ENFERMERÃ\x8dA 12 HORAS DÃ\x8dA": "ENFERMERÍA 12 HORAS DÍA", "ENFERMERÍA 12 HORAS DÍA": "ENFERMERÍA 12 HORAS DÍA",
    "ENFERMERIA 12 HORAS NOCHE": "ENFERMERIA 12 HORAS NOCHE", "ENFERMERÃ\x8dA 6 HORAS": "ENFERMERÍA 6 HORAS",
    "ENFERMERÍA 6 HORAS": "ENFERMERÍA 6 HORAS", "ENFERMERÃ\x8dA 8 HORAS": "ENFERMERÍA 8 HORAS",
    "ENFERMERÍA 8 HORAS": "ENFERMERÍA 8 HORAS", "ENTRENAMIENTO 12 HORAS DIA": "ENTRENAMIENTO 12 HORAS DIA",
    "ENTRENAMIENTO 12 HORAS NOCHE": "ENTRENAMIENTO 12 HORAS NOCHE", "ENTRENAMIENTO 8 HORAS": "ENTRENAMIENTO 8 HORAS",
    "INYECCION O INFUSION DE MEDICAMENTOS": "INYECCION O INFUSION DE MEDICAMENTOS", "MEDICINA GENERAL": "MEDICINA GENERAL",
    "NUTRICION": "NUTRICION", "PSICOLOGIA": "PSICOLOGIA", "TERAPIA FISICA": "TERAPIA FISICA",
    "TERAPIA FONOAUDIOLOGICA": "TERAPIA FONOAUDIOLOGICA", "TERAPIA OCUPACIONAL": "TERAPIA OCUPACIONAL",
    "TERAPIA RESPIRATORIA": "TERAPIA RESPIRATORIA", "VALORACION TERAPIA FISICA": "VALORACION TERAPIA FISICA",
    "VALORACION TERAPIA RESPIRATORIA": "VALORACION TERAPIA RESPIRATORIA", "VIDEOCONSULTA": "VIDEOCONSULTA"
}

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
    if "PACIENTE" in [str(c).strip().upper() for c in df_raw.columns]:
        df_target["PACIENTE"] = clean_str(get_col(df_raw, "PACIENTE"))
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

        df_clean = proc_rutero(df_raw)
        df_clean.to_sql("rutero", con=engine, if_exists='append', index=False)
        return {"status": "ok"}
    except Exception as e:
        print(f"ERROR RUTERO: {traceback.format_exc()}")
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