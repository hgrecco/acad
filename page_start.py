

import streamlit as st

from common import COL_NOMBRE, MULTICOL_COMISION, COL_FACULTAD, COL_CARRERA, REQUIRED_COLS, version


if "df" not in st.session_state:
    st.markdown(
f"""
**Estructura de los datos**

Un archivo de excel (`.xlsx`) con una hoja para cada facultad. 
Cada hoja debe contener una fila por asignación docente con al menos las siguientes columnas:
{"\n- ".join(REQUIRED_COLS)}

Las hojas cuyo nombre inician con `_` son ignoradas.

**Método para importar datos**

1. A través de un archivo en tu computadora.
2. A través de un archivo en la web compartido como sólo lectura.
""")
else:
    df = st.session_state.df

    st.markdown(
f"""
**Descripción de los datos**
- {len(df)} filas.
- {len(df[COL_FACULTAD].unique())} facultades.
- {len(df.groupby([COL_FACULTAD, COL_CARRERA]))} carreras.
- {len(df.groupby(MULTICOL_COMISION))} comisiones.
- {len(df[COL_NOMBRE].unique())} personas.

---

**Fuente**
- Acceso: {df.attrs["import_datetime"]}
- Origen: `{df.attrs["url"]}`
""")
    st.divider()
    st.markdown(f"*version de la aplicación: {version}*")