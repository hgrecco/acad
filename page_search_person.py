import streamlit as st

from common import CALENDAR_BUFFER, person_view, COL_NOMBRE


if "df" not in st.session_state:
    st.warning("No hay datos para usar search_person")
    st.stop()

df = st.session_state.df
try:
    dview = person_view(
        df,
        sorted({name for name in df[COL_NOMBRE] if name}),
        st.session_state.schedule_by_name,
        CALENDAR_BUFFER
    ) 
except Exception as ex:
    st.error(f"No se puedo mostrar la vista: {ex}")