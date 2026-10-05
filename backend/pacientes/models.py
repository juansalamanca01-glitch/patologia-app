from django.db import models


# Listas fijas (docs/propuesta-informe-v2.md, sección 3.3). El frontend las pide a
# GET /api/opciones/ en lugar de copiarlas. Las usará el modelo Paciente (etapa 3).
class TipoDocumento(models.TextChoices):
    CC = 'CC', 'Cédula de ciudadanía'
    TI = 'TI', 'Tarjeta de identidad'
    RC = 'RC', 'Registro civil'
    CE = 'CE', 'Cédula de extranjería'
    PA = 'PA', 'Pasaporte'
    PPT = 'PPT', 'Permiso por protección temporal'
    MS = 'MS', 'Menor sin identificación'
    AS = 'AS', 'Adulto sin identificación'


class Sexo(models.TextChoices):
    """Etiqueta "Sexo", como en el formato real del informe (P-3)."""
    FEMENINO = 'femenino', 'Femenino'
    MASCULINO = 'masculino', 'Masculino'
    INDETERMINADO = 'indeterminado', 'Indeterminado'


class EPS(models.Model):
    """Catálogo editable de EPS. Se desactiva en lugar de borrarse (decisión D-4)."""

    nombre = models.CharField(max_length=150, unique=True, verbose_name='Nombre')
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'EPS'
        verbose_name_plural = 'EPS'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre
