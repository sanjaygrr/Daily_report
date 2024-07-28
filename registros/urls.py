from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('crear/', views.crear_trabajo, name='crear_trabajo'),
    path('historial/', views.historial, name='historial'),
    path('pendientes/', views.pendientes, name='pendientes'),
    path('aprobar/<int:pk>/', views.aprobar_trabajo, name='aprobar_trabajo'),
    path('export_historial_xlsx/', views.export_historial_xlsx,
         name='export_historial_xlsx'),
    path('register_user/', views.register_user, name='register_user'),
    path('listar_usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('crear_maquina/', views.crear_maquina, name='crear_maquina'),
    path('listar_maquinas/', views.listar_maquinas, name='listar_maquinas'),
    path('crear_faena/', views.crear_faena, name='crear_faena'),
    path('listar_faenas/', views.listar_faenas, name='listar_faenas'),
    path('generar_pdf_trabajo/<int:pk>/',
         views.generar_pdf_trabajo, name='generar_pdf_trabajo'),
    path('upload_logo/', views.upload_logo, name='upload_logo'),
]
