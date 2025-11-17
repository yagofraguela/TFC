from django.urls import path
from .views import (
    CrearLugarView,
    AñadirMiembroView,
    CrearGastoView,
    EditarGastoView,
    ResumenLugarView,
    ListaGastosLugarView,
    DetalleLugarView
)

urlpatterns = [
    # --- Lugares ---
    path('lugares/crear/', CrearLugarView.as_view(), name='crear_lugar'),
    path('lugares/<int:lugar_id>/', DetalleLugarView.as_view(), name='detalle_lugar'),

    # --- Miembros ---
    path('lugares/<int:lugar_id>/miembros/añadir/', AñadirMiembroView.as_view(), name='añadir_miembro'),

    # --- Gastos ---
    path('lugares/<int:lugar_id>/gastos/', ListaGastosLugarView.as_view(), name='lista_gastos_lugar'),
    path('lugares/<int:lugar_id>/gastos/crear/', CrearGastoView.as_view(), name='crear_gasto'),
    path('gastos/<int:gasto_id>/editar/', EditarGastoView.as_view(), name='editar_gasto'),
    path('gastos/<int:gasto_id>/eliminar/', EditarGastoView.as_view(), name='eliminar_gasto'),

    # --- Resumen ---
    path('lugares/<int:lugar_id>/resumen/', ResumenLugarView.as_view(), name='resumen_lugar'),
]
