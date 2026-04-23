import io
import traceback
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from .database import engine

# Importamos las herramientas compartidas (Asegúrate de tener utils.py con estas funciones)
from .utils import get_col, clean_str, consultar_maestro_sheets

router = APIRouter()

# Las cabeceras exactas solicitadas para Invasivos
HEADERS_ESTANDAR_INVASIVOS = [
    "CC PROFESIONAL", "FECHA", "CC PACIENTE", "JORNADA", 
    "FECHA CREACION", "LIDER", "COORDINADOR", "GEOREFERENCIA", 
    "ESTADO", "CRUCE"
]

HEADERS_PLANTILLA_INVASIVOS = [
    "CC PROFESIONAL", "FECHA", "CC PACIENTE", "JORNADA", 
    "FECHA CREACION", "LIDER", "COORDINADOR", "GEOREFERENCIA", 
    "ESTADO", "CRUCE"
]

@router.get("/template/invasivos")
async def download_invasivos_template():
    """Genera y descarga la plantilla CSV para Medios Invasivos."""
    try:
        output = io.StringIO()
        df_template = pd.DataFrame(columns=HEADERS_PLANTILLA_INVASIVOS)
        
        # Fila de ejemplo para guiar al usuario
        df_template.loc[0] = [
            "12345678", "01/04/2026", "87654321", "MAÑANA", 
            "01/04/2026 08:30", "(Autogenerado)", "(Autogenerado)", 
            "http://maps.google.com/...", "Rango confirmado", "(Autogenerado)"
        ]
        
        df_template.to_csv(output, index=False, sep=';', encoding='utf-8-sig')
        response = StreamingResponse(io.BytesIO(output.getvalue().encode('utf-8-sig')), media_type="text/csv")
        response.headers["Content-Disposition"] = "attachment; filename=Plantilla_Invasivos_Control_Interno.csv"
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def procesar_plantilla_invasivos(df_raw):
    """Procesa el CSV de Invasivos, estandariza y cruza con Google Sheets."""
    # Limpiamos los nombres de las columnas entrantes
    df_raw.columns = [str(c).strip().upper() for c in df_raw.columns]
    df_target = pd.DataFrame(columns=HEADERS_ESTANDAR_INVASIVOS)
    
    # 1. Extracción y Limpieza Inteligente (soporta diferentes nombres de columna)
    df_target["CC PROFESIONAL"] = clean_str(get_col(df_raw, ["CC PROFESIONAL", "DOCUMENTO PROFESIONAL"])).str.extract(r'(\d+)', expand=False)
    df_target["FECHA"] = pd.to_datetime(get_col(df_raw, "FECHA"), errors='coerce', dayfirst=True).dt.strftime('%d/%m/%Y')
    df_target["CC PACIENTE"] = clean_str(get_col(df_raw, ["CC PACIENTE", "DOCUMENTO PACIENTE"])).str.replace(r'\.0$', '', regex=True)
    df_target["JORNADA"] = clean_str(get_col(df_raw, "JORNADA")).str.upper()
    df_target["FECHA CREACION"] = pd.to_datetime(get_col(df_raw, "FECHA CREACION"), errors='coerce', dayfirst=True).dt.strftime('%d/%m/%Y %H:%M')
    df_target["GEOREFERENCIA"] = get_col(df_raw, "GEOREFERENCIA").fillna("")
    df_target["ESTADO"] = get_col(df_raw, "ESTADO").fillna("")
    df_target = df_target.fillna("")
    
    # 2. Cruce Automático (CC + Fecha + Jornada)
    c_pac = df_target["CC PACIENTE"].astype(str)
    c_fec = df_target["FECHA"].astype(str).str.replace("/", "", regex=False)
    c_jor = df_target["JORNADA"].astype(str)
    df_target["CRUCE"] = (c_pac + c_fec + c_jor).str.strip()

    # 3. Búsqueda de Líder y Coordinador en Google Sheets
    cedulas = [c for c in df_target['CC PACIENTE'].unique().tolist() if c and len(c) > 3]
    df_maestro = consultar_maestro_sheets(cedulas)
    
    if not df_maestro.empty:
        df_merged = pd.merge(df_target, df_maestro, left_on='CC PACIENTE', right_on='KeyM', how='left')
        df_target['LIDER'] = df_merged['LidM'].fillna('')
        df_target['COORDINADOR'] = df_merged['CoordM'].fillna('Revisar')
    else:
        df_target['LIDER'] = ''
        df_target['COORDINADOR'] = 'Revisar'

    return df_target

@router.post("/upload/invasivos")
async def upload_invasivos(file: UploadFile = File(...)):
    try:
        content = await file.read()
        df_raw = None
        
        # Bucle robusto para leer el CSV sin importar si es de Excel o Mac
        for enc in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
            for sep in [';', ',', '\t']:
                try:
                    temp_df = pd.read_csv(io.BytesIO(content), sep=sep, encoding=enc, dtype=str, on_bad_lines='skip')
                    if len(temp_df.columns) > 3:
                        df_raw = temp_df
                        break
                except: continue
            if df_raw is not None: break
        
        if df_raw is None: 
            raise ValueError("El archivo no pudo ser leído como CSV.")

        # Validamos que el archivo tenga la columna mínima
        df_raw.columns = [str(c).strip().upper() for c in df_raw.columns]
        if "CC PACIENTE" not in df_raw.columns and "DOCUMENTO PACIENTE" not in df_raw.columns:
             raise ValueError("Plantilla inválida. No se encontró la columna CC PACIENTE.")

        df_clean = procesar_plantilla_invasivos(df_raw)
        
        # Guardar en Base de Datos
        df_clean.to_sql("medios_invasivos", con=engine, if_exists='append', index=False)
        return {"status": "ok", "rows_processed": len(df_clean)}
        
    except Exception as e:
        print(f"ERROR UPLOAD INVASIVOS: {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/data/invasivos")
async def get_invasivos():
    try: 
        return pd.read_sql("SELECT * FROM medios_invasivos ORDER BY rowid DESC", con=engine).fillna('').to_dict(orient='records')
    except: 
        return []

@router.delete("/clear/invasivos")
async def clear_invasivos():
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS medios_invasivos"))
        conn.commit()
    return {"status": "ok"}