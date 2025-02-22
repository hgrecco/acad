import streamlit as st
import io
import datetime
import pandas as pd
import pytz
from typing import Any, Literal, NamedTuple
import requests

from calendar_view.calendar import Calendar
from calendar_view.core.event import Event, EventStyles
from calendar_view.core import data

from functools import cache

type DOW = Literal[0, 1, 2, 3, 4, 5, 6]

DOW_2_NUM: dict[str, DOW]= {
    "Lunes": 0,
    "Martes": 1,
    "Miércoles": 2,
    "Jueves": 3,
    "Viernes": 4,
    "Sábado": 5,
    "Domingo": 6,
}

COL_NOMBRE = "Nombre"

@cache
def time_str_to_float(s: str) -> float:
    if ":" in s:
        h, m = s.split(":")
        return float(h) + float(m) / 60
    return float(s)


class ScheduleEvent(NamedTuple):
    start_str: str
    stop_str: str
    title: str
    tag: int

    @property
    def start(self) -> float:
        return time_str_to_float(self.start_str)

    @property
    def stop(self) -> float:
        return time_str_to_float(self.stop_str)

    @property
    def duration(self) -> float:
        return self.stop - self.start


class Schedule(dict[DOW, list[ScheduleEvent]]):

    def __missing__(self, key: DOW) -> list[ScheduleEvent]:
        self[key] = value = list()
        return value

    def add_event(self, dow: DOW, start_str: str, stop_str: str, title: str, *, tag: int=0):
        self[dow].append(ScheduleEvent(start_str, stop_str, title, tag))

    def hours(self, dow: DOW) -> float:
        return sum((ev.duration for ev in self[dow]))
    
    def is_busy(self, dow: DOW, start: float, stop: float) -> bool:
        for ev in self[dow]:
            if ev.start < start < ev.stop:
                return True
            if ev.start < stop < ev.stop:
                return True
            if start < ev.start and ev.stop < stop:
                return True

        return False
    

def parse(s):
    if pd.isna(s):
        return
    try:
        dow, chk1, start, chk2, stop, chk3 = s.strip().split(" ")
    except:
        raise
    assert chk1 == "de"
    assert chk2 == "a"
    assert chk3 == "h"
    return (dow, start.replace(".", ":"), stop.replace(".", ":"))


def build_schedule(sdf: pd.DataFrame) -> Schedule:

    sch = Schedule()

    for _, row in sdf.iterrows():

        title = f"{row['Confirmación docente']} | {row['Facultad']}, {row["Carrera"]}, {row["Asignatura"]}. {int(row["Año"])}.{row["Turno"]}.{row["Com"]} "

        try:
            dow, start, stop = parse(row["Horarios"])
            dow = DOW_2_NUM[dow]
            tag = 1
        except Exception as ex:
            title += f" ({row['Horarios']}) {ex}"
            dow = 6
            start = "8:00"
            stop = "9:00"
            tag = 2
        
        sch.add_event(dow, start, stop, title, tag=tag)
    
    return sch


def read(p: str, *, required_columns: tuple[str] = tuple(), ffill_columns: tuple[str] = tuple()):
    out = []
    columns = None
    import_log = []
    with pd.ExcelFile(p, engine="openpyxl") as fi:
        for sheet_name in sorted(fi.sheet_names):
            if sheet_name.startswith("_"):
                import_log.append(
                    f"{sheet_name} | Salteando {sheet_name} porque el nombre inicia con _"
                )
                continue
            
            try:
                df = fi.parse(sheet_name=sheet_name)

                for col in tuple(required_columns) + tuple(ffill_columns): 
                    if col not in df.columns:
                        import_log.append(
                            f"{sheet_name} | Error al importar, no se encontró una columna requerida: {col}"
                        )
                    continue

                if columns is None:
                    columns = df.columns
                    import_log.append(
                        f"{sheet_name} | Definiendo columnas de referencia: {df.columns.to_list()}"
                    )
                elif all(df.columns != columns):
                    import_log.append(
                        f"{sheet_name} | Error al importar, las columnas no coinciden con la referencia: {df.columns.to_list()}"
                    )
                    continue

                for col in ffill_columns:
                    df[col] = df[col].ffill()
                
                df[COL_NOMBRE] = df[COL_NOMBRE].fillna("")
                df.insert(0, "Facultad", sheet_name)
                import_log.append(
                            f"{sheet_name} | Se importaron {len(df)} filas"
                        )
                out.append(df)
            except Exception as ex:
                import_log.append(
                            f"{sheet_name} | {ex}"
                        )

    outdf = pd.concat(out)
    outdf.attrs["import_log"] = import_log
    outdf.attrs["import_datetime"] = datetime.datetime.now(pytz.timezone("America/Argentina/Buenos_Aires")).strftime("%Y-%m-%d %H:%M:%S")
    return outdf


def read_into_session(content, **attrs: str):
    df = read(
                content,
                required_columns=(COL_NOMBRE, "Horarios", "Confirmación docente"),
                ffill_columns=("Carrera", "Asignatura", "Año", "Turno", "Com"),
            )
    
    for k, v in attrs.items():
        df.attrs[k] = v

    st.session_state.df = df
    st.session_state.schedule_by_name = {}
    st.rerun()

def download(url: str):
    with st.spinner(f'Downloading {url}'):
        download_url = url.split("?")[0] + "?download=1"

        response = requests.get(download_url, stream=True)

        if response.status_code != 200:
            st.error(f"No se pudo bajar el archivo (status code {response.status_code})")
        else:
            read_into_session(response.content, url=url)  


@st.dialog("Elegí un archivo")
def upload_file_dialog():
    uploaded_file = st.file_uploader("Elegí un archivo", type=['xlsx'])
    if st.button("Submit"):
        if uploaded_file is not None:
            read_into_session(uploaded_file)


@st.dialog("Elegí un link")
def download_from_sharepoint_dialog():
    if "df" in st.session_state:
        default = st.session_state.df.attrs.get("url")
    else:
        default = ""

    url = st.text_input("Link al archivo", value=default)
    if st.button("Submit"):
        download(url)

def generate_schedule_image(sch: Schedule, buffer: io.BytesIO):
    config = data.CalendarConfig(
        lang='es',
        title='Horario',
        dates='Mo - Su',
        hours='7 - 23',
        legend=True,
        show_date=False,
        show_year=False,
    )
    data.validate_config(config)

    calendar = Calendar.build(config)

    for dow, events in sorted(sch.items()):
        for ev in events:
            calendar.add_event(
                day_of_week=dow,
                start=ev.start_str, 
                end=ev.stop_str, 
                title=ev.title, 
                style=EventStyles.RED if ev.tag == 2 else EventStyles.GREEN
            )

    calendar.save(buffer)


def docente_view(sdf: pd.DataFrame, options: list[Any], schedule_by_name: dict[str, Schedule], calendar_buffer: io.BytesIO):
    selected_name = st.selectbox(
        f'Docente ({len(options)})',
        options=options, 
        index=0
    )

    filtered_df = sdf[sdf[COL_NOMBRE] == selected_name]
    
    if selected_name in schedule_by_name:
        sch = schedule_by_name[selected_name]
    else:
        schedule_by_name[selected_name] = sch = build_schedule(filtered_df)

    elements = st.container()

    generate_schedule_image(sch, calendar_buffer)
    with elements:
        st.image(calendar_buffer)        
        st.dataframe(filtered_df, height=300, hide_index=True, use_container_width=True)
    return elements

def main():
    calendar_buffer = io.BytesIO()

    if "df" in st.session_state:
        df = st.session_state.df
        schedule_by_name = st.session_state.schedule_by_name
    else:
        df = None
        schedule_by_name: dict[str, Schedule] = {}
    
    with st.sidebar:
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Via Archivo 📎"):
                upload_file_dialog()
        
        with col2:
            if st.button("Via Link 🔗"):
                download_from_sharepoint_dialog()

        with col3:          
            if df is not None:
                url = st.session_state.df.attrs.get("url")
                if url:
                    if st.button("↻"):
                        download(url)
                    

        if df is not None:
            st.header(f"Datos")
            st.markdown(f"**Actualización**: {df.attrs["import_datetime"]}")
            st.markdown(f"**Filas**: {len(df)}")
                    
            api_options = ("Importar", "Por docente", "Con hora libre")
            selected_api = st.selectbox(
                label="Visualización:",
                options=api_options,
            )

    if df is not None:
        if selected_api == "Importar":
            st.header("Registro de importación")
            for k in df.attrs["import_log"]:
                st.text(k)

        if selected_api == "Por docente":
            dview = docente_view(
                df,
                sorted({name for name in df[COL_NOMBRE] if name}),
                schedule_by_name,
                calendar_buffer
            ) 

        if selected_api == "Con hora libre":
            col1, col2, col3= st.columns(3)
            _, _, col5= st.columns(3)
            with col5:
                present = st.checkbox("Sólo día presentes")
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
            
            dview = docente_view(
                df,
                options,
                schedule_by_name,
                calendar_buffer
            ) 


if __name__ == "__main__":
    date = "2025-11-21"

    st.set_page_config(
        page_title="Académica", page_icon=":chart_with_upwards_trend:",
        layout="wide",
    )
    main()
    with st.sidebar:
        st.markdown("---")
        st.markdown(
            f'<div style="margin-top: 0.75em;">version: {date}</div>',
            unsafe_allow_html=True,
        )
