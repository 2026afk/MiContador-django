from django.urls import path

from . import views

#-------movimiento entre paginas-------
urlpatterns = [
    path("", views.login_view, name="login"),
    path("registro/", views.registro_view, name="registro"),
    path("menu/", views.menu_inicio, name="menu_inicio"),
    path("movimientos/nuevo/", views.agregar_movimiento, name="agregar_movimiento"),
    path("logout/", views.logout_view, name="logout"),
]