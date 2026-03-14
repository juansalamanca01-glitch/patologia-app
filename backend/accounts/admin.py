from django.contrib import admin
from django.contrib.auth import get_user_model

Usuario = get_user_model()


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ['username', 'nombre_completo', 'email', 'rol', 'activo', 'fecha_creacion']
    list_filter = ['rol', 'activo']
    search_fields = ['username', 'nombre_completo', 'email']
