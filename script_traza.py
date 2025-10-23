import flet as ft
import pandas as pd
from shapely.geometry import LineString, Point
from geopy.distance import geodesic
import os
import sys
from tkinter import Tk, filedialog

# Función para obtener la ruta de recursos correctamente
def resource_path(relative_path):
    try:
        # Cuando se ejecuta como exe con PyInstaller
        base_path = sys._MEIPASS
    except AttributeError:
        # Cuando se ejecuta en Python normal
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def main(page: ft.Page):
    page.theme_mode = ft.ThemeMode.DARK
    page.title = "GPS - PK"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.scroll = ft.ScrollMode.AUTO

    # --- Componentes de UI ---
    titulo = ft.Text("GPS - PK", size=24, weight=ft.FontWeight.BOLD)
    subir_excel = ft.FilePicker()
    resultados_table = ft.DataTable(columns=[
        ft.DataColumn(ft.Text("Latitude")),
        ft.DataColumn(ft.Text("Longitude")),
        ft.DataColumn(ft.Text("Lat Cercana")),
        ft.DataColumn(ft.Text("Lon Cercana")),
        ft.DataColumn(ft.Text("KM Cercano")),
        ft.DataColumn(ft.Text("Distancia (m)")),
    ])
    progreso = ft.ProgressBar(width=400)
    status = ft.Text("")

    # --- Agregar FilePicker al overlay ---
    page.overlay.append(subir_excel)

    # --- Cargar datos base ---
    puntos_file = resource_path("data/sarmiento.csv")
    df_puntos = pd.read_csv(puntos_file)
    df_puntos.columns = df_puntos.columns.str.strip().str.lower()
    df_puntos = df_puntos.dropna(subset=['latitude', 'longitude', 'km'])
    linea_traza = LineString(df_puntos[['longitude', 'latitude']].values)

    df_resultados = pd.DataFrame()  # guardaremos resultados para descargar

    # --- Función de cálculo ---
    def procesar_archivo(e: ft.FilePickerResultEvent):
        nonlocal df_resultados
        if not e.files:
            return
        archivo_path = e.files[0].path
        sospechas_df = pd.read_excel(archivo_path)
        sospechas_df.columns = sospechas_df.columns.str.strip().str.lower()
        sospechas_df = sospechas_df.dropna(subset=['latitude', 'longitude'])

        resultados = []
        total = len(sospechas_df)

        for i, row in enumerate(sospechas_df.itertuples(), start=1):
            point = Point(row.longitude, row.latitude)

            # Punto más cercano en la línea
            nearest_point_on_line = linea_traza.interpolate(linea_traza.project(point))
            lat_cercana = nearest_point_on_line.y
            lon_cercana = nearest_point_on_line.x

            # Distancia mínima a la línea (m)
            distancia_deg = point.distance(nearest_point_on_line)
            distancia_m = distancia_deg * 111000

            # Encontrar punto CSV más cercano
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
                'distancia_m': distancia_m
            })

            progreso.value = i / total
            status.value = f"{i} de {total} puntos procesados"
            page.update()

        # Guardar resultados en DataFrame para descargar
        df_resultados = pd.DataFrame(resultados)

        # Mostrar resultados en la tabla
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

    # --- Función para descargar Excel usando Tkinter ---
    def descargar_excel(e):
        if df_resultados.empty:
            return
        # Abrir diálogo de guardar archivo
        root = Tk()
        root.withdraw()  # no mostrar ventana principal
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

    # --- Función para limpiar pantalla ---
    def limpiar_pantalla(e):
        nonlocal df_resultados
        df_resultados = pd.DataFrame()
        resultados_table.rows.clear()
        progreso.value = 0
        status.value = ""
        page.update()

    # --- Botones ---
    boton_subir = ft.ElevatedButton(
        "Seleccionar archivo Excel",
        on_click=lambda _: subir_excel.pick_files(
            allowed_extensions=["xlsx"],
            allow_multiple=False
        ),
    )
    subir_excel.on_result = procesar_archivo

    boton_descargar = ft.ElevatedButton(
        "Descargar resultados en Excel",
        on_click=descargar_excel
    )

    boton_limpiar = ft.ElevatedButton(
        "Limpiar pantalla",
        on_click=limpiar_pantalla
    )

    # --- Layout principal ---
    page.add(
        titulo,
        boton_subir,
        boton_descargar,
        boton_limpiar,
        progreso,
        status,
        ft.Divider(),
        resultados_table
    )

ft.app(target=main)



