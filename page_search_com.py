import streamlit as st

from common import generate_schedule_image, build_schedule, CALENDAR_BUFFER, COL_FACULTAD, COL_ASIGNATURA, DERIVED_COL_YEAR_TURNO_COM


if "df" not in st.session_state:
    st.warning("No hay datos para usar slot_finder")
    st.stop()

df = st.session_state.df

facultad = st.selectbox("Facultad", sorted(df[COL_FACULTAD].unique()))
if facultad:
    sdf1 = df[df[COL_FACULTAD] == facultad]
    asignatura = st.selectbox("Asignatura", sorted(sdf1[COL_ASIGNATURA].unique()))
else:
    sdf1 = None
    asignatura = None
        
if asignatura:
    sdf2 = sdf1[sdf1[COL_ASIGNATURA] == asignatura]
    com = st.selectbox("Año/Turno/Comisión", sorted(sdf2[DERIVED_COL_YEAR_TURNO_COM].unique()))
else:
    sdf2 = None
    com_content = None
    year = None

if com is not None:
    sdf3 = sdf2[sdf2[DERIVED_COL_YEAR_TURNO_COM] == com]
    sch = build_schedule(sdf3)
    generate_schedule_image(sch, CALENDAR_BUFFER)

    st.image(CALENDAR_BUFFER)        
    st.dataframe(sdf3, height=300, hide_index=True, use_container_width=True)
