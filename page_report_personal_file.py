
import streamlit as st
import pandas as pd
from collections import defaultdict

from export_helper import export_form, generate_excel_content, create_zip_in_memory, safe_filename
from common import COL_NOMBRE


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