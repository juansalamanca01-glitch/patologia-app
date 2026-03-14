from django.contrib import admin
from .models import Patologia, Plantilla, Informe


class PlantillaInline(admin.TabularInline):
    model = Plantilla
    extra = 1


@admin.register(Patologia)
class PatologiaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activa', 'fecha_creacion']
    list_filter = ['activa']
    search_fields = ['nombre']
    inlines = [PlantillaInline]


@admin.register(Informe)
class InformeAdmin(admin.ModelAdmin):
    list_display = ['numero_caso', 'patologia', 'autor', 'fecha', 'estado']
    list_filter = ['estado', 'patologia', 'fecha']
    search_fields = ['numero_caso', 'tipo_muestra']
    readonly_fields = ['texto_generado', 'fecha_creacion', 'fecha_actualizacion']


@admin.register(Plantilla)
class PlantillaAdmin(admin.ModelAdmin):
    list_display = ['campo_nombre', 'patologia', 'tipo_campo', 'obligatorio', 'orden']
    list_filter = ['patologia', 'tipo_campo', 'obligatorio']
