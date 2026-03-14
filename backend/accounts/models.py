from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """Custom user model with role-based access."""

    class Rol(models.TextChoices):
        ADMIN = 'admin', 'Administrador'
        PATOLOGO = 'patologo', 'Patólogo'
        AUDITOR = 'auditor', 'Auditor'

    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.PATOLOGO,
        verbose_name='Rol',
    )
    nombre_completo = models.CharField(max_length=255, blank=True, verbose_name='Nombre completo')
    telefono = models.CharField(max_length=20, blank=True, verbose_name='Teléfono')
    especialidad = models.CharField(max_length=100, blank=True, verbose_name='Especialidad')
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'{self.nombre_completo or self.username} ({self.get_rol_display()})'

    @property
    def es_admin(self):
        return self.rol == self.Rol.ADMIN

    @property
    def es_patologo(self):
        return self.rol == self.Rol.PATOLOGO

    @property
    def es_auditor(self):
        return self.rol == self.Rol.AUDITOR
