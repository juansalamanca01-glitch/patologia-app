from django.contrib import admin

from .models import EPS, Paciente


@admin.register(EPS)
class EPSAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activa']
    list_filter = ['activa']
    search_fields = ['nombre']


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ['apellidos', 'nombres', 'tipo_documento', 'numero_documento', 'sexo', 'eps']
    list_filter = ['sexo', 'tipo_documento']
    search_fields = ['numero_documento', 'nombres', 'apellidos']
    list_select_related = ['eps']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
