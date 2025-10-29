import flet as ft
import pandas as pd
from shapely.geometry import LineString, Point
from geopy.distance import geodesic
from tkinter import Tk, filedialog
import os
import sys


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def gps_page(page: ft.Page):
    # --- Componentes base ---
    titulo = ft.Text("GPS - PK", size=24, weight=ft.FontWeight.BOLD)

    progreso = ft.ProgressBar(width=400)
    status = ft.Text("")

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
    archivos_base = [f for f in os.listdir(data_dir) if f.endswith((".csv", ".xlsx"))]
    if not archivos_base:
        return ft.Text("⚠️ No hay archivos en la carpeta 'data'. Subí uno desde 'Carga de progresivado'.")

    archivo_seleccionado = ft.Dropdown(
        label="Seleccionar ramal base",
        options=[ft.dropdown.Option(f) for f in archivos_base],
        width=300
    )

    # --- Variables auxiliares ---
    df_puntos = None
    linea_traza = None

    # --- Cargar ramal seleccionado ---
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

    # --- Procesar Excel con Tkinter ---
    def seleccionar_y_procesar_excel(e):
        nonlocal df_resultados
        if df_puntos is None:
            page.snack_bar = ft.SnackBar(ft.Text("⚠️ Primero cargá un ramal base."))
            page.snack_bar.open = True
            page.update()
            return

        # Usar Tkinter para abrir diálogo de selección
        root = Tk()
        root.withdraw()
        archivo_path = filedialog.askopenfilename(
            title="Seleccionar archivo de sospechas",
            filetypes=[("Archivos Excel", "*.xlsx")]
        )
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
            nearest_point_on_line = linea_traza.interpolate(linea_traza.project(point))
            lat_cercana = nearest_point_on_line.y
            lon_cercana = nearest_point_on_line.x
            distancia_m = point.distance(nearest_point_on_line) * 111000

            df_puntos['distancia'] = df_puntos.apply(
                lambda r: geodesic(
                    (row.latitude, row.longitude),
                    (r['latitude'], r['longitude'])
                ).km * 1000,
                axis=1
            )
            punto_cercano = df_puntos.loc[df_puntos['distancia'].idxmin()]

            resultados.append({
                'latitude_busq': row.latitude,
                'longitude_busq': row.longitude,
                'lat_cercana': lat_cercana,
                'lon_cercana': lon_cercana,
                'km_punto_cercano': punto_cercano['km'],
                'distancia_m': distancia_m
            })

            progreso.value = i / total
            status.value = f"{i} de {total} puntos procesados"
            page.update()

        df_resultados = pd.DataFrame(resultados)
        resultados_table.rows.clear()

        for r in resultados:
            resultados_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(r['latitude_busq']))),
                    ft.DataCell(ft.Text(str(r['longitude_busq']))),
                    ft.DataCell(ft.Text(str(r['lat_cercana']))),
                    ft.DataCell(ft.Text(str(r['lon_cercana']))),
                    ft.DataCell(ft.Text(str(r['km_punto_cercano']))),
                    ft.DataCell(ft.Text(f"{r['distancia_m']:,.2f}".replace('.', ',')))
                ])
            )
        page.update()

    # --- Descargar resultados ---
    def descargar_excel(e):
        if df_resultados.empty:
            return
        root = Tk()
        root.withdraw()
        ruta = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Guardar resultados"
        )
        root.destroy()
        if ruta:
            df_resultados.to_excel(ruta, index=False)
            page.snack_bar = ft.SnackBar(ft.Text(f"Archivo guardado en {ruta}"))
            page.snack_bar.open = True
            page.update()

    # --- Limpiar ---
    def limpiar_pantalla(e):
        nonlocal df_resultados
        df_resultados = pd.DataFrame()
        resultados_table.rows.clear()
        progreso.value = 0
        status.value = ""
        page.update()

    # --- Botones ---
    boton_subir = ft.ElevatedButton("Seleccionar archivo de sospechas", on_click=seleccionar_y_procesar_excel)
    boton_descargar = ft.ElevatedButton("Descargar resultados", on_click=descargar_excel)
    boton_limpiar = ft.ElevatedButton("Limpiar pantalla", on_click=limpiar_pantalla)

    # --- Layout ---
    return ft.Column(
        [
            titulo,
            ft.Row([archivo_seleccionado, boton_cargar_ramal], spacing=10),
            ft.Row([boton_subir, boton_descargar, boton_limpiar], spacing=10),
            progreso,
            status,
            ft.Divider(),
            resultados_table
        ],
        spacing=10,
        expand=True
    )

