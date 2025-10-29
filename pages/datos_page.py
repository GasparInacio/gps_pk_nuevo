import flet as ft
import os
import shutil

def datos_page(page: ft.Page):
    # Crear carpeta "data" si no existe
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)

    subir_progresivado = ft.FilePicker()
    status = ft.Text("")
    nombre_archivo_input = ft.TextField(label="Nombre del archivo (opcional)", width=300)

    # --- Función para manejar archivos seleccionados ---
    def on_file_picked(e: ft.FilePickerResultEvent):
        if not e.files:
            status.value = "No se seleccionó ningún archivo."
            page.update()
            return

        for file in e.files:
            origen = file.path

            # Si el usuario escribió un nombre, se usa ese; si no, el original
            nombre_personalizado = nombre_archivo_input.value.strip()
            if nombre_personalizado:
                # Agregamos extensión según el archivo original
                ext = os.path.splitext(file.name)[1]
                destino = os.path.join(data_dir, f"{nombre_personalizado}{ext}")
            else:
                destino = os.path.join(data_dir, os.path.basename(file.name))

            try:
                shutil.copy(origen, destino)
                status.value = f"Archivo guardado como: {os.path.basename(destino)}"
            except Exception as err:
                status.value = f"Error al copiar archivo: {err}"

        page.update()

    subir_progresivado.on_result = on_file_picked

    # --- Botón para abrir el selector de archivos ---
    boton_subir = ft.ElevatedButton(
        "Seleccionar archivo(s) de progresivado",
        on_click=lambda _: subir_progresivado.pick_files(
            allow_multiple=True,
            allowed_extensions=["csv", "xlsx"],
        ),
    )

    # Agregamos el FilePicker al overlay de la página
    page.overlay.append(subir_progresivado)

    # --- Layout principal ---
    return ft.Column(
        [
            ft.Text("Carga de progresivado", size=24, weight=ft.FontWeight.BOLD),
            nombre_archivo_input,
            boton_subir,
            status,
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )



