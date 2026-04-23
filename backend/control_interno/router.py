# Archivo: backend/control_interno/router.py
import os
import json
import urllib.parse
import requests
import io
import traceback
import pandas as pd
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import create_engine, text

load_dotenv()

router = APIRouter()
engine = create_engine("sqlite:///./prototipo.db")

# =====================================================================
# CONFIGURACIÓN DE COLUMNAS 
# =====================================================================
HEADERS_ESTANDAR = [
    "CC PROFESIONAL", "SERVICIO", "FECHA", "CC PACIENTE", "TURNO", 
    "FECHA CREACION", "LIDER", "COORDINADOR", "GEOREFERENCIA", "ESTADO", 
    "CRUCE", "EPS", "DIFERENCIADOR"
]

HEADERS_PLANTILLA_EYC = [
    "CC PROFESIONAL", "SERVICIO", "FECHA", "CC PACIENTE", "TURNO", 
    "FECHA CREACION", "LIDER", "COORDINADOR", "GEOREFERENCIA", "ESTADO", "CRUCE"
]

HEADERS_INVASIVOS = ["CC PROFESIONAL", "FECHA", "CC PACIENTE", "JORNADA", "FECHA CREACION", "LIDER", "COORDINADOR", "GEOREFERENCIA", "ESTADO"]
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

# =====================================================================
# ENDPOINT: DESCARGAR PLANTILLA CSV (EYC)
# =====================================================================
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

# =====================================================================
# LÓGICA SOLID: FUNCIONES DE RESPONSABILIDAD ÚNICA (PARA EYC)
# =====================================================================

def extraer_estructura_base(df_raw):
    """SRP 1: Extrae y limpia únicamente las columnas base ingresadas por el usuario."""
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
    """SRP 2: Procesa y formatea las fechas."""
    try: df_target["FECHA"] = pd.to_datetime(df_raw.get("FECHA", pd.Series()), errors='coerce', dayfirst=True).dt.strftime('%d/%m/%Y')
    except: pass
    try: df_target["FECHA CREACION"] = pd.to_datetime(df_raw.get("FECHA CREACION", pd.Series()), errors='coerce', dayfirst=True).dt.strftime('%d/%m/%Y %H:%M')
    except: pass
    return df_target.fillna("")

def generar_columna_cruce(df_target):
    """SRP 3: Concatena la Cédula, Fecha y Turno para crear la llave única CRUCE."""
    c_pac = df_target["CC PACIENTE"].astype(str)
    c_fec = df_target["FECHA"].astype(str)
    c_tur = df_target["TURNO"].astype(str)
    df_target["CRUCE"] = (c_pac + c_fec + c_tur).str.replace("/", "", regex=False)
    return df_target

def consultar_maestro_sheets(lista_cedulas):
    """SRP 4: Interactúa con la API de Google Sheets buscando por CC PACIENTE."""
    sheet_id = os.getenv("SHEET_ID_MAESTRO", "1xo5EzCA0tla56ENzeiuoHZd-mJ5v1R813zmyNTFkEqE")
    sheet_name = os.getenv("SHEET_NAME_COORDINADORES", "COORDINADORES")
    
    if not sheet_id or not lista_cedulas:
        return pd.DataFrame()

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
            
            # Extraemos A(CC PACIENTE), C(Lider), D(Coord), I(EPS)
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
    """SRP 5: Inyecta los datos de Líder, Coordinador y EPS."""
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
    """SRP 6: Calcula el DIFERENCIADOR aplicando la lógica de sufijos a la columna LIDER."""
    def aplicar_regla(v):
        val = str(v).strip()
        if not val or val.lower() == 'nan': return ""
        # Si el Líder termina en " 2", cambiamos el espacio por _2, si no, añadimos _1
        if val.endswith(" 2"):
            return val.replace(" 2", "_2")
        return val + "_1"

    # ¡CORRECCIÓN VITAL! Se aplica estrictamente sobre la columna LIDER
    df_target["DIFERENCIADOR"] = df_target["LIDER"].apply(aplicar_regla)
    return df_target

# =====================================================================
# ORQUESTADOR (DIRECTOR) DE EYC
# =====================================================================
def procesar_plantilla_eyc(df_raw):
    """Orquesta el flujo asegurando que el DIFERENCIADOR sea el último paso."""
    df_target = extraer_estructura_base(df_raw)
    df_target = estandarizar_fechas(df_target, df_raw)
    df_target = generar_columna_cruce(df_target)
    
    # 1. Buscamos al Líder en Sheets
    cedulas_unicas = [c for c in df_target['CC PACIENTE'].unique().tolist() if c and len(c) > 3]
    df_maestro = consultar_maestro_sheets(cedulas_unicas)
    
    # 2. Asignamos el Líder a nuestra tabla
    df_target = asignar_lider_coordinador_eps(df_target, df_maestro)
    
    # 3. ÚLTIMO PASO: Creamos el Diferenciador basándonos en el Líder que acabamos de traer
    df_target = calcular_diferenciador(df_target)
    
    return df_target

# =====================================================================
# PROCESADORES ORIGINALES: INVASIVOS Y RUTERO
# =====================================================================

def proc_invasivos(df_raw):
    df_target = pd.DataFrame(index=df_raw.index, columns=HEADERS_INVASIVOS).fillna("")
    try: df_target["CC PROFESIONAL"] = df_raw.iloc[:, 33].astype(str).str.extract(r'(\d+)', expand=False)
    except: pass
    try: df_target["FECHA"] = pd.to_datetime(df_raw.iloc[:, 1], errors='coerce', dayfirst=True).dt.strftime('%d/%m/%Y')
    except: pass
    try: df_target["FECHA CREACION"] = pd.to_datetime(df_raw.iloc[:, 39], errors='coerce', dayfirst=True).dt.strftime('%d/%m/%Y %H:%M')
    except: pass
    try: df_target["CC PACIENTE"] = df_raw.iloc[:, 3].astype(str).str.extract(r'(\d+)', expand=False)
    except: pass
    try: df_target["JORNADA"] = df_raw.iloc[:, 14]
    except: pass
    try: df_target["GEOREFERENCIA"] = df_raw.iloc[:, 37].fillna("").astype(str)
    except: pass
    try: df_target["ESTADO"] = df_raw.iloc[:, 38].fillna("").astype(str)
    except: pass
    return df_target

def proc_rutero(df_raw):
    df_target = pd.DataFrame(index=df_raw.index, columns=HEADERS_RUTERO).fillna("")
    try: df_target["FECHA"] = pd.to_datetime(df_raw.iloc[:, 17], errors='coerce', dayfirst=True).dt.strftime('%d/%m/%Y')
    except: pass
    try: df_target["DOCUMENTO PROFESIONAL"] = df_raw.iloc[:, 13].astype(str).str.extract(r'(\d+)', expand=False)
    except: pass
    try: df_target["PROFESIONAL"] = df_raw.iloc[:, 14].fillna("").astype(str).str.strip()
    except: pass
    try: df_target["ASUNTO"] = df_raw.iloc[:, 16].fillna("").astype(str).str.strip()
    except: pass
    try: df_target["DOCUMENTO PACIENTE"] = df_raw.iloc[:, 1].astype(str).str.extract(r'(\d+)', expand=False)
    except: pass
    try: 
        c1 = df_raw.iloc[:, 2].fillna("").astype(str)
        c2 = df_raw.iloc[:, 3].fillna("").astype(str)
        c3 = df_raw.iloc[:, 4].fillna("").astype(str)
        df_target["PACIENTE"] = (c1 + " " + c2 + " " + c3).str.replace(r'\s+', ' ', regex=True).str.strip()
    except: pass
    try: 
        tipos_crudos = df_raw.iloc[:, 15].fillna("").astype(str).str.strip()
        df_target["TIPO"] = tipos_crudos.map(HOMOLOGACION_TIPO).fillna(tipos_crudos)
    except: pass
    try: df_target["ESTADO"] = df_raw.iloc[:, 19].fillna("").astype(str).str.strip()
    except: pass
    return df_target

# =====================================================================
# UPLOAD Y GESTIÓN DE DATOS (API ROUTER)
# =====================================================================

@router.post("/upload/eyc")
async def upload_eyc_file(file: UploadFile = File(...)):
    """Endpoint exclusivo para la plantilla de EYC."""
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

@router.post("/upload/{seccion}/{tipo}")
async def upload_file_generic(seccion: str, tipo: str, file: UploadFile = File(...)):
    """Endpoint genérico para Invasivos y Rutero."""
    try:
        content = await file.read()
        df_raw = None
        
        for enc in ['utf-8-sig', 'latin-1', 'cp1252']:
            for sep in [';', ',']:
                try:
                    temp_df = pd.read_csv(io.BytesIO(content), sep=sep, encoding=enc, dtype=str, on_bad_lines='skip')
                    if len(temp_df.columns) > 5:
                        df_raw = temp_df
                        break
                except: continue
            if df_raw is not None: break
                
        if df_raw is None: 
            raise ValueError("Formato de CSV no reconocido.")

        if tipo == "invasivos": 
            df_clean = proc_invasivos(df_raw)
        elif tipo == "rutero": 
            df_clean = proc_rutero(df_raw)
        else: 
            raise ValueError(f"Tipo '{tipo}' no soportado en esta ruta genérica.")

        table_name = seccion.lower().replace(" ", "_")
        df_clean.to_sql(table_name, con=engine, if_exists='append', index=False)
        return {"status": "ok"}
        
    except Exception as e:
        print(f"ERROR UPLOAD GENERIC: {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/data/{seccion}")
async def get_data(seccion: str):
    try:
        table_name = "control_interno_eyc" if seccion == "NOTAS EYC" else seccion.lower().replace(" ", "_")
        query = f"SELECT * FROM {table_name} ORDER BY rowid DESC"
        df = pd.read_sql(query, con=engine)
        return df.fillna('').to_dict(orient='records')
    except: 
        return []

# NUEVO: Endpoint Exclusivo para evitar el error 404 al purgar Notas EYC
@router.delete("/clear/eyc")
async def clear_eyc_data():
    """Endpoint exclusivo para purgar EYC."""
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS control_interno_eyc"))
        conn.commit()
    return {"status": "ok"}

@router.delete("/clear/{seccion}")
async def clear_data(seccion: str):
    """Endpoint genérico para purgar Invasivos y Rutero."""
    table_name = seccion.lower().replace(" ", "_")
    with engine.connect() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
        conn.commit()
    return {"status": "ok"}