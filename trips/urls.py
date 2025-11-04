from django.urls import path
from . import views
from .views import BalanceLugarView,prueba

urlpatterns = [
    path('prueba/', views.prueba),
    path('lugares/<int:lugar_id>/balance/', BalanceLugarView.as_view(), name='balance_lugar'),
]