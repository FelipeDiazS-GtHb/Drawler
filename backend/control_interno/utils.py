import pandas as pd

def get_col(df, col_names, iloc_idx=None):
    """Busca una columna por nombre inteligente o por índice como respaldo."""
    if isinstance(col_names, str):
        col_names = [col_names]
    
    df_cols_upper = {str(c).strip().upper(): c for c in df.columns}
    for name in col_names:
        name_upper = name.strip().upper()
        if name_upper in df_cols_upper:
            return df[df_cols_upper[name_upper]]
            
    if iloc_idx is not None and iloc_idx < len(df.columns):
        return df.iloc[:, iloc_idx]
    return pd.Series([None] * len(df))

def clean_str(series):
    """Limpia cadenas, espacios y NaNs de Pandas."""
    return series.astype(str).replace('nan', '').replace('None', '').str.strip()