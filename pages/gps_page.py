# pages/gps_page.py
import flet as ft
import pandas as pd
from shapely.geometry import LineString, Point
from geopy.distance import geodesic
from tkinter import Tk, filedialog
from utils.utils import resource_path
import os

def gps_page(page: ft.Page):
    # --- Componentes base ---
    titulo = ft.Text("GPS - PK", size=24, weight=ft.FontWeight.BOLD)

    progreso = ft.ProgressBar(width=400)
    status = ft.Text("")

    km_desde_field = ft.TextField(label="Km desde", width=120)
    km_hasta_field = ft.TextField(label="Km hasta", width=120)

    resultados_table = ft.DataTable(columns=[
        ft.DataColumn(ft.Text("Latitude")),
        ft.DataColumn(ft.Text("Longitude")),
        ft.DataColumn(ft.Text("Lat Cercana")),
        ft.DataColumn(ft.Text("Lon Cercana")),
        ft.DataColumn(ft.Text("KM Cercano")),
        ft.DataColumn(ft.Text("Distancia (m)")),
    ])
    df_resultados = pd.DataFrame()

    # --- Buscar archivos base en /data ---
    data_dir = resource_path("data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)  # crea carpeta si no existe

    archivos_base = [f for f in os.listdir(data_dir) if f.endswith((".csv", ".xlsx"))]

    archivo_seleccionado = ft.Dropdown(
        label="Seleccionar ramal base",
        options=[ft.dropdown.Option(f) for f in archivos_base],
        width=300
    )

    df_puntos = None
    linea_traza = None

    def cargar_ramal(e):
        nonlocal df_puntos, linea_traza
        archivo = archivo_seleccionado.value
        if not archivo:
            page.snack_bar = ft.SnackBar(ft.Text("Seleccione un ramal primero."))
            page.snack_bar.open = True
            page.update()
            return

        ruta = os.path.join(data_dir, archivo)
        if ruta.endswith(".csv"):
            df_puntos = pd.read_csv(ruta)
        else:
            df_puntos = pd.read_excel(ruta)

        df_puntos.columns = df_puntos.columns.str.strip().str.lower()
        df_puntos = df_puntos.dropna(subset=['latitude', 'longitude', 'km'])
        linea_traza = LineString(df_puntos[['longitude', 'latitude']].values)

        page.snack_bar = ft.SnackBar(ft.Text(f"Ramal '{archivo}' cargado correctamente."))
        page.snack_bar.open = True
        page.update()

    boton_cargar_ramal = ft.ElevatedButton("Cargar ramal", on_click=cargar_ramal)

    def seleccionar_y_procesar_excel(e):
        nonlocal df_resultados
        if df_puntos is None:
            page.snack_bar = ft.SnackBar(ft.Text("⚠️ Primero cargá un ramal base."))
            page.snack_bar.open = True
            page.update()
            return

        try:
            km_desde = float(km_desde_field.value or 0)
            km_hasta = float(km_hasta_field.value or df_puntos['km'].max())
        except ValueError:
            page.snack_bar = ft.SnackBar(ft.Text("❌ Los valores de km deben ser numéricos."))
            page.snack_bar.open = True
            page.update()
            return

        df_segmento = df_puntos[(df_puntos['km'] >= km_desde) & (df_puntos['km'] <= km_hasta)]
        if df_segmento.empty:
            page.snack_bar = ft.SnackBar(ft.Text("⚠️ No hay puntos en ese rango de km."))
            page.snack_bar.open = True
            page.update()
            return

        linea_traza_segmento = LineString(df_segmento[['longitude', 'latitude']].values)

        # Tkinter para abrir archivo de sospechas
        root = Tk()
        root.withdraw()
        archivo_path = filedialog.askopenfilename(title="Seleccionar archivo de sospechas", filetypes=[("Archivos Excel", "*.xlsx")])
        root.destroy()
        if not archivo_path:
            return

        sospechas_df = pd.read_excel(archivo_path)
        sospechas_df.columns = sospechas_df.columns.str.strip().str.lower()
        sospechas_df = sospechas_df.dropna(subset=['latitude', 'longitude'])

        resultados = []
        total = len(sospechas_df)

        for i, row in enumerate(sospechas_df.itertuples(), start=1):
            point = Point(row.longitude, row.latitude)
            nearest_point_on_line = linea_traza_segmento.interpolate(linea_traza_segmento.project(point))
            lat_cercana = nearest_point_on_line.y
            lon_cercana = nearest_point_on_line.x
            distancia_m = geodesic((row.latitude, row.longitude), (lat_cercana, lon_cercana)).m

            idx_cercano = df_segmento['latitude'].sub(lat_cercana).abs() + df_segmento['longitude'].sub(lon_cercana).abs()
            km_cercano = df_segmento.loc[idx_cercano.idxmin(), 'km']

            resultados.append({
                'latitude_busq': row.latitude,
                'longitude_busq': row.longitude,
                'lat_cercana': lat_cercana,
                'lon_cercana': lon_cercana,
                'km_punto_cercano': km_cercano,
                'distancia_m': distancia_m
            })

            progreso.value = i / total
            status.value = f"{i} de {total} puntos procesados"
            page.update()

        df_resultados = pd.DataFrame(resultados)
        resultados_table.rows.clear()
        for r in resultados:
            resultados_table.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(r['latitude_busq']))),
                ft.DataCell(ft.Text(str(r['longitude_busq']))),
                ft.DataCell(ft.Text(str(r['lat_cercana']))),
                ft.DataCell(ft.Text(str(r['lon_cercana']))),
                ft.DataCell(ft.Text(str(r['km_punto_cercano']))),
                ft.DataCell(ft.Text(f"{r['distancia_m']:,.2f}".replace('.', ',')))
            ]))
        page.update()

    def descargar_excel(e):
        if df_resultados.empty:
            return
        root = Tk()
        root.withdraw()
        ruta = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")], title="Guardar resultados")
        root.destroy()
        if ruta:
            df_resultados.to_excel(ruta, index=False)
            page.snack_bar = ft.SnackBar(ft.Text(f"Archivo guardado en {ruta}"))
            page.snack_bar.open = True
            page.update()

    def limpiar_pantalla(e):
        nonlocal df_resultados
        df_resultados = pd.DataFrame()
        resultados_table.rows.clear()
        progreso.value = 0
        status.value = ""
        page.update()

    boton_subir = ft.ElevatedButton("Seleccionar archivo de sospechas", on_click=seleccionar_y_procesar_excel)
    boton_descargar = ft.ElevatedButton("Descargar resultados", on_click=descargar_excel)
    boton_limpiar = ft.ElevatedButton("Limpiar pantalla", on_click=limpiar_pantalla)

    # --- Layout ---
    return ft.Column([
        titulo,
        ft.Row([archivo_seleccionado, boton_cargar_ramal], spacing=10),
        ft.Row([km_desde_field, km_hasta_field]),
        ft.Row([boton_subir, boton_descargar, boton_limpiar], spacing=10),
        progreso,
        status,
        ft.Divider(),
        resultados_table
    ], spacing=10, expand=True)
