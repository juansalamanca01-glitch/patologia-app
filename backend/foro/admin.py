from django.contrib import admin

from .models import Comentario, ImagenPublicacion, Publicacion, TemaForo


class ImagenInline(admin.TabularInline):
    model = ImagenPublicacion
    extra = 0


class ComentarioInline(admin.TabularInline):
    model = Comentario
    extra = 0
    readonly_fields = ['autor', 'contenido', 'fecha_creacion']
    can_delete = True


@admin.register(TemaForo)
class TemaForoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activo', 'fecha_creacion']
    list_filter = ['activo']
    search_fields = ['nombre']


@admin.register(Publicacion)
class PublicacionAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'autor', 'tema', 'fijado', 'fecha_creacion']
    list_filter = ['tema', 'fijado']
    search_fields = ['titulo', 'contenido']
    inlines = [ImagenInline, ComentarioInline]
