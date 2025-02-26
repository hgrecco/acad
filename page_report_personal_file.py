import unicodedata
import streamlit as st
import pandas as pd
import re
import io
from collections import defaultdict
import zipfile

from export_helper import export_form
from common import COL_NOMBRE, COL_ASIGNATURA, COL_CARRERA, COL_COMISION, COL_FACULTAD, COL_HORARIOS, COL_TURNO, COL_YEAR, COL_STATUS


def safe_filename(s: str) -> str:
    """Removes all non-ASCII letters and returns a safe string."""
    # Normalize the string
    n= unicodedata.normalize('NFKD', s)  
    s = ''.join([c for c in n if not unicodedata.combining(c)]) 
    return re.sub(r'[^a-zA-Z]', '_', s.replace(" ", ""))

def create_zip_in_memory(files: dict[str, bytes]) -> bytes:
    """Creates a ZIP file in memory and returns bytes."""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for filename, file_content in files.items():
            zipf.writestr(filename, file_content)
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()


def generate_excel_content(sheetname_2_df: dict[str, pd.DataFrame]) -> bytes:
    buff = io.BytesIO()
    with pd.ExcelWriter(buff, engine="openpyxl") as writer:
        for sheet_name, sheet_df in sheetname_2_df.items():
            sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)

    buff.seek(0)
    return buff.getvalue()


@st.cache_data
def converte_dfs_to_excel(sheet_2_df: dict[str, pd.DataFrame], personas: dict[str, tuple[str, str]] | None = None) -> bytes:
    cnt = defaultdict(int)
    files: dict[str, bytes] = {}

    records = []

    nombres = set()
    for sheet_df in sheet_2_df.values():
        nombres.update(sheet_df[COL_NOMBRE].unique())

    filenames = {}
    mails = {}
    for nombre in sorted(nombres):
        stem = safe_filename(nombre)
        if stem in cnt:
            fn = f"{stem}_{cnt[stem]}.xlsx"
        else:
            fn = f"{stem}.xlsx"

        filenames[nombre] = fn
        cnt[stem] += 1

        if personas:
            mails[nombre] = personas.get(nombre, ["", ""])[1]
        else:
            mails[nombre] = ""


    for nombre in sorted(nombres):

        records.append({
            COL_NOMBRE: nombre,
            "archivo": filenames[nombre],
            "mail": mails[nombre],
        })

        files[filenames[nombre]] = generate_excel_content({
            sheet_name: sheet_df[sheet_df[COL_NOMBRE] == nombre]
            for sheet_name, sheet_df in sheet_2_df.items()
            })

    files["_listado_completo.xlsx"] = generate_excel_content(
        {"listado": pd.DataFrame.from_records(records)}
    )

    return create_zip_in_memory(files)


if "df" not in st.session_state:
    st.warning("No hay datos para usar page_report_personal_file")
    st.stop()

df = st.session_state.df

export_form(df)