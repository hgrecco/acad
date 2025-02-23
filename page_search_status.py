import streamlit as st

from common import generate_schedule_image, build_schedule, CALENDAR_BUFFER, COL_FACULTAD, COL_ASIGNATURA, COL_YEAR, COL_TURNO, COL_COMISION, COL_STATUS


if "df" not in st.session_state:
    st.warning("No hay datos para usar slot_finder")
    st.stop()

df = st.session_state.df

status = st.selectbox("Estado", sorted(df[COL_STATUS].unique()))
if status:
    sdf1 = df[df[COL_STATUS] == status]     
    st.dataframe(sdf1, height=400, hide_index=True, use_container_width=True)
