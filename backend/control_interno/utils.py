import os
import json
import urllib.parse
import requests
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

def get_col(df, col_names, iloc_idx=None):
    if isinstance(col_names, str): col_names = [col_names]
    df_cols_upper = {str(c).strip().upper(): c for c in df.columns}
    for name in col_names:
        name_upper = name.strip().upper()
        if name_upper in df_cols_upper: return df[df_cols_upper[name_upper]]
    if iloc_idx is not None and iloc_idx < len(df.columns): return df.iloc[:, iloc_idx]
    return pd.Series([None] * len(df))

def clean_str(series):
    return series.astype(str).replace('nan', '').replace('None', '').str.strip()

def consultar_maestro_sheets(lista_cedulas):
    """Búsqueda estandarizada en Google Sheets para todos los módulos."""
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
            condiciones = " OR ".join([f"(A='{c}' OR A={c})" if str(c).isdigit() else f"A='{c}'" for c in lote])
            sql_query = f"SELECT A, C, D, I WHERE {condiciones}"
            url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tq={urllib.parse.quote(sql_query)}&sheet={urllib.parse.quote(sheet_name)}&access_token={access_token}"
            
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
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
    except Exception as e:
        print(f"Error en Sheets: {e}")
    return pd.DataFrame()