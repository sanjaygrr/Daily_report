from django.urls import path
from . import views

urlpatterns = [
    path('crear/', views.crear_trabajo, name='crear_trabajo'),
    path('home/', views.home, name='home'),
    path('historial/', views.historial, name='historial'),
    path('pendientes/', views.pendientes, name='pendientes'),
    path('aprobar/<int:pk>/', views.aprobar_trabajo, name='aprobar_trabajo'),
    path('export_historial_xlsx/', views.export_historial_xlsx,
         name='export_historial_xlsx'),
]
