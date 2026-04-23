import os
import json
import urllib.parse
import requests
import io
import traceback
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import text

# Importamos la base de datos
from .database import engine

router = APIRouter()

HEADERS_ESTANDAR = [
    "CC PROFESIONAL", "SERVICIO", "FECHA", "CC PACIENTE", "TURNO", 
    "FECHA CREACION", "LIDER", "COORDINADOR", "GEOREFERENCIA", "ESTADO", 
    "CRUCE", "EPS", "DIFERENCIADOR"
]

HEADERS_PLANTILLA_EYC = [
    "CC PROFESIONAL", "SERVICIO", "FECHA", "CC PACIENTE", "TURNO", 
    "FECHA CREACION", "LIDER", "COORDINADOR", "GEOREFERENCIA", "ESTADO", "CRUCE"
]

@router.get("/template/eyc")
async def download_eyc_template():
    try:
        output = io.StringIO()
        df_template = pd.DataFrame(columns=HEADERS_PLANTILLA_EYC)
        df_template.loc[0] = [
            "12345678", "NOTA ENFERMERIA", "01/04/2026", "87654321", 
            "DIA", "01/04/2026 08:30", "(Autogenerado)", "(Autogenerado)", 
            "http://googleusercontent.com/maps...", "Rango confirmado", "(Autogenerado)"
        ]
        df_template.to_csv(output, index=False, sep=';', encoding='utf-8-sig')
        
        response = StreamingResponse(io.BytesIO(output.getvalue().encode('utf-8-sig')), media_type="text/csv")
        response.headers["Content-Disposition"] = "attachment; filename=Plantilla_EYC_Control_Interno.csv"
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def extraer_estructura_base(df_raw):
    df_target = pd.DataFrame(columns=HEADERS_ESTANDAR)
    try: df_target["CC PROFESIONAL"] = df_raw.get("CC PROFESIONAL", pd.Series()).astype(str).str.extract(r'(\d+)', expand=False)
    except: pass
    try: df_target["SERVICIO"] = df_raw.get("SERVICIO", pd.Series()).astype(str).str.upper().str.strip()
    except: pass
    try: df_target["CC PACIENTE"] = df_raw.get("CC PACIENTE", pd.Series()).astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    except: pass
    try: df_target["TURNO"] = df_raw.get("TURNO", pd.Series()).astype(str).str.upper().str.strip()
    except: pass
    try: df_target["GEOREFERENCIA"] = df_raw.get("GEOREFERENCIA", pd.Series()).fillna("")
    except: pass
    try: df_target["ESTADO"] = df_raw.get("ESTADO", pd.Series()).fillna("")
    except: pass
    return df_target.fillna("")

def estandarizar_fechas(df_target, df_raw):
    try: df_target["FECHA"] = pd.to_datetime(df_raw.get("FECHA", pd.Series()), errors='coerce', dayfirst=True).dt.strftime('%d/%m/%Y')
    except: pass
    try: df_target["FECHA CREACION"] = pd.to_datetime(df_raw.get("FECHA CREACION", pd.Series()), errors='coerce', dayfirst=True).dt.strftime('%d/%m/%Y %H:%M')
    except: pass
    return df_target.fillna("")

def generar_columna_cruce(df_target):
    c_pac = df_target["CC PACIENTE"].astype(str)
    c_fec = df_target["FECHA"].astype(str)
    c_tur = df_target["TURNO"].astype(str)
    df_target["CRUCE"] = (c_pac + c_fec + c_tur).str.replace("/", "", regex=False)
    return df_target

def consultar_maestro_sheets(lista_cedulas):
    sheet_id = os.getenv("SHEET_ID_MAESTRO", "1xo5EzCA0tla56ENzeiuoHZd-mJ5v1R813zmyNTFkEqE")
    sheet_name = os.getenv("SHEET_NAME_COORDINADORES", "COORDINADORES")
    if not sheet_id or not lista_cedulas: return pd.DataFrame()

    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets.readonly", "https://www.googleapis.com/auth/drive.readonly"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        access_token = creds.get_access_token().access_token
        headers = {"Authorization": f"Bearer {access_token}"}
        
        resultados_maestro = []
        for i in range(0, len(lista_cedulas), 30):
            lote = lista_cedulas[i:i+30]
            condiciones_lista = [f"(A='{c}' OR A={c})" if str(c).isdigit() else f"A='{c}'" for c in lote]
            condiciones = " OR ".join(condiciones_lista)
            
            sql_query = f"SELECT A, C, D, I WHERE {condiciones}"
            url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tq={urllib.parse.quote(sql_query)}&sheet={urllib.parse.quote(sheet_name)}&access_token={access_token}"
            
            res = requests.get(url, headers=headers)
            if res.status_code != 200: continue
            
            json_str = res.text[res.text.find('{'):res.text.rfind('}')+1]
            data = json.loads(json_str)
            
            if 'rows' in data['table']:
                for row in data['table']['rows']:
                    c_list = row.get('c', [])
                    get_val = lambda idx: str(c_list[idx].get('f', c_list[idx].get('v', ''))).strip() if idx < len(c_list) and c_list[idx] else ''
                    resultados_maestro.append([get_val(0), get_val(1), get_val(2), get_val(3)])

        if resultados_maestro:
            df_bq = pd.DataFrame(resultados_maestro, columns=['KeyM', 'LidM', 'CoordM', 'EpsM'])
            df_bq['KeyM'] = df_bq['KeyM'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            return df_bq
        return pd.DataFrame()
    except Exception as e:
        print(f" [X] Error en conexión a Sheets: {e}")
        return pd.DataFrame()

def asignar_lider_coordinador_eps(df_target, df_maestro):
    if not df_maestro.empty:
        df_merged = pd.merge(df_target, df_maestro, left_on='CC PACIENTE', right_on='KeyM', how='left')
        df_target['LIDER'] = df_merged['LidM'].fillna('')
        df_target['COORDINADOR'] = df_merged['CoordM'].fillna('Revisar')
        df_target['EPS'] = df_merged['EpsM'].fillna('')
    else:
        df_target['LIDER'] = ''
        df_target['COORDINADOR'] = 'Revisar'
        df_target['EPS'] = ''
    return df_target

def calcular_diferenciador(df_target):
    def aplicar_regla(v):
        val = str(v).strip()
        if not val or val.lower() == 'nan': return ""
        if val.endswith(" 2"):
            return val.replace(" 2", "_2")
        return val + "_1"
    df_target["DIFERENCIADOR"] = df_target["LIDER"].apply(aplicar_regla)
    return df_target

def procesar_plantilla_eyc(df_raw):
    df_target = extraer_estructura_base(df_raw)
    df_target = estandarizar_fechas(df_target, df_raw)
    df_target = generar_columna_cruce(df_target)
    
    cedulas_unicas = [c for c in df_target['CC PACIENTE'].unique().tolist() if c and len(c) > 3]
    df_maestro = consultar_maestro_sheets(cedulas_unicas)
    
    df_target = asignar_lider_coordinador_eps(df_target, df_maestro)
    df_target = calcular_diferenciador(df_target)
    return df_target

@router.post("/upload/eyc")
async def upload_eyc_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        df_raw = pd.read_csv(io.BytesIO(content), sep=None, engine='python', encoding='utf-8-sig', dtype=str)

        if "CC PACIENTE" not in df_raw.columns:
            raise ValueError("La plantilla no es válida. Descargue el formato oficial.")
        
        df_clean = procesar_plantilla_eyc(df_raw)
        df_clean.to_sql("control_interno_eyc", con=engine, if_exists='append', index=False)
        return {"status": "ok", "rows_processed": len(df_clean)}
    except Exception as e:
        print(f"ERROR UPLOAD EYC: {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/data/eyc")
async def get_eyc_data():
    try:
        query = "SELECT * FROM control_interno_eyc ORDER BY rowid DESC"
        df = pd.read_sql(query, con=engine)
        return df.fillna('').to_dict(orient='records')
    except: 
        return []

@router.delete("/clear/eyc")
async def clear_eyc_data():
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS control_interno_eyc"))
        conn.commit()
    return {"status": "ok"}