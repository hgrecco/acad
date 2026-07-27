import streamlit as st

from common import (
    CALENDAR_BUFFER,
    COL_ASIGNATURA,
    COL_FACULTAD,
    DERIVED_COL_YEAR_TURNO_COM,
    DOW_2_NUM,
    build_schedule,
    df_to_records,
)
from occupancy import generate_occupancy_figure

NO_FILTER = "Sin filtro"

if "df" not in st.session_state:
    st.warning("No hay datos para usar slot_finder")
    st.stop()

df = st.session_state.df

dows = st.multiselect(
    "Dias",
    options=list(DOW_2_NUM.keys()), 
    default=list(DOW_2_NUM.keys())[:5],
)

st.caption("Rango horario")
col1, col2 = st.columns(2)
with col1:
    start = st.time_input("Desde", key="page_search_slot_start", value="07:00")
with col2:
    stop = st.time_input("Hasta", key="page_search_slot_stop", value="23:00")

facultad = st.selectbox("Facultad", [NO_FILTER] + sorted(df[COL_FACULTAD].unique()))
if facultad and facultad != NO_FILTER:
    sdf1 = df[df[COL_FACULTAD] == facultad]
    asignatura = st.selectbox("Asignatura", [NO_FILTER] + sorted(sdf1[COL_ASIGNATURA].unique()))
else:
    sdf1 = df
    asignatura = None
        
if asignatura and asignatura != NO_FILTER:
    sdf2 = sdf1[sdf1[COL_ASIGNATURA] == asignatura]
    com = st.selectbox("Año/Turno/Comisión", [NO_FILTER] + sorted(sdf2[DERIVED_COL_YEAR_TURNO_COM].unique()))
else:
    sdf2 = sdf1
    com = None

if com and com != NO_FILTER:
    sdf3 = sdf2[sdf2[DERIVED_COL_YEAR_TURNO_COM] == com]
else:
    sdf3 = sdf2

calendar_err = None
try:
    sch = build_schedule(sdf3)
    events = list(sch.yield_events())
    if events:
        generate_occupancy_figure(
            events, 
            CALENDAR_BUFFER,
            list(map(DOW_2_NUM.get, dows)), start, stop
        )
    else:
        calendar_err = "No hay cursos con estas características."
except Exception as ex:
    calendar_err = f"No se pudo generar el horario. Revise que la planilla este correcta.\n{ex}"

if calendar_err:
    st.error(calendar_err)
else:
    st.image(CALENDAR_BUFFER)       

    try:
        st.dataframe(
            df_to_records(sdf3), 
            height=300, width='stretch',
            hide_index=True
        )
    except Exception as ex:
        st.error(f"No se pudo mostrar la tabla. {ex}")
