"""
Aplicación interactiva del catálogo de Netflix.
Librerías: streamlit y pandas.
Ejecutar en local: streamlit run app.py
"""

import io
import os

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------
# 1. Configuración de la página
# ---------------------------------------------------------------
st.set_page_config(page_title="Catálogo de Netflix", page_icon="🎬", layout="wide")

# ---------------------------------------------------------------
# 2. Cargar y limpiar los datos
#    st.cache_data guarda el resultado para no recalcularlo
#    cada vez que el usuario mueve un filtro.
# ---------------------------------------------------------------
@st.cache_data
def cargar_datos(contenido: bytes) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(contenido))
    df["country"] = df["country"].fillna("Desconocido")
    df["director"] = df["director"].fillna("Sin dato")
    df["date_added"] = pd.to_datetime(df["date_added"].str.strip(), errors="coerce")
    return df

ARCHIVO_LOCAL = "netflix_titles.csv"

if os.path.exists(ARCHIVO_LOCAL):
    # El CSV está en el repositorio: se carga directamente
    with open(ARCHIVO_LOCAL, "rb") as f:
        contenido = f.read()
else:
    # Si el CSV no está en el repositorio, el usuario lo sube
    subido = st.sidebar.file_uploader("Sube netflix_titles.csv", type="csv")
    if subido is None:
        st.info("Sube el archivo netflix_titles.csv en la barra lateral para comenzar.")
        st.stop()
    contenido = subido.getvalue()

df = cargar_datos(contenido)

# ---------------------------------------------------------------
# 3. Encabezado
# ---------------------------------------------------------------
st.title("🎬 Catálogo de Netflix")
st.write("Explora películas y series del catálogo. Usa los filtros de la izquierda.")

# ---------------------------------------------------------------
# 4. Filtros
# ---------------------------------------------------------------
st.sidebar.header("Filtros")

tipos = st.sidebar.multiselect(
    "Tipo de título",
    options=["Movie", "TV Show"],
    default=["Movie", "TV Show"],
)

anio_min = int(df["release_year"].min())
anio_max = int(df["release_year"].max())
rango_anios = st.sidebar.slider(
    "Año de estreno", min_value=anio_min, max_value=anio_max, value=(2000, anio_max)
)

paises_disponibles = (
    df["country"]
    .str.split(", ")
    .explode()
    .value_counts()
    .drop("Desconocido", errors="ignore")
    .head(30)
    .index.tolist()
)
pais = st.sidebar.selectbox("País", ["Todos"] + paises_disponibles)

# Aplicamos los filtros
filtrado = df[df["type"].isin(tipos) & df["release_year"].between(*rango_anios)]
if pais != "Todos":
    filtrado = filtrado[filtrado["country"].str.contains(pais, regex=False)]

if filtrado.empty:
    st.warning("No hay títulos con esos filtros. Prueba con otra combinación.")
    st.stop()

# ---------------------------------------------------------------
# 5. Indicadores
# ---------------------------------------------------------------
peliculas = int((filtrado["type"] == "Movie").sum())
series = len(filtrado) - peliculas

col1, col2, col3 = st.columns(3)
col1.metric("Títulos", f"{len(filtrado):,}")
col2.metric("Películas", f"{peliculas:,}")
col3.metric("Series", f"{series:,}")

# ---------------------------------------------------------------
# 6. Gráficas
# ---------------------------------------------------------------
st.subheader("Películas vs. series")
st.bar_chart(filtrado["type"].value_counts())

st.subheader("Top 10 países")
top_paises = (
    filtrado["country"]
    .str.split(", ")
    .explode()
    .value_counts()
    .drop("Desconocido", errors="ignore")
    .head(10)
)
st.bar_chart(top_paises)

st.subheader("Estrenos por año")
st.line_chart(filtrado.groupby("release_year").size())

# ---------------------------------------------------------------
# 7. Tabla de datos
# ---------------------------------------------------------------
with st.expander("Ver los datos filtrados"):
    st.dataframe(filtrado[["title", "type", "release_year", "country", "rating"]])
