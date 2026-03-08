import streamlit as st

from common import generate_schedule_image, build_schedule, CALENDAR_BUFFER, COL_FACULTAD, COL_ASIGNATURA, DERIVED_COL_YEAR_TURNO_COM, df_to_records


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

    try:
        generate_schedule_image(sch, CALENDAR_BUFFER)
        calendar_err = ""
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
