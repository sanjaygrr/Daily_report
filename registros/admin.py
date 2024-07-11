# admin.py
from django.contrib import admin
from import_export.admin import ExportMixin
from .models import Trabajo


class TrabajoAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ['fecha', 'faena', 'maquina',
                    'trabajo', 'supervisor', 'trabajador', 'aprobado']


admin.site.register(Trabajo, TrabajoAdmin)
