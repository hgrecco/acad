
import streamlit as st
import pandas as pd
from collections import defaultdict

from export_helper import persona_export_form, generate_excel_content, create_zip_in_memory, safe_filename
from common import COL_NOMBRE


if "df" not in st.session_state:
    st.warning("No hay datos para usar page_report_personal_file")
    st.stop()

df = st.session_state.df

persona_export_form(df)