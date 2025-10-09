import streamlit as st
import pandas as pd
from shapely.geometry import LineString, Point
from geopy.distance import geodesic
from io import BytesIO

st.title("GPS - PK")

st.sidebar.header("Subir archivos")
puntos_file = 'sarmiento.csv'
sospechas_file = st.sidebar.file_uploader("Excel con coordenadas a buscar (Latitude, Longitude)", type=["xlsx"])

# --- Leer CSV de puntos fijos ---
df_puntos = pd.read_csv(puntos_file)
df_puntos.columns = df_puntos.columns.str.strip().str.lower()
df_puntos = df_puntos.dropna(subset=['latitude', 'longitude', 'km'])

# --- Crear LineString de la traza ---
linea_traza = LineString(df_puntos[['longitude', 'latitude']].values)

# --- Calcular distancia de sospechas a la línea ---
if sospechas_file:
    sospechas_df = pd.read_excel(sospechas_file)
    sospechas_df.columns = sospechas_df.columns.str.strip().str.lower()
    sospechas_df = sospechas_df.dropna(subset=['latitude', 'longitude'])

    if 'resultados_linea' not in st.session_state:
        resultados = []
        progress = st.progress(0)
        status_text = st.empty()
        total = len(sospechas_df)

        for i, row in enumerate(sospechas_df.itertuples()):
            point = Point(row.longitude, row.latitude)

            # Punto más cercano en la línea
            nearest_point_on_line = linea_traza.interpolate(linea_traza.project(point))
            lat_cercana = nearest_point_on_line.y
            lon_cercana = nearest_point_on_line.x

            # Distancia mínima a la línea en metros
            distancia_deg = point.distance(nearest_point_on_line)
            distancia_m = distancia_deg * 111000
            distancia_m_str = f"{distancia_m:,.2f}".replace('.', ',')

            # Encontrar el punto CSV más cercano para obtener el km
            df_puntos['distancia'] = df_puntos.apply(
                lambda r: geodesic((row.latitude, row.longitude), (r['latitude'], r['longitude'])).km * 1000,
                axis=1
            )
            punto_cercano = df_puntos.loc[df_puntos['distancia'].idxmin()]

            resultados.append({
                'latitude_busq': row.latitude,
                'longitude_busq': row.longitude,
                'lat_cercana': lat_cercana,
                'lon_cercana': lon_cercana,
                'km_punto_cercano': punto_cercano['km'],
                'distancia_m': distancia_m_str
            })

            status_text.text(f'{i+1} de {total} puntos procesados')

            progress.progress((i + 1) / total)

        st.session_state.resultados_linea = pd.DataFrame(resultados)

    st.subheader("Resultados")
    st.dataframe(st.session_state.resultados_linea)

    # Descargar Excel
    def to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Resultados')
        return output.getvalue()

    excel_data = to_excel(st.session_state.resultados_linea)
    st.download_button(
        label="Descargar resultados",
        data=excel_data,
        file_name="resultados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Subí un excel con las columnas Latitude y Longitude.")