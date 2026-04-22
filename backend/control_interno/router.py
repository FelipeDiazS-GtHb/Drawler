from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy import create_engine, text
import pandas as pd
import io
import re
import traceback
from oauth2client.service_account import ServiceAccountCredentials
import requests
import json
import urllib.parse
import os
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()
engine = create_engine("sqlite:///./prototipo.db")

# CABECERAS EXACTAS DE TU SCRIPT
HEADERS_ESTANDAR = ["CC PROFESIONAL", "SERVICIO", "FECHA", "CC PACIENTE", "TURNO", "FECHA CREACION", "LIDER", "COORDINADOR", "GEOREFERENCIA", "ESTADO", "CRUCE"]
HEADERS_INVASIVOS = ["CC PROFESIONAL", "FECHA", "CC PACIENTE", "JORNADA", "FECHA CREACION", "LIDER", "COORDINADOR", "GEOREFERENCIA", "ESTADO"]
HEADERS_RUTERO = ["FECHA", "DOCUMENTO PROFESIONAL", "PROFESIONAL", "ASUNTO", "DOCUMENTO PACIENTE", "PACIENTE", "TIPO", "ESTADO"]

# HOMOLOGACIÓN EXACTA DE TU SCRIPT
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


def aplicar_cruce_bigquery_sheets(df_target):
    """
    Realiza una consulta tipo BigQuery directamente a Google Sheets.
    Busca el documento del PACIENTE en la Columna A y trae C (Líder) y D (Coordinador).
    """
    # 1. Obtener configuraciones del .env
    sheet_id = os.getenv("SHEET_ID_MAESTRO")
    sheet_name = os.getenv("SHEET_NAME_COORDINADORES", "COORDINADORES")
    
    if not sheet_id:
        print("  [!] Error: SHEET_ID_MAESTRO no definido en el .env")
        return df_target

    # 2. Extraer Cédulas ÚNICAS de PACIENTES para la búsqueda (Ignorar vacíos)
    df_target['CC PACIENTE'] = df_target['CC PACIENTE'].astype(str).str.strip()
    cedulas = [c for c in df_target['CC PACIENTE'].unique().tolist() if c]
    
    if not cedulas: 
        print("  [-] No hay CC PACIENTE válidos para buscar.")
        return df_target
        
    try:
        # 3. Autenticación con Cuenta de Servicio (credentials.json)
        scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        access_token = creds.get_access_token().access_token
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 4. Construir la consulta SQL para Google Sheets (GViz API)
        # Búsqueda en Col A (Paciente), extracción de Col C (Líder) y Col D (Coordinador)
        condiciones = " OR ".join([f"A='{c}'" for c in cedulas])
        sql_query = f"SELECT A, C, D WHERE {condiciones}"
        
        url = (
            f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?"
            f"tq={urllib.parse.quote(sql_query)}&sheet={urllib.parse.quote(sheet_name)}"
        )
        
        res = requests.get(url, headers=headers)
        
        if res.status_code != 200:
            print(f"  [X] Error de conexión con Google: {res.status_code}")
            return df_target

        # 5. Procesar respuesta JSON de Google
        text_resp = res.text
        json_str = text_resp[text_resp.find('{'):text_resp.rfind('}')+1]
        data = json.loads(json_str)
        
        filas = []
        if 'rows' in data['table']:
            for row in data['table']['rows']:
                celdas = [val['v'] if val else '' for val in row['c']]
                filas.append(celdas)
                
        # 6. Convertir resultados a DataFrame
        df_bq = pd.DataFrame(filas, columns=['DocumentoPaciente', 'Lider', 'Coordinador'])
        df_bq['DocumentoPaciente'] = df_bq['DocumentoPaciente'].astype(str).str.replace(".0", "", regex=False).str.strip()
        
        # 7. Unir con los datos locales (LEFT JOIN) cruzando PACIENTE con PACIENTE
        df_merged = pd.merge(
            df_target, df_bq, 
            left_on='CC PACIENTE', right_on='DocumentoPaciente', how='left'
        )
        
        # 8. Asignar a las columnas de destino
        df_target['LIDER'] = df_merged['Lider'].fillna('')
        df_target['COORDINADOR'] = df_merged['Coordinador'].fillna('')
        
        if 'CRUCE' in df_target.columns:
            df_target['CRUCE'] = df_target['LIDER'].apply(lambda x: "CRUCE OK" if x != "" else "SIN DATOS EN MAESTRO")
            
        print(f"  ✓ Query exitosa: Se encontraron {len(df_bq)} pacientes en la hoja '{sheet_name}'.")
        
    except Exception as e:
        print(f"  [X] Fallo en el cruce de datos: {str(e)}")
        
    return df_target
# =====================================================================
# FUNCIONES NATIVAS DE procesar_datos.py ADAPTADAS A BYTES
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
# RUTAS DE API
# =====================================================================

@router.post("/upload/{seccion}/{tipo}")
async def upload_file(seccion: str, tipo: str, file: UploadFile = File(...)):
    try:
        content = await file.read()
        df_raw = None
        
        # Intentar múltiples codificaciones de forma segura
        for enc in ['utf-8-sig', 'latin-1', 'cp1252', 'utf-8']:
            for sep in [';', ',']:
                try:
                    temp_df = pd.read_csv(io.BytesIO(content), sep=sep, encoding=enc, dtype=str, on_bad_lines='skip')
                    if len(temp_df.columns) > 5:
                        df_raw = temp_df
                        break
                except Exception:
                    continue
            if df_raw is not None: break
                
        if df_raw is None or df_raw.empty:
            raise ValueError("El archivo está vacío o el formato es irreconocible.")

        # Ejecutar las funciones exactas de tu script original
        if tipo == "ventilados": df_clean = proc_ventilados(df_raw)
        elif tipo == "enfermeria": df_clean = proc_enfermeria(df_raw)
        elif tipo == "actividades": df_clean = proc_actividades(df_raw)
        elif tipo == "invasivos": df_clean = proc_invasivos(df_raw)
        elif tipo == "rutero": df_clean = proc_rutero(df_raw)
        else: raise ValueError(f"Tipo {tipo} no soportado")

        # Guardar en tablas separadas para respetar el # de columnas de cada Excel
        table_name = seccion.lower().replace(" ", "_")
        
        df_clean.to_sql(table_name, con=engine, if_exists='append', index=False)
        return {"status": "ok", "filas_procesadas": len(df_clean)}
        
    except Exception as e:
        print(f"ERROR EN BACKEND: {traceback.format_exc()}")
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