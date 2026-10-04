from django.contrib import admin
from .models import Categoria, ConsecutivoPeticion, Patologia, Plantilla, Informe


class PlantillaInline(admin.TabularInline):
    model = Plantilla
    extra = 1


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activa', 'fecha_creacion']
    list_filter = ['activa']
    search_fields = ['nombre']


@admin.register(Patologia)
class PatologiaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'activa', 'fecha_creacion']
    list_filter = ['activa', 'categoria']
    search_fields = ['nombre']
    inlines = [PlantillaInline]


@admin.register(Informe)
class InformeAdmin(admin.ModelAdmin):
    list_display = ['numero_peticion', 'numero_orden_externa', 'patologia', 'autor', 'fecha', 'estado']
    list_filter = ['estado', 'patologia', 'fecha']
    search_fields = ['numero_peticion', 'numero_orden_externa', 'tipo_muestra']
    # numero_peticion no es editable (D-7): se muestra pero no se puede cambiar.
    readonly_fields = ['numero_peticion', 'texto_generado', 'fecha_creacion', 'fecha_actualizacion']


@admin.register(ConsecutivoPeticion)
class ConsecutivoPeticionAdmin(admin.ModelAdmin):
    """Solo consulta: cambiar el contador a mano podría repetir números de petición."""
    list_display = ['anio', 'ultimo']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Plantilla)
class PlantillaAdmin(admin.ModelAdmin):
    list_display = ['campo_nombre', 'patologia', 'tipo_campo', 'obligatorio', 'orden']
    list_filter = ['patologia', 'tipo_campo', 'obligatorio']
