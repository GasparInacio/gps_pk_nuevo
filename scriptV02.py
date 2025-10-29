import flet as ft
from pages.gps_page import gps_page
from pages.datos_page import datos_page

def main(page: ft.Page):
    page.title = "GPS"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#012C33"

    # Sidebar fija
    sidebar = ft.Row([
        ft.ElevatedButton("GPS", on_click=lambda e: page.go("/")),
        ft.ElevatedButton("Carga de progresivado", on_click=lambda e: page.go("/datos")),
    ], spacing=10, alignment=ft.MainAxisAlignment.CENTER)

    sidebar_container = ft.Container(content=sidebar, width=200, bgcolor="#012C33", padding=10, expand=False, alignment=ft.alignment.center)

    # Contenedor dinámico
    content = ft.Column([], expand=True, scroll=ft.ScrollMode.AUTO)

    # Layout principal
    layout = ft.Column([sidebar_container, content], expand=True)
    page.add(layout)

    # Función de cambio de página
    def route_change(route):
        content.controls.clear()
        if page.route == "/":
            content.controls.extend(gps_page(page).controls)
        elif page.route == "/datos":
            content.controls.extend(datos_page(page).controls)
        else:
            content.controls.append(ft.Text("Página no encontrada"))
        page.update()

    page.on_route_change = route_change

    # Página inicial
    page.go("/")

ft.app(target=main)
