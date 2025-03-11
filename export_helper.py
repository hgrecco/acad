from typing import TypedDict
import unicodedata
import streamlit as st
import pandas as pd
import re
import io
from collections import defaultdict
import zipfile

from common import COL_NOMBRE, COL_ASIGNATURA, COL_CARRERA, COL_COMISION, COL_FACULTAD, COL_HORARIOS, COL_TURNO, COL_YEAR, COL_STATUS, COL_HORA_VIRTUAL, COL_OBSERVACIONES

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
def converte_dfs_to_excel(sheet_2_df: dict[str, pd.DataFrame], filename_column: str, *, mail_mapping: dict[str, tuple[str, str]] | None = None, zip_stem: str = "archivo") -> Download:
    
    nombres: set[str] = set()
    for sheet_df in sheet_2_df.values():
        nombres.update(sheet_df[filename_column].unique())

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

        if mail_mapping:
            mails[nombre] = mail_mapping.get(nombre, ["", ""])[1]
        else:
            mails[nombre] = ""


    files: dict[str, bytes] = {}
    records = []

    for nombre in sorted(nombres):

        records.append({
            filename_column: nombre,
            "archivo": filenames[nombre],
            "mail": mails[nombre],
        })

        files[filenames[nombre]] = generate_excel_content({
            sheet_name: sheet_df[sheet_df[filename_column] == nombre]
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
                "file_name": f"{zip_stem}.zip",
                "mime": "application/zip",
        }



def export_form(sdf: pd.DataFrame, filename_column: str, filters: list[tuple[str, str, list[str]]] = [], *, zip_stem: str = "archivo", mail_mapping: dict[str, tuple[str, str]] | None = None):
    EXPORT_COLUMNS = [
        COL_FACULTAD, COL_CARRERA, COL_ASIGNATURA, COL_YEAR, COL_TURNO, COL_COMISION, COL_HORARIOS, COL_HORA_VIRTUAL, COL_OBSERVACIONES, COL_NOMBRE
    ]

    data_to_download = None
    with st.form("my_form"):

        sheet_names: list[str] = []
        includes: list[list[str]] = []
        for sheet_name, col, defaults in filters:
            options = set(sdf[col].unique())
            for default in defaults:
                options.add(default)

            sheet_name_1 = st.text_input("Nombre la hoja", sheet_name)
            include_status_1 = st.multiselect(
                f"Incluir asignaciones con {col}",
                options,
                defaults,
            )
            sheet_names.append(sheet_name_1)
            includes.append(include_status_1)

        # Every form must have a submit button.
        submitted = st.form_submit_button("Generar archivos")
        if submitted:
            data_to_download = converte_dfs_to_excel(
                {
                    sheet_name_1: sdf[sdf[col].isin(include_status_1)][EXPORT_COLUMNS]
                    for sheet_name_1, include_status_1, (_, col, _) in zip(sheet_names, includes, filters)
                },
                filename_column=filename_column,
                mail_mapping=mail_mapping,
                zip_stem=zip_stem,
            )

    if data_to_download is not None:
        st.download_button(
            label=f"Bajar asignaciones ({len(data_to_download['data'])//1024} KB)",
            icon=":material/download:",
            **data_to_download
        )

def persona_export_form(sdf: pd.DataFrame):
    export_form(
        sdf, 
        filename_column=COL_NOMBRE,
        filters=[("Cargos activos", COL_STATUS, ["X", "XP"]), ("Cargos en licencia", COL_STATUS, ["LICENCIA"])], 
        mail_mapping=sdf.attrs["personas"],
        zip_stem="asignaciones"
        )


def school_export_form(sdf: pd.DataFrame):
    export_form(
        sdf, 
        filename_column=COL_FACULTAD,
        filters=[("Cursos activos", COL_STATUS, ["X", "XP"])], 
        mail_mapping=None,
        zip_stem="facultades"
    )


@st.dialog("Exportar a Excel")
def export_dialog(sdf: pd.DataFrame):
    persona_export_form(sdf)