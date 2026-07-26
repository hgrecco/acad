import streamlit as st
import pandas as pd

from common import parse_into_event, COL_HORARIOS, COL_HORA_PRESENCIAL, parse_min, COL_HORA_VIRTUAL

if "df" not in st.session_state:
    st.warning("No hay datos para usar page_report_time")
    st.stop()

df = st.session_state.df

records = []
records_HP = []
records_HV = []
records_MM = []

for k, row in df.iterrows():
    try:
        _, ev = parse_into_event(row, com_string_to_add="")
    except:
        ev = None
        records.append(row)

    try:
        hours = parse_min(row[COL_HORA_VIRTUAL])
    except:
        records_HV.append(row)

    try:
        hours = parse_min(row[COL_HORA_PRESENCIAL])
    except:
        hours = None
        records_HP.append(row)

    if ev is not None and hours is not None:
        if hours != ev.duration:
            records_MM.append(row)

for title, cols, recs in [
    ("interpretar el horario", (COL_HORARIOS, ), records),
    ("interpretar las horas virtuales", (COL_HORA_VIRTUAL, ), records_HV),
    ("interpretar las horas presenciales", (COL_HORA_PRESENCIAL, ), records_HP),
    ("reconciliar el horario con las horas presenciales", (COL_HORARIOS, COL_HORA_PRESENCIAL, ), records_HP),
]:
    if recs:
        st.caption(f":warning: Se detectaron problemas para {title} :red[{len(recs)}] filas.")
        st.dataframe(
            pd.DataFrame.from_records(recs)[['Facultad', 'Carrera', 'Asignatura', 'Año', 'Turno', 'Com', 'Nombre', ] + list(cols)], 
            width='stretch',
            hide_index=True, 
        )
    else:
        st.caption(f"No se detectaron problemas para {title} :tada:")

