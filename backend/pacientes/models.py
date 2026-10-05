from django.db import models
from django.utils import timezone


# Listas fijas (docs/propuesta-informe-v2.md, sección 3.3). El frontend las pide a
# GET /api/opciones/ en lugar de copiarlas.
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


def _plural(cantidad, singular, plural):
    return f'{cantidad} {singular if cantidad == 1 else plural}'


class Paciente(models.Model):
    """
    Paciente del informe (docs/propuesta-informe-v2.md, 3.1). Solo guarda lo que
    aparece en el informe: los datos de salud son datos sensibles (Ley 1581 de
    2012), así que no se piden dirección, teléfono ni correo. La edad no se guarda:
    se calcula con edad_en().
    """

    tipo_documento = models.CharField(max_length=3, choices=TipoDocumento.choices, verbose_name='Tipo de documento')
    # Alfanumérico: los pasaportes llevan letras. Se guarda sin espacios ni puntos y en mayúsculas.
    numero_documento = models.CharField(max_length=20, verbose_name='Número de documento')
    nombres = models.CharField(max_length=150)
    apellidos = models.CharField(max_length=150)
    fecha_nacimiento = models.DateField(verbose_name='Fecha de nacimiento')
    sexo = models.CharField(max_length=13, choices=Sexo.choices)
    # EPS actual del paciente. El informe guarda aparte la del momento del estudio (Informe.eps).
    eps = models.ForeignKey(EPS, on_delete=models.PROTECT, null=True, blank=True,
                            related_name='pacientes', verbose_name='EPS')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        ordering = ['apellidos', 'nombres', 'id']
        constraints = [
            models.UniqueConstraint(fields=['tipo_documento', 'numero_documento'], name='paciente_documento_unico'),
        ]

    def __str__(self):
        return f'{self.nombres} {self.apellidos} ({self.tipo_documento} {self.numero_documento})'

    @property
    def nombre_completo(self):
        return f'{self.nombres} {self.apellidos}'

    @property
    def documento(self):
        """Tipo y número, p. ej. "CC PRUEBA0001"."""
        return f'{self.tipo_documento} {self.numero_documento}'

    def edad_en(self, fecha):
        """
        Edad a la fecha dada, como texto: en años cumplidos; si es menor de 1 año,
        en meses; si es menor de 1 mes, en días. Devuelve None si la fecha es
        anterior al nacimiento.
        """
        nacimiento = self.fecha_nacimiento
        if fecha < nacimiento:
            return None
        # Quien nació un 29 de febrero cumple años el 1 de marzo en los años no bisiestos.
        anios = fecha.year - nacimiento.year - ((fecha.month, fecha.day) < (nacimiento.month, nacimiento.day))
        if anios >= 1:
            return _plural(anios, 'año', 'años')
        meses = (fecha.year - nacimiento.year) * 12 + fecha.month - nacimiento.month - (fecha.day < nacimiento.day)
        if meses >= 1:
            return _plural(meses, 'mes', 'meses')
        return _plural((fecha - nacimiento).days, 'día', 'días')

    @property
    def edad(self):
        """Edad a la fecha local de hoy (America/Bogota)."""
        return self.edad_en(timezone.localdate())
