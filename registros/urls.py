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
    path('crear_empresa/', views.crear_empresa, name='crear_empresa'),
    path('listar_empresas/', views.listar_empresas, name='listar_empresas'),
    path('listar_usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('crear_maquina/', views.crear_maquina, name='crear_maquina'),
    path('listar_maquinas/', views.listar_maquinas, name='listar_maquinas'),
    path('crear_faena/', views.crear_faena, name='crear_faena'),
     path('empresas/editar/<int:pk>/', views.editar_empresa, name='editar_empresa'),
     
    path('empresas/eliminar/<int:pk>/', views.eliminar_empresa, name='eliminar_empresa'),
    path('listar_faenas/', views.listar_faenas, name='listar_faenas'),
    path('generar_pdf_trabajo/<int:pk>/',
         views.generar_pdf_trabajo, name='generar_pdf_trabajo'),
    path('upload_logo/', views.upload_logo, name='upload_logo'),
    path('faenas/editar/<int:pk>/', views.editar_faena, name='editar_faena'),
    path('faenas/eliminar/<int:pk>/', views.eliminar_faena, name='eliminar_faena'),
    path('maquinas/editar/<int:pk>/',
         views.listar_maquinas, name='listar_maquinas'),
    path('maquinas/eliminar/<int:pk>/',
         views.eliminar_maquina, name='eliminar_maquina'),
    path('usuarios/eliminar/<int:pk>/',
         views.eliminar_usuario, name='eliminar_usuario'),
    path('guardar_cambios_usuarios/', views.guardar_cambios_usuarios,
         name='guardar_cambios_usuarios'),

]
