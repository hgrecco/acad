from collections import defaultdict
import streamlit as st
import pandas as pd
import datetime

from common import DOW_2_NUM, COL_NOMBRE, person_view, build_schedule, CALENDAR_BUFFER, COL_STATUS, com_string, parse_into_event, ScheduleEvent, Schedule, EVENT_TAG_VACANT, COL_FACULTAD

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
    day: str = st.selectbox("Dia", tuple(DOW_2_NUM.keys()), key="page_search_slot_day")
with col2:
    start: datetime.time = st.time_input("Desde", key="page_search_slot_start")
with col3:
    stop: datetime.time = st.time_input("Hasta", key="page_search_slot_stop")

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

with st.container(border=True):
    st.text("Sólo incluir personas que tengan otras actividades ")
    cols = st.columns(3)
    with cols[0]:
        present = st.checkbox(f"el {day}")
    with cols[1]:
        misma_facultad = st.checkbox(f"en {picker.split(",")[0]}")
    with cols[2]:
        misma_franja = st.checkbox("en la misma franja horaria")

options = []
for selected_name, gdf in df[sel].groupby(COL_NOMBRE):
    if selected_name == "":
        continue
    if misma_facultad and not picker.split(",")[0] in gdf[COL_FACULTAD].values:
        continue
    if selected_name in schedule_by_name:
        sch = schedule_by_name[selected_name]
    else:
        schedule_by_name[selected_name] = sch = build_schedule(gdf)
    if sch.is_busy(DOW_2_NUM[day], start, stop):
        continue
    if present and not sch[DOW_2_NUM[day]]:
        continue
    if misma_franja:
        if start < datetime.time(13):
            franja_start, franja_stop = datetime.time(8), datetime.time(13)
        elif start < datetime.time(18):
            franja_start, franja_stop = datetime.time(13), datetime.time(18)
        else:
            franja_start, franja_stop = datetime.time(18), datetime.time(23)
        for dow in range(7):
            if sch.is_busy(dow, franja_start, franja_stop):
                break
        else:
            continue
    options.append(selected_name)

sch = Schedule()
sch.add_event(DOW_2_NUM[day], ScheduleEvent(start, stop, "Curso a completar", EVENT_TAG_VACANT))
schedule_by_name["Curso a completar"] = sch

st.divider()

dview = person_view(
    df,
    options,
    schedule_by_name,
    CALENDAR_BUFFER,
    sch
) 