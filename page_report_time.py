import streamlit as st
import pandas as pd

from common import parse, COL_HORARIOS

if "df" not in st.session_state:
    st.warning("No hay datos para usar page_report_time")
    st.stop()

df = st.session_state.df

records = []
for k, row in df.iterrows():
    try:
        parse(row[COL_HORARIOS])
    except:
        records.append(row)

if records:
    st.caption(f":warning: Se detectaron problemas para interpretar el horario en las siguientes :red[{len(records)}] filas.")
    st.dataframe(pd.DataFrame.from_records(records)[['Facultad', 'Carrera', 'Asignatura', 'Año', 'Turno', 'Com', 'Nombre', COL_HORARIOS]], 
                 hide_index=True, use_container_width=True)
else:
    st.caption("No se detectaron problemas para interpretar el horario :partying_face: :tada:")