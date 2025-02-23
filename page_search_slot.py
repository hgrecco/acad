import streamlit as st

from common import DOW_2_NUM, COL_NOMBRE, person_view, build_schedule, CALENDAR_BUFFER


if "df" not in st.session_state:
    st.warning("No hay datos para usar slot_finder")
    st.stop()

df = st.session_state.df
schedule_by_name = st.session_state.schedule_by_name

col1, col2, col3= st.columns(3)
_, _, col5= st.columns(3)
with col5:
    present = st.checkbox("Sólo días con horas")
with col1:
    day = st.selectbox("Dia", tuple(DOW_2_NUM.keys()))
with col2:
    start = st.number_input("Desde", 0, 24, 9)
with col3:
    stop = st.number_input("Hasta", 0, 24, 10)

options = []
for selected_name, gdf in df.groupby(COL_NOMBRE):
    if selected_name == "":
        continue
    if selected_name in schedule_by_name:
        sch = schedule_by_name[selected_name]
    else:
        schedule_by_name[selected_name] = sch = build_schedule(gdf)
    if sch.is_busy(DOW_2_NUM[day], start, stop):
        continue
    if present and not sch[DOW_2_NUM[day]]:
        continue
    options.append(selected_name)

st.divider()

dview = person_view(
    df,
    options,
    schedule_by_name,
    CALENDAR_BUFFER
) 