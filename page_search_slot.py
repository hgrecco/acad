from collections import defaultdict
import streamlit as st
import pandas as pd

from common import DOW_2_NUM, COL_NOMBRE, person_view, build_schedule, CALENDAR_BUFFER, COL_STATUS, com_string, parse_into_event, ScheduleEvent

@st.cache_data
def get_vacant_options(sdf: pd.DataFrame) -> dict[str, tuple[int, ScheduleEvent]]:
    return dict(sorted(
        { com_string(row): parse_into_event(row)
          for _, row in sdf[sdf[COL_STATUS] == "VACANTE"].iterrows()
        }.items()
    ))


@st.cache_data
def get_areas(d: dict[str, tuple[str, str]]) -> dict[str, list[str]]:
    out = defaultdict(list)

    for k, v in d.items():
        out[v[0]].append(k)

    return out


if "df" not in st.session_state:
    st.warning("No hay datos para usar slot_finder")
    st.stop()

df = st.session_state.df
schedule_by_name = st.session_state.schedule_by_name

picker_options = get_vacant_options(df)

def _update():
    value = st.session_state.page_search_slot_picker
    dow, sch_ev= picker_options[value]
    for k, v in DOW_2_NUM.items():
        if dow == v:
            st.session_state.page_search_slot_day = k
            break
    st.session_state.page_search_slot_start = sch_ev.start
    st.session_state.page_search_slot_stop = sch_ev.stop

picker = st.selectbox(
    "Elegí la franja horaria de un curso vacante",
    options=list(picker_options.keys()),
    on_change=_update,
    key="page_search_slot_picker",
)

st.caption("o elegila arbitrariamente")
col1, col2, col3= st.columns(3)
with col1:
    day = st.selectbox("Dia", tuple(DOW_2_NUM.keys()), key="page_search_slot_day")
with col2:
    start = st.time_input("Desde", key="page_search_slot_start")
with col3:
    stop = st.time_input("Hasta", key="page_search_slot_stop")

AREAS_2_PERSONAS = get_areas(df.attrs["personas"])
if df.attrs["personas"]:
    areas = st.multiselect(
        "Areas", 
        options=sorted(AREAS_2_PERSONAS.keys()), 
        default=sorted(AREAS_2_PERSONAS.keys()),
    )
    if areas:
        sel = df[COL_NOMBRE].isin(sum((AREAS_2_PERSONAS[k] for k in areas), start=[]))
    else:
        sel = slice(-1)
else:
    sel =  slice(-1)

present = st.checkbox(f"Sólo incluir personas que tengan otras actividades el {day}")

options = []
for selected_name, gdf in df[sel].groupby(COL_NOMBRE):
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