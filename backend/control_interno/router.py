import os
import json
import urllib.parse
import requests
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy import create_engine, text
import io
import traceback

load_dotenv()

router = APIRouter()
engine = create_engine("sqlite:///./prototipo.db")

# =====================================================================
# CABECERAS EXACTAS AL FRONTEND
# =====================================================================
HEADERS_ESTANDAR = [
    "CC PROFESIONAL", "SERVICIO", "FECHA", "CC PACIENTE", "TURNO", 
    "FECHA CREACION", "LIDER", "COORDINADOR", "GEOREFERENCIA", "ESTADO", 
    "CRUCE", "EPS", "DIFERENCIADOR"
]
HEADERS_INVASIVOS = ["CC PROFESIONAL", "FECHA", "CC PACIENTE", "JORNADA", "FECHA CREACION", "LIDER", "COORDINADOR", "GEOREFERENCIA", "ESTADO"]
HEADERS_RUTERO = ["FECHA", "DOCUMENTO PROFESIONAL", "PROFESIONAL", "ASUNTO", "DOCUMENTO PACIENTE", "PACIENTE", "TIPO", "ESTADO"]

# HOMOLOGACIÓN
HOMOLOGACION_TIPO = {
    "CUIDADOR 10 HORAS": "CUIDADOR 10 HORAS",
    "CUIDADOR 12 HORAS DÃ\x8dA": "CUIDADOR 12 HORAS DÍA",
    "CUIDADOR 12 HORAS DÍA": "CUIDADOR 12 HORAS DÍA",
    "CUIDADOR 12 HORAS NOCHE": "CUIDADOR 12 HORAS NOCHE",
    "CUIDADOR 6 HORAS": "CUIDADOR 6 HORAS",
    "CUIDADOR 8 HORAS": "CUIDADOR 8 HORAS",
    "CUIDADOR 9 HORAS": "CUIDADOR 9 HORAS",
    "ENFERMERÃ\x8dA 12 HORAS DÃ\x8dA": "ENFERMERÍA 12 HORAS DÍA",
    "ENFERMERÍA 12 HORAS DÍA": "ENFERMERÍA 12 HORAS DÍA",
    "ENFERMERIA 12 HORAS NOCHE": "ENFERMERIA 12 HORAS NOCHE",
    "ENFERMERÃ\x8dA 6 HORAS": "ENFERMERÍA 6 HORAS",
    "ENFERMERÍA 6 HORAS": "ENFERMERÍA 6 HORAS",
    "ENFERMERÃ\x8dA 8 HORAS": "ENFERMERÍA 8 HORAS",
    "ENFERMERÍA 8 HORAS": "ENFERMERÍA 8 HORAS",
    "ENTRENAMIENTO 12 HORAS DIA": "ENTRENAMIENTO 12 HORAS DIA",
    "ENTRENAMIENTO 12 HORAS NOCHE": "ENTRENAMIENTO 12 HORAS NOCHE",
    "ENTRENAMIENTO 8 HORAS": "ENTRENAMIENTO 8 HORAS",
    "INYECCION O INFUSION DE MEDICAMENTOS": "INYECCION O INFUSION DE MEDICAMENTOS",
    "MEDICINA GENERAL": "MEDICINA GENERAL",
    "NUTRICION": "NUTRICION",
    "PSICOLOGIA": "PSICOLOGIA",
    "TERAPIA FISICA": "TERAPIA FISICA",
    "TERAPIA FONOAUDIOLOGICA": "TERAPIA FONOAUDIOLOGICA",
    "TERAPIA OCUPACIONAL": "TERAPIA OCUPACIONAL",
    "TERAPIA RESPIRATORIA": "TERAPIA RESPIRATORIA",
    "VALORACION TERAPIA FISICA": "VALORACION TERAPIA FISICA",
    "VALORACION TERAPIA RESPIRATORIA": "VALORACION TERAPIA RESPIRATORIA",
    "VIDEOCONSULTA": "VIDEOCONSULTA"
}

# =====================================================================
# FUNCIÓN BIGQUERY Y CONCATENACIÓN (CRUCE Y DIFERENCIADOR)
# =====================================================================
def bigquery_notasEyc_liderCoord(df_target):
    """
    Procesa el cruce de datos con Google Sheets para obtener Líder, Coordinador y EPS.
    Calcula el Diferenciador basado en el servicio y genera la llave de Cruce única.
    """
    sheet_id = os.getenv("SHEET_ID_MAESTRO", "1xo5EzCA0tla56ENzeiuoHZd-mJ5v1R813zmyNTFkEqE")
    sheet_name = os.getenv("SHEET_NAME_COORDINADORES", "COORDINADORES")

    # 1. CÁLCULO DE DIFERENCIADOR (REPLICA EXACTA DE TU IMAGEN DE EXCEL)
    # Lógica: VENTILADO -> CUIDADOR -> ENFERMERIA -> TERAPIAS (por defecto)
    def calcular_diferenciador(servicio):
        s = str(servicio).upper()
        if "VENTILADO" in s:
            return "VENTILADO"
        elif "CUIDADOR" in s:
            return "CUIDADOR"
        elif "ENFERMER" in s:
            return "ENFERMERIA"
        else:
            return "TERAPIAS"

    # Asignamos el valor calculado a la columna DIFERENCIADOR
    df_target['DIFERENCIADOR'] = df_target['SERVICIO'].apply(calcular_diferenciador)

    # 2. CONCATENACIÓN CRUCE (CC PACIENTE + FECHA + TURNO/JORNADA) SIN "/"
    # Determinamos si el archivo tiene columna TURNO o JORNADA
    col_v = 'TURNO' if 'TURNO' in df_target.columns else 'JORNADA'
    
    # Limpiamos los datos para asegurar una concatenación sin errores
    c_pac = df_target['CC PACIENTE'].astype(str).replace('nan', '').str.replace(r'\.0$', '', regex=True).str.strip()
    c_fec = df_target['FECHA'].astype(str).replace('nan', '').str.strip()
    c_tur = df_target[col_v].astype(str).replace('nan', '').str.strip()
    
    # Unimos y eliminamos todos los "/" del resultado final para la columna CRUCE
    df_target['CRUCE'] = (c_pac + c_fec + c_tur).str.replace('/', '', regex=False)
    
    # Actualizamos CC PACIENTE en el DataFrame con el valor limpio para la búsqueda en Sheets
    df_target['CC PACIENTE'] = c_pac
    
    if not sheet_id:
        print(" [!] Aviso: SHEET_ID_MAESTRO no configurado en el archivo .env")
        return df_target

    # Obtenemos lista de pacientes únicos para optimizar la cuota de la API
    cedulas_unicas = [c for c in df_target['CC PACIENTE'].unique().tolist() if c and len(c) > 3]
    
    if not cedulas_unicas: 
        return df_target
        
    try:
        # Configuración de credenciales y acceso
        scope = ["https://www.googleapis.com/auth/spreadsheets.readonly", "https://www.googleapis.com/auth/drive.readonly"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        access_token = creds.get_access_token().access_token
        headers = {"Authorization": f"Bearer {access_token}"}
        
        chunk_size = 30 
        resultados_maestro = []
        
        # Procesamiento por lotes para evitar errores de URL demasiado larga (HTTP 400)
        for i in range(0, len(cedulas_unicas), chunk_size):
            lote = cedulas_unicas[i:i+chunk_size]
            condiciones_lista = [f"(A='{c}' OR A={c})" if c.isdigit() else f"A='{c}'" for c in lote]
            condiciones = " OR ".join(condiciones_lista)
            
            # CONSULTA SQL: Extraemos A(Doc), C(Lider), D(Coord), I(EPS según imagen)
            sql_query = f"SELECT A, C, D, I WHERE {condiciones}"
            
            url = (
                f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?"
                f"tq={urllib.parse.quote(sql_query)}&sheet={urllib.parse.quote(sheet_name)}"
                f"&access_token={access_token}"
            )
            
            res = requests.get(url, headers=headers)
            if res.status_code != 200: 
                print(f" [X] Error en petición a Sheets: {res.status_code}")
                continue
            
            # Parseo de la respuesta JSON de Google Visualization API
            text_resp = res.text
            json_str = text_resp[text_resp.find('{'):text_resp.rfind('}')+1]
            data = json.loads(json_str)
            
            if 'rows' in data['table']:
                for row in data['table']['rows']:
                    c_list = row.get('c', [])
                    
                    def get_val(idx):
                        if idx < len(c_list) and c_list[idx]:
                            # Priorizamos el valor formateado 'f' para evitar formatos tipo Date()
                            return str(c_list[idx].get('f', c_list[idx].get('v', ''))).strip()
                        return ''

                    doc = get_val(0)        # Columna A
                    lider = get_val(1)      # Columna C
                    coord = get_val(2)      # Columna D
                    eps = get_val(3)        # Columna I
                    
                    resultados_maestro.append([doc, lider, coord, eps])

        if resultados_maestro:
            # Consolidamos resultados y limpiamos documentos
            df_bq = pd.DataFrame(resultados_maestro, columns=['DocM', 'LidM', 'CoordM', 'EpsM'])
            df_bq['DocM'] = df_bq['DocM'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            
            # Unión final de datos (Left Join)
            df_merged = pd.merge(df_target, df_bq, left_on='CC PACIENTE', right_on='DocM', how='left')
            
            # Asignación de los valores obtenidos a las columnas correspondientes
            df_target['LIDER'] = df_merged['LidM'].fillna('')
            df_target['COORDINADOR'] = df_merged['CoordM'].fillna('')
            df_target['EPS'] = df_merged['EpsM'].fillna('')
            
        print(f" ✓ Cruce finalizado: Diferenciador '{df_target['DIFERENCIADOR'].iloc[0]}' aplicado y {len(df_target)} registros procesados.")
        
    except Exception as e:
        print(f" [X] Error en bigquery_notasEyc_liderCoord: {str(e)}")
        
    return df_target

# =====================================================================
# FUNCIONES DE PROCESAMIENTO INICIALES
# =====================================================================
def proc_ventilados(df_raw):
    df_target = pd.DataFrame(index=df_raw.index, columns=HEADERS_ESTANDAR)
    df_target["SERVICIO"] = "VENTILADO"
    try: df_target["CC PROFESIONAL"] = df_raw.iloc[:, 77].astype(str).str.extract(r'(\d+)', expand=False)
    except Exception: pass
    try: 
        fechas_dt = pd.to_datetime(df_raw.iloc[:, 1], errors='coerce')
        df_target["FECHA"] = [l if pd.notna(l) and str(l) not in ('NaT', 'nan', '') else c for l, c in zip(fechas_dt.dt.strftime('%d/%m/%Y').tolist(), df_raw.iloc[:, 1].fillna("").astype(str).tolist())]
    except Exception: pass
    try: df_target["CC PACIENTE"] = df_raw.iloc[:, 3].astype(str).str.extract(r'(\d+)', expand=False)
    except Exception: pass
    try: df_target["TURNO"] = df_raw.iloc[:, 21]
    except Exception: pass
    try: df_target["GEOREFERENCIA"] = df_raw.iloc[:, 78].fillna("").astype(str)
    except Exception: pass
    try: df_target["ESTADO"] = df_raw.iloc[:, 79].fillna("").astype(str)
    except Exception: pass
    return df_target.fillna("")

def proc_enfermeria(df_raw):
    df_target = pd.DataFrame(index=df_raw.index, columns=HEADERS_ESTANDAR)
    df_target["SERVICIO"] = "NOTA ENFERMERIA" 
    try: df_target["CC PROFESIONAL"] = df_raw.iloc[:, 44].astype(str).str.extract(r'(\d+)', expand=False)
    except Exception: pass
    try: 
        fechas_dt = pd.to_datetime(df_raw.iloc[:, 1], errors='coerce')
        df_target["FECHA"] = [l if pd.notna(l) and str(l) not in ('NaT', 'nan', '') else c for l, c in zip(fechas_dt.dt.strftime('%d/%m/%Y').tolist(), df_raw.iloc[:, 1].fillna("").astype(str).tolist())]
    except Exception: pass
    try: df_target["CC PACIENTE"] = df_raw.iloc[:, 3].astype(str).str.extract(r'(\d+)', expand=False)
    except Exception: pass
    try: df_target["TURNO"] = df_raw.iloc[:, 21]
    except Exception: pass
    try: df_target["GEOREFERENCIA"] = df_raw.iloc[:, 45].fillna("").astype(str)
    except Exception: pass
    try: df_target["ESTADO"] = df_raw.iloc[:, 46].fillna("").astype(str)
    except Exception: pass
    return df_target.fillna("")

def proc_actividades(df_raw):
    df_target = pd.DataFrame(index=df_raw.index, columns=HEADERS_ESTANDAR)
    df_target["SERVICIO"] = "CUIDADOR" 
    try: df_target["CC PROFESIONAL"] = df_raw.iloc[:, 35].astype(str).str.extract(r'(\d+)', expand=False)
    except Exception: pass
    try: 
        fechas_dt = pd.to_datetime(df_raw.iloc[:, 1], errors='coerce')
        df_target["FECHA"] = [l if pd.notna(l) and str(l) not in ('NaT', 'nan', '') else c for l, c in zip(fechas_dt.dt.strftime('%d/%m/%Y').tolist(), df_raw.iloc[:, 1].fillna("").astype(str).tolist())]
    except Exception: pass
    try: 
        fechas_crea_dt = pd.to_datetime(df_raw.iloc[:, 41], errors='coerce')
        df_target["FECHA CREACION"] = [l if pd.notna(l) and str(l) not in ('NaT', 'nan', '') else c for l, c in zip(fechas_crea_dt.dt.strftime('%d/%m/%Y %H:%M').tolist(), df_raw.iloc[:, 41].fillna("").astype(str).tolist())]
    except Exception: pass
    try: df_target["CC PACIENTE"] = df_raw.iloc[:, 3].astype(str).str.extract(r'(\d+)', expand=False)
    except Exception: pass
    try: df_target["TURNO"] = df_raw.iloc[:, 14]
    except Exception: pass
    try: df_target["GEOREFERENCIA"] = df_raw.iloc[:, 39].fillna("").astype(str) 
    except Exception: pass
    try: df_target["ESTADO"] = df_raw.iloc[:, 40].fillna("").astype(str) 
    except Exception: pass
    return df_target.fillna("")

def proc_invasivos(df_raw):
    df_target = pd.DataFrame(index=df_raw.index, columns=HEADERS_INVASIVOS)
    try: df_target["CC PROFESIONAL"] = df_raw.iloc[:, 33].astype(str).str.extract(r'(\d+)', expand=False)
    except Exception: pass
    try: 
        fechas_dt = pd.to_datetime(df_raw.iloc[:, 1], errors='coerce')
        df_target["FECHA"] = [l if pd.notna(l) and str(l) not in ('NaT', 'nan', '') else c for l, c in zip(fechas_dt.dt.strftime('%d/%m/%Y').tolist(), df_raw.iloc[:, 1].fillna("").astype(str).tolist())]
    except Exception: pass
    try: 
        fechas_crea_dt = pd.to_datetime(df_raw.iloc[:, 39], errors='coerce')
        df_target["FECHA CREACION"] = [l if pd.notna(l) and str(l) not in ('NaT', 'nan', '') else c for l, c in zip(fechas_crea_dt.dt.strftime('%d/%m/%Y %H:%M').tolist(), df_raw.iloc[:, 39].fillna("").astype(str).tolist())]
    except Exception: pass
    try: df_target["CC PACIENTE"] = df_raw.iloc[:, 3].astype(str).str.extract(r'(\d+)', expand=False)
    except Exception: pass
    try: df_target["JORNADA"] = df_raw.iloc[:, 14]
    except Exception: pass
    try: df_target["GEOREFERENCIA"] = df_raw.iloc[:, 37].fillna("").astype(str) 
    except Exception: pass
    try: df_target["ESTADO"] = df_raw.iloc[:, 38].fillna("").astype(str) 
    except Exception: pass
    return df_target.fillna("")

def proc_rutero(df_raw):
    df_target = pd.DataFrame(index=df_raw.index, columns=HEADERS_RUTERO)
    try: 
        fechas_dt = pd.to_datetime(df_raw.iloc[:, 17], errors='coerce')
        df_target["FECHA"] = [l if pd.notna(l) and str(l) not in ('NaT', 'nan', '') else c for l, c in zip(fechas_dt.dt.strftime('%d/%m/%Y').tolist(), df_raw.iloc[:, 17].fillna("").astype(str).tolist())]
    except Exception: pass
    try: df_target["DOCUMENTO PROFESIONAL"] = df_raw.iloc[:, 13].astype(str).str.extract(r'(\d+)', expand=False)
    except Exception: pass
    try: df_target["PROFESIONAL"] = df_raw.iloc[:, 14].fillna("").astype(str).str.strip()
    except Exception: pass
    try: df_target["ASUNTO"] = df_raw.iloc[:, 16].fillna("").astype(str).str.strip()
    except Exception: pass
    try: df_target["DOCUMENTO PACIENTE"] = df_raw.iloc[:, 1].astype(str).str.extract(r'(\d+)', expand=False)
    except Exception: pass
    try: 
        c1 = df_raw.iloc[:, 2].fillna("").astype(str)
        c2 = df_raw.iloc[:, 3].fillna("").astype(str)
        c3 = df_raw.iloc[:, 4].fillna("").astype(str)
        df_target["PACIENTE"] = (c1 + " " + c2 + " " + c3).str.replace(r'\s+', ' ', regex=True).str.strip()
    except Exception: pass
    try: 
        tipos_crudos = df_raw.iloc[:, 15].fillna("").astype(str).str.strip()
        df_target["TIPO"] = tipos_crudos.map(HOMOLOGACION_TIPO).fillna(tipos_crudos)
    except Exception: pass
    try: df_target["ESTADO"] = df_raw.iloc[:, 19].fillna("").astype(str).str.strip()
    except Exception: pass
    return df_target.fillna("")

# =====================================================================
# UPLOAD ENDPOINT
# =====================================================================
@router.post("/upload/{seccion}/{tipo}")
async def upload_file(seccion: str, tipo: str, file: UploadFile = File(...)):
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
                
        if df_raw is None: raise ValueError("Formato de CSV no reconocido.")

        if tipo == "ventilados": df_clean = proc_ventilados(df_raw)
        elif tipo == "enfermeria": df_clean = proc_enfermeria(df_raw)
        elif tipo == "actividades": df_clean = proc_actividades(df_raw)
        elif tipo == "invasivos": df_clean = proc_invasivos(df_raw)
        elif tipo == "rutero": df_clean = proc_rutero(df_raw)
        else: raise ValueError(f"Tipo {tipo} no soportado")

        # EJECUTAR CRUCE Y CONCATENACIÓN PARA NOTAS EYC
        if tipo in ["ventilados", "enfermeria", "actividades"]:
            df_clean = bigquery_notasEyc_liderCoord(df_clean)

        table_name = seccion.lower().replace(" ", "_")
        df_clean.to_sql(table_name, con=engine, if_exists='append', index=False)
        return {"status": "ok"}
        
    except Exception as e:
        print(f"ERROR: {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/data/{seccion}")
async def get_data(seccion: str):
    try:
        table_name = seccion.lower().replace(" ", "_")
        query = f"SELECT * FROM {table_name} ORDER BY rowid DESC"
        df = pd.read_sql(query, con=engine)
        return df.fillna('').to_dict(orient='records')
    except: return []

@router.delete("/clear/{seccion}")
async def clear_data(seccion: str):
    table_name = seccion.lower().replace(" ", "_")
    with engine.connect() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
        conn.commit()
    return {"status": "ok"}