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
def converte_dfs_to_excel(sdf: dict[str, pd.DataFrame]) -> bytes:
    cnt = defaultdict(int)
    files: dict[str, bytes] = {}

    records = []

    nombres = set()
    for sheet_df in sdf.values():
        nombres.update(sheet_df[COL_NOMBRE].unique())

    for nombre in sorted(nombres):
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
            for sheet_name, sheet_df in sdf.items()
                sheet_df[sheet_df[COL_NOMBRE == nombre]].to_excel(writer, sheet_name=sheet_name, index=False)
            
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

    options = set(df[COL_STATUS].unique())
    options.add("X")
    options.add("XP")
    options.add("LICENCIA")

    sheet_name_1 = st.text_input("Nombre la hoja", "Cargos activos")
    include_status_1 = st.multiselect(
        "Incluir asignaciones con",
        options,
        ["X", "XP"],
    )

    sheet_name_2 = st.text_input("Nombre la hoja", "Cargos en licencia")
    include_status_2 = st.multiselect(
        "Incluir asignaciones con",
        options,
        ["LICENCIA", ],
    )

    # Every form must have a submit button.
    submitted = st.form_submit_button("Generar archivos")
    if submitted:
        sdf1 = df[df[COL_STATUS].isin(include_status_1)]
        sdf2 = df[df[COL_STATUS].isin(include_status_2)]
        data_to_download = converte_dfs_to_excel(
            {
                sheet_name_1: sdf1[EXPORT_COLUMNS], 
                sheet_name_2: sdf2[EXPORT_COLUMNS],
            }
        )

if data_to_download is not None:
    st.download_button(
        label=f"Bajar asignaciones ({len(data_to_download)//1024} KB)",
        data=data_to_download,
        file_name="asignaciones.zip",
        mime="application/zip",
        icon=":material/download:"
    )