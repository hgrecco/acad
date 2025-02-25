import streamlit as st
import pandas as pd

from common import parse, COL_HORARIOS, COL_NOMBRE

if "df" not in st.session_state:
    st.warning("No hay datos para usar page_report_time")
    st.stop()

df = st.session_state.df

en_asignacion: set[str] = set(df[COL_NOMBRE])
en_mails: set[str] = set(df.attrs["personas"].keys())

en_ambos = en_asignacion.intersection(en_mails)

solo_en_asignacion = en_asignacion.difference(en_mails)
solo_en_mails = en_mails.difference(en_asignacion)

st.caption(f":interrobang: Personas presentes solo en las asignaciones (:red[{len(solo_en_asignacion)}])")
st.dataframe(
    pd.DataFrame.from_records([{COL_NOMBRE: s} for s in sorted(solo_en_asignacion) if s.strip()]), 
    hide_index=True, use_container_width=True
)


st.caption(f":warning: Personas presentes solo en la lista de mails (:orange[{len(solo_en_mails)}])")
st.dataframe(
    pd.DataFrame.from_records([{COL_NOMBRE: s} for s in sorted(solo_en_mails) if s.strip()]), 
    hide_index=True, use_container_width=True
)

st.caption(f":partying_face: Personas presentes en ambos listados (:green[{len(en_ambos)}])")
st.dataframe(
    pd.DataFrame.from_records([{COL_NOMBRE: s}for s in sorted(en_ambos) if s.strip()]), 
    hide_index=True, use_container_width=True
)
