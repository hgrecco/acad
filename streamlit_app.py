import streamlit as st

from common import read_into_session, download

@st.dialog("Importar desde tu computadora")
def upload_file_dialog():
    uploaded_file = st.file_uploader("Elegí un archivo", type=['xlsx'])
    if st.button("Subir archivo", icon=":material/upload_file:"):
        if uploaded_file is not None:
            read_into_session(uploaded_file, url=uploaded_file.name)
            st.switch_page("page_start.py")


@st.dialog("Importar desde la web")
def download_from_sharepoint_dialog():
    if "df" in st.session_state:
        default = st.session_state.df.attrs.get("url")
        if not default.startswith("http"):
            default = ""
    else:
        default = ""

    url = st.text_input("Link al archivo", value=default)
    if st.button("Obtener datos", icon=":material/cloud_download:"):
        url = url.strip()
        if url == "":
            st.error("El link no puede estar vacio.")
        elif not url.startswith("http"):
            st.error("El link es inválido.")            
        else:
            try:
                download(url)
                st.switch_page("page_start.py")
            except Exception as ex:
                st.error(f"No se pudo obtener los datos: {ex}")

@st.dialog("(Re)Importar desde la web")
def redownload_from_sharepoint_dialog():
    default = st.session_state.df.attrs.get("url")
    download(default)
    st.switch_page("page_start.py")


def main():

    if "df" in st.session_state:
        df = st.session_state.df
    else:
        df = None

    pages = {
        "": [
            st.Page("page_start.py", title="Inicio")
        ],
        "Importar 📥": [
            st.Page(upload_file_dialog, title="desde tu computadora", icon=":material/upload_file:"),
            st.Page(download_from_sharepoint_dialog, title="desde la web", icon=":material/cloud_download:")
        ]
    }

    if df is not None:
        url = st.session_state.df.attrs.get("url")
        if url and url.startswith("http"):
            pages["Importar 📥"].append(st.Page(redownload_from_sharepoint_dialog, title="desde la web (actualizar)", icon=":material/refresh:"))
            

    if df is not None:
        pages = {**pages, 
            "Reporte 📄": [
                st.Page("page_report_import.py", title="de importación"),
                st.Page("page_report_time.py", title="de errores de horario"),
                st.Page("page_report_personal_file.py", title="de horarios por persona", icon=":material/download:"),
            ],
            "Buscar 🔎": [
                st.Page("page_search_person.py", title="persona por nombre"),
                st.Page("page_search_slot.py", title="persona por horario disponible"),
                st.Page("page_search_com.py", title="comisión"),
                st.Page("page_search_status.py", title="asignación por estado"),
            ],
        }

    pg = st.navigation(pages)
    pg.run()

if __name__ == "__main__":
    # if "df" not in st.session_state:
    #     read_into_session("demo.xlsx", url="demo.xlsx")
    st.set_page_config(
        page_title="Asistencia académica", page_icon="🎓",
        layout="wide",
    )

    st.markdown(
        """
        <style>
        div.stToolbarActions {
            visibility: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    main()