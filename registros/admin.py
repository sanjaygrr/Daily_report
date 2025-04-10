from django.contrib import admin
from import_export.admin import ExportMixin
from .models import Trabajo, Maquina, Faena, Empresa, PerfilUsuario
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin
from django.db import models

class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Perfil de Usuario'

class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'administrador', 'activa')
    list_filter = ('activa',)
    search_fields = ('nombre', 'rut', 'administrador__username')
    raw_id_fields = ('administrador',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(administrador=request.user)

class MaquinaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'modelo', 'empresa', 'estado', 'activa')
    list_filter = ('empresa', 'estado', 'activa')
    search_fields = ('nombre', 'modelo', 'numero_serie')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(empresa__administrador=request.user)

class FaenaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ubicacion', 'empresa', 'estado', 'activa')
    list_filter = ('empresa', 'estado', 'activa')
    search_fields = ('nombre', 'ubicacion')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(empresa__administrador=request.user)

class TrabajoAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('fecha', 'faena', 'maquina', 'trabajo', 'supervisor', 'trabajador', 'estado', 'empresa')
    list_filter = ('empresa', 'faena', 'maquina', 'estado')
    search_fields = ('trabajo', 'observaciones')
    date_hierarchy = 'fecha'
    readonly_fields = ('total_horas', 'fecha_creacion', 'fecha_actualizacion')
    fieldsets = (
        (None, {
            'fields': ('faena', 'maquina', 'fecha', 'trabajo')
        }),
        ('Mediciones', {
            'fields': ('horometro_inicial', 'horometro_final', 'total_horas', 'tipo_medida')
        }),
        ('Insumos', {
            'fields': ('petroleo_litros', 'aceite_tipo', 'aceite_litros')
        }),
        ('Personal', {
            'fields': ('supervisor', 'trabajador')
        }),
        ('Estado', {
            'fields': ('estado', 'observaciones')
        }),
        ('Auditoría', {
            'fields': ('creado_por', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(empresa__administrador=request.user)
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'empresa_display', 'is_staff')
    list_filter = ('groups', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    inlines = [PerfilUsuarioInline]  # Añadir el inline de PerfilUsuario
    
    def empresa_display(self, obj):
        if hasattr(obj, 'perfil') and obj.perfil.empresa:
            return obj.perfil.empresa.nombre
        elif obj.empresas_administradas.exists():
            return ", ".join([e.nombre for e in obj.empresas_administradas.all()])
        return "-"
    empresa_display.short_description = 'Empresa'
    
    # Eliminamos el fieldset adicional que causaba el error
    # El campo empresa ahora se muestra a través del inline PerfilUsuarioInline
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(models.Q(perfil__empresa__administrador=request.user) | 
                     models.Q(empresas_administradas__administrador=request.user)).distinct()

# Registros
admin.site.register(Empresa, EmpresaAdmin)
admin.site.register(Maquina, MaquinaAdmin)
admin.site.register(Faena, FaenaAdmin)
admin.site.register(Trabajo, TrabajoAdmin)

# Desregistrar el UserAdmin por defecto y registrar el nuestro
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)