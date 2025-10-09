import streamlit as st
import pandas as pd
from geopy.distance import geodesic
from io import BytesIO

st.title("GPS - PK más cercano")

st.sidebar.header("Subir archivos")
# Archivo con puntos fijos, se encuentra en la carpeta, el script ya toma el archivo como referencia
puntos_file = 'sarmiento.csv'

# Uploader para subir el archivo con las sospechas. Tiene que ser un archivo excel con una columna con el encabezado Latitude y otra con el encabezado Longitude. El archivo 'sospechas.xlsx' que se encuentra en la carpeta del script es un ejemplo

sospechas_file = st.sidebar.file_uploader("Excel con coordenadas a buscar (Latitude, Longitude)", type=["xlsx"])

# Una vez subido el archivo excel se calculan los puntos mas cercanos

if puntos_file and sospechas_file:
    # Leer archivos
    df_puntos = pd.read_csv(puntos_file)
    sospechas_df = pd.read_excel(sospechas_file)

    # Normalizar columnas
    df_puntos.columns = df_puntos.columns.str.strip().str.lower()
    sospechas_df.columns = sospechas_df.columns.str.strip().str.lower()

    # Quitar filas con NaN
    df_puntos = df_puntos.dropna(subset=['latitude', 'longitude'])
    sospechas_df = sospechas_df.dropna(subset=['latitude', 'longitude'])

    st.write(f"Puntos cargados: {len(df_puntos)}")
    st.write(f"Coordenadas a buscar: {len(sospechas_df)}")

    # --- Usar session_state para no recalcular ---
    if 'resultados' not in st.session_state:
        resultados = []
        progress = st.progress(0)
        total = len(sospechas_df)

        for i, row in enumerate(sospechas_df.itertuples()):
            lat_busq = row.latitude
            lon_busq = row.longitude

            df_puntos['distancia'] = df_puntos.apply(
                lambda r: geodesic((lat_busq, lon_busq), (r['latitude'], r['longitude'])).km * 1000,  # metros
                axis=1
            )

            punto_cercano = df_puntos.loc[df_puntos['distancia'].idxmin()]

            resultados.append({
                'latitude_busq': lat_busq,
                'longitude_busq': lon_busq,
                'km_cercano': punto_cercano['km'],
                'lat_cercano': punto_cercano['latitude'],
                'lon_cercano': punto_cercano['longitude'],
                'distancia_m': punto_cercano['distancia']
            })

            progress.progress((i + 1) / total)

        st.session_state.resultados = pd.DataFrame(resultados)

    # Mostrar resultados
    st.dataframe(st.session_state.resultados)

    # Descargar Excel
    def to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Resultados')
        return output.getvalue()

    excel_data = to_excel(st.session_state.resultados)

    st.download_button(
        label="Descargar resultados",
        data=excel_data,
        file_name="resultados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Subí un excel con las columnas Latitude y Longitude para calcular los PK más cercanos.")

