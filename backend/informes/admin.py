from django.contrib import admin
from .models import Categoria, ConsecutivoPeticion, Diagnostico, Patologia, Plantilla, Informe, Servicio


class PlantillaInline(admin.TabularInline):
    model = Plantilla
    extra = 1


class DiagnosticoInline(admin.TabularInline):
    model = Diagnostico
    extra = 0


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


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre']


@admin.register(Informe)
class InformeAdmin(admin.ModelAdmin):
    list_display = ['numero_peticion', 'paciente', 'tipo_estudio', 'patologia', 'autor', 'fecha', 'estado']
    list_filter = ['estado', 'tipo_estudio', 'patologia', 'fecha']
    search_fields = [
        'numero_peticion', 'numero_orden_externa', 'tipo_muestra',
        'paciente__numero_documento', 'paciente__nombres', 'paciente__apellidos',
    ]
    list_select_related = ['paciente', 'patologia', 'autor']
    # Listas con búsqueda en lugar de un menú con todos los pacientes.
    autocomplete_fields = ['paciente']
    # numero_peticion (D-7), fecha_informe y datos_finalizacion (D-10) no son editables:
    # se muestran pero no se pueden cambiar.
    readonly_fields = [
        'numero_peticion', 'texto_generado', 'fecha_informe', 'datos_finalizacion',
        'fecha_creacion', 'fecha_actualizacion',
    ]
    inlines = [DiagnosticoInline]


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
