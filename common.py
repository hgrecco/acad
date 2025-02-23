import streamlit as st
import io
import datetime
import pandas as pd
import pytz
from typing import Any, Literal, Mapping, NamedTuple
import requests
from collections import defaultdict

from calendar_view.calendar import Calendar
from calendar_view.core.event import EventStyles
from calendar_view.core import data

from functools import cache

type DOW = Literal[0, 1, 2, 3, 4, 5, 6]

version = "2025-02-23"

DOW_2_NUM: dict[str, DOW]= {
    "Lunes": 0,
    "Martes": 1,
    "Miércoles": 2,
    "Jueves": 3,
    "Viernes": 4,
    "Sábado": 5,
    "Domingo": 6,
}

EVENT_TAG_OK = 1
EVENT_TAG_ERROR = 2
EVENT_TAG_VACANT = 3
EVENT_TAG_LICENSE = 4

TAG_TO_STYLE = {
    1: EventStyles.GREEN, 
    2: EventStyles.RED,
    3: EventStyles.BLUE,
    4: EventStyles.GRAY,
}


COL_FACULTAD = "Facultad"
COL_CARRERA = "Carrera"
COL_ASIGNATURA = "Asignatura"
COL_YEAR = "Año"
COL_TURNO = "Turno"
COL_COMISION = "Com"
MULTICOL_COMISION = [COL_FACULTAD, COL_CARRERA] + [COL_ASIGNATURA, COL_YEAR, COL_YEAR, COL_COMISION]
COL_NOMBRE = "Nombre"
COL_HORARIOS = "Horarios"
COL_STATUS = "Estado"
DERIVED_COL_YEAR_TURNO_COM = "Año_Turno_Com"

# COL_FACULTAD is added later 
REQUIRED_COLS = [
    COL_CARRERA, COL_ASIGNATURA, COL_YEAR, COL_YEAR, COL_COMISION,
    COL_NOMBRE, COL_HORARIOS, COL_STATUS
]

CALENDAR_BUFFER = io.BytesIO()

@cache
def parse_time(s: str) -> datetime.time:
    if ":" not in s:
        return datetime.time(int(s.strip()))
    h, m = s.split(":")
    return datetime.time(int(h.strip()), int(m.strip()))
    


class ScheduleEvent(NamedTuple):
    start: datetime.time
    stop: datetime.time
    title: str
    tag: int

    @property
    def duration(self) -> float:
        dt1 = datetime.datetime.combine(datetime.datetime.min, self.start)
        dt2 = datetime.datetime.combine(datetime.datetime.min, self.stop)
        
        # Compute the difference in seconds
        diff_seconds = (dt2 - dt1).total_seconds()
        
        # Convert seconds to hours
        diff_hours = diff_seconds / 3600  
        return diff_hours


class Schedule(defaultdict[DOW, list[ScheduleEvent]]):
    def __init__(self):
        super().__init__(list)

    def add_event(self, dow: DOW, event: ScheduleEvent):
        self[dow].append(event)

    def create_and_add_event(self, dow: DOW, start_str: str, stop_str: str, title: str, *, tag: int = 0):
        self[dow].append(ScheduleEvent(
            parse_time(start_str), 
            parse_time(stop_str), 
            title, tag)
            )

    def hours(self, dow: DOW) -> float:
        return sum(ev.duration for ev in self[dow])

    def is_busy(self, dow: DOW, start: datetime.time, stop: datetime.time) -> bool:
        return any(not (ev.stop <= start or ev.start >= stop) for ev in self[dow])
    

def parse(s):
    if pd.isna(s):
        return
    
    try:
        dow, chk1, start, chk2, stop, chk3 = s.strip().split(" ")
    except Exception as ex:
        raise ValueError(f"Invalid time format: {s}\n{n}")
    if chk1 != "de" or chk2 != "a" or chk3 != "h":
        raise ValueError(f"Invalid time format: {s}")
    
    return dow, start.replace(".", ":"), stop.replace(".", ":")


def parse_into_event(row: Mapping[str, Any], *, title_prefix: str = "") -> tuple[int, ScheduleEvent]:
    title = title_prefix + com_string(row)

    try:
        dow, start_str, stop_str = parse(row["Horarios"])
        dow = DOW_2_NUM[dow]
        if row[COL_STATUS] in ("X", "XP"):
            tag = EVENT_TAG_OK
        elif row[COL_STATUS] in ("LICENCIA"):
            tag = EVENT_TAG_LICENSE
        elif row[COL_STATUS] in ("VACANTE"):
            tag = EVENT_TAG_VACANT
        else:
            tag = EVENT_TAG_ERROR
        start = parse_time(start_str)
        stop = parse_time(stop_str)
    except Exception as ex:
        title += f" ({row['Horarios']}) {ex}"
        dow = 6
        start = datetime.time(8)
        stop = datetime.time(9)
        tag = EVENT_TAG_ERROR    

    return dow, ScheduleEvent(start, stop, title, tag)


def com_string(row: Mapping[Any, Any]) -> str:
    return f"{row[COL_FACULTAD]}, {row[COL_CARRERA]}, {row[COL_ASIGNATURA]} - {row[DERIVED_COL_YEAR_TURNO_COM]}"


def build_schedule(sdf: pd.DataFrame) -> Schedule:

    sch = Schedule()

    for _, row in sdf.iterrows():

        dow, event = parse_into_event(row, title_prefix=f"{row[COL_STATUS]} | ")

        sch.add_event(dow, event)
    
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

                if df.empty:
                    import_log.append(
                        f"{sheet_name} | Error al importar, la hoja está vacía"
                    )
                    continue

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

                nan_columns = df.columns[df.isna().all()].tolist()
                if nan_columns:
                    import_log.append(
                        f"{sheet_name} | Atención las siguientes columnas no contienen datos: {nan_columns}"
                    )

                for col in ffill_columns:
                    df[col] = df[col].ffill()
                
                df[COL_NOMBRE] = df[COL_NOMBRE].fillna("").str.strip()
                df[COL_YEAR] = df[COL_YEAR].astype(int) 
                df[COL_STATUS] = df[COL_STATUS].astype(str).fillna("").str.strip()
                
                for col in [COL_CARRERA, COL_ASIGNATURA, COL_TURNO, COL_COMISION]:
                    df[col] = df[col].str.strip()

                fstring = "{0[%s]} / {0[%s]} / {0[%s]} " % (COL_YEAR, COL_TURNO, COL_COMISION)
                df[DERIVED_COL_YEAR_TURNO_COM] = df.agg(fstring.format, axis=1)


                df.insert(0, "Facultad", sheet_name)
                import_log.append(
                            f"{sheet_name} | Se importaron {len(df)} filas"
                        )
                out.append(df)
            except Exception as ex:
                import_log.append(
                            f"{sheet_name} | {ex}"
                        )

    if not out:
        raise Exception("No se encontraron los datos esperados:\n" + "\n-".join(import_log))

    outdf = pd.concat(out)
    outdf.attrs["import_log"] = import_log
    outdf.attrs["import_datetime"] = datetime.datetime.now(pytz.timezone("America/Argentina/Buenos_Aires")).strftime("%Y-%m-%d %H:%M:%S")
    return outdf



def read_into_session(content, **attrs: str):
    st.cache_data.clear()
    df = read(
                content,
                required_columns=REQUIRED_COLS,
                ffill_columns=(COL_CARRERA, COL_ASIGNATURA, COL_YEAR, COL_TURNO, COL_COMISION),
            )
    
    for k, v in attrs.items():
        df.attrs[k] = v

    st.session_state.df = df
    st.session_state.schedule_by_name = {}
    

def download(url: str):
    with st.spinner(f'Downloading {url}'):
        download_url = url.split("?")[0] + "?download=1"

        response = requests.get(download_url, stream=True)

        if response.status_code != 200:
            st.error(f"No se pudo bajar el archivo (status code {response.status_code})")
        else:
            read_into_session(io.BytesIO(response.content), url=url)  

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
                start=ev.start.strftime("%H:%M"), 
                end=ev.stop.strftime("%H:%M"), 
                title=ev.title, 
                style=TAG_TO_STYLE[ev.tag]
            )

    calendar.save(buffer)


def person_view(sdf: pd.DataFrame, options: list[Any], schedule_by_name: dict[str, Schedule], calendar_buffer: io.BytesIO):
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
