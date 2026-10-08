from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import Usuario


# Los formularios de Django apuntan al User de auth: se adaptan al modelo Usuario.
class UsuarioCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('username',)


class UsuarioChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """
    Usuarios en /admin/ con el UserAdmin de Django: al crear un usuario la contraseña
    se cifra, y en la ficha se ve en solo lectura y se cambia con el formulario de
    Django. Antes era un ModelAdmin común, que guardaba la contraseña tal cual y
    mostraba el hash en un campo editable (hallazgo del 2026-10-05).
    El registro médico solo lo asigna un admin (decisión D-8): aquí o con /api/auth/registro/.
    """

    form = UsuarioChangeForm
    add_form = UsuarioCreationForm
    list_display = ['username', 'nombre_completo', 'email', 'rol', 'registro_medico', 'activo', 'fecha_creacion']
    list_filter = ['rol', 'activo', 'is_staff']
    search_fields = ['username', 'nombre_completo', 'email', 'registro_medico']
    ordering = ['-fecha_creacion']
    fieldsets = UserAdmin.fieldsets + (
        (
            'Datos de PathoLab',
            {
                'fields': ('rol', 'nombre_completo', 'telefono', 'especialidad', 'registro_medico', 'activo'),
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'username',
                    'password1',
                    'password2',
                    'rol',
                    'nombre_completo',
                    'especialidad',
                    'registro_medico',
                ),
            },
        ),
    )
