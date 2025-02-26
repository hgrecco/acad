from typing import TypedDict
import unicodedata
import streamlit as st
import pandas as pd
import re
import io
from collections import defaultdict
import zipfile

from common import COL_NOMBRE, COL_ASIGNATURA, COL_CARRERA, COL_COMISION, COL_FACULTAD, COL_HORARIOS, COL_TURNO, COL_YEAR, COL_STATUS

class Download(TypedDict):
    data: bytes
    file_name: str
    mime: str

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
def converte_dfs_to_excel(sheet_2_df: dict[str, pd.DataFrame], personas: dict[str, tuple[str, str]] | None = None) -> Download:
    
    nombres: set[str] = set()
    for sheet_df in sheet_2_df.values():
        nombres.update(sheet_df[COL_NOMBRE].unique())

    cnt = defaultdict(int)
    filenames: dict[str, str] = {}
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


    files: dict[str, bytes] = {}
    records = []

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

    if len(nombres) == 1:
        nombre = nombres.pop()
        return {
                "data": files[filenames[nombre]],
                "file_name": filenames[nombre],
                "mime": "application/vnd.ms-excel",
        }
    else:
        files["_listado_completo.xlsx"] = generate_excel_content(
            {"listado": pd.DataFrame.from_records(records)}
        )
        return {
                "data": create_zip_in_memory(files),
                "file_name": "asignaciones.zip",
                "mime": "application/zip",
        }

def export_form(sdf: pd.DataFrame):
    EXPORT_COLUMNS = [
        COL_FACULTAD, COL_CARRERA, COL_ASIGNATURA, COL_YEAR, COL_TURNO, COL_COMISION, COL_HORARIOS, COL_NOMBRE
    ]

    data_to_download = None
    with st.form("my_form"):

        options = set(sdf[COL_STATUS].unique())
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
            sdf1 = sdf[sdf[COL_STATUS].isin(include_status_1)]
            sdf2 = sdf[sdf[COL_STATUS].isin(include_status_2)]
            data_to_download = converte_dfs_to_excel(
                {
                    sheet_name_1: sdf1[EXPORT_COLUMNS], 
                    sheet_name_2: sdf2[EXPORT_COLUMNS],
                },
                sdf.attrs["personas"]
            )

    if data_to_download is not None:
        st.download_button(
            label=f"Bajar asignaciones ({len(data_to_download['data'])//1024} KB)",
            icon=":material/download:",
            **data_to_download
        )

@st.dialog("Exportar a Excel")
def export_dialog(sdf: pd.DataFrame):
    export_form(sdf)