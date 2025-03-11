
import streamlit as st
import pandas as pd
from collections import defaultdict

from export_helper import school_export_form, generate_excel_content, create_zip_in_memory, safe_filename
from common import COL_FACULTAD, COL_CARRERA, COL_ASIGNATURA, DERIVED_COL_YEAR_TURNO_COM


if "df" not in st.session_state:
    st.warning("No hay datos para usar page_report_school_file")
    st.stop()

df = st.session_state.df

school_export_form(df)