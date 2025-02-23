import unicodedata
import streamlit as st
import pandas as pd
import re
import io
from collections import defaultdict
import zipfile

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


@st.cache_data
def convert_df(sdf: pd.DataFrame) -> bytes:
    cnt = defaultdict(int)
    files: dict[str, bytes] = {}

    records = []

    for nombre, gdf in sdf.groupby(COL_NOMBRE):
        stem = safe_filename(nombre)

        if stem in cnt:
            fn = f"{stem}_{cnt[stem]}.xlsx"
        else:
            fn = f"{stem}.xlsx"

        cnt[stem] += 1

        records.append({
            COL_NOMBRE: nombre,
            "archivo": fn,
            "mail": "",
        })

        buff = io.BytesIO()
        with pd.ExcelWriter(buff, engine="openpyxl") as writer:
            gdf.to_excel(writer, sheet_name="cursos", index=False)
        buff.seek(0)

        files[fn] = buff.getvalue()

    buff = io.BytesIO()
    with pd.ExcelWriter(buff, engine="openpyxl") as writer:
        pd.DataFrame.from_records(records).to_excel(writer, sheet_name="listado", index=False)
    buff.seek(0)

    files["_listado_completo.xlsx"] = buff.getvalue()

    return create_zip_in_memory(files)


if "df" not in st.session_state:
    st.warning("No hay datos para usar page_report_personal_file")
    st.stop()

df = st.session_state.df

EXPORT_COLUMNS = [
    COL_FACULTAD, COL_CARRERA, COL_ASIGNATURA, COL_YEAR, COL_TURNO, COL_COMISION, COL_HORARIOS, COL_NOMBRE
]

data_to_download = None
with st.form("my_form"):
    include_status = st.multiselect(
        "Incluir asignaciones con",
        sorted(df[COL_STATUS].unique()),
        ["X", "XP"],
    )


    # Every form must have a submit button.
    submitted = st.form_submit_button("Generar archivos")
    sdf = df[df[COL_STATUS].isin(include_status)]
    if submitted:
        data_to_download = convert_df(sdf[EXPORT_COLUMNS])

if data_to_download is not None:
    st.download_button(
        label=f"Bajar asignaciones ({len(data_to_download)//1024} KB)",
        data=data_to_download,
        file_name="asignaciones.zip",
        mime="application/zip",
        icon=":material/download:"
    )