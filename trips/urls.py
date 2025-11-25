from django.urls import path
from .views import (
    ListaLugaresHTMLView, DetalleLugarView, CrearLugarView,
     DashboardView,CrearGastoFormView,AnadirParticipanteView
)

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),

    # Lugares
    path("lugares/", ListaLugaresHTMLView.as_view(), name="lista_lugares"),
    path("lugares/crear/", CrearLugarView.as_view(), name="crear_lugar"),
    path("lugares/<int:lugar_id>/", DetalleLugarView.as_view(), name="detalle_lugar"),

    # Gastos
    path("lugares/<int:lugar_id>/gastos/crear/", CrearGastoFormView.as_view(), name="crear_gasto"),

    path('lugares/<int:pk>/anadir-participante/', AnadirParticipanteView.as_view(), name='anadir_participante'),

]


