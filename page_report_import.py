import streamlit as st
import pandas as pd

if "df" not in st.session_state:
    st.warning("No hay datos para usar page_report_import")
    st.stop()

df = st.session_state.df

records = []
for k in df.attrs["import_log"]:
    sheetname, info = k.split("|")
    records.append(
        {
            "Hoja": sheetname.strip(),
            "Mensaje": info,
        }
    )

st.dataframe(pd.DataFrame.from_records(records), hide_index=True, use_container_width=True)
