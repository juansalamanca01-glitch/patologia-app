from django.db import models
from django.conf import settings


class Patologia(models.Model):
    """Pathology type with its required fields and medical protocol."""

    nombre = models.CharField(max_length=200, unique=True, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    campos_requeridos = models.JSONField(
        default=list,
        verbose_name='Campos requeridos',
        help_text='Lista JSON de los campos requeridos para esta patología.',
    )
    protocolo_medico = models.TextField(
        blank=True,
        verbose_name='Protocolo médico',
        help_text='Protocolo médico asociado a esta patología.',
    )
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Patología'
        verbose_name_plural = 'Patologías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Plantilla(models.Model):
    """Dynamic form field template linked to a pathology type."""

    class TipoCampo(models.TextChoices):
        TEXTO = 'texto', 'Texto'
        NUMERO = 'numero', 'Número'
        LISTA = 'lista', 'Lista desplegable'
        TEXTAREA = 'textarea', 'Área de texto'
        BOOLEAN = 'boolean', 'Sí / No'

    patologia = models.ForeignKey(
        Patologia,
        on_delete=models.CASCADE,
        related_name='plantillas',
        verbose_name='Patología',
    )
    campo_nombre = models.CharField(max_length=150, verbose_name='Nombre del campo')
    campo_label = models.CharField(max_length=200, blank=True, verbose_name='Etiqueta visible')
    tipo_campo = models.CharField(
        max_length=20,
        choices=TipoCampo.choices,
        default=TipoCampo.TEXTO,
        verbose_name='Tipo de campo',
    )
    obligatorio = models.BooleanField(default=False, verbose_name='Obligatorio')
    opciones = models.JSONField(
        default=list, blank=True,
        verbose_name='Opciones',
        help_text='Lista de opciones para campos de tipo lista.',
    )
    orden = models.PositiveIntegerField(default=0, verbose_name='Orden')
    valor_defecto = models.CharField(max_length=255, blank=True, verbose_name='Valor por defecto')

    class Meta:
        verbose_name = 'Plantilla'
        verbose_name_plural = 'Plantillas'
        ordering = ['patologia', 'orden']
        unique_together = ['patologia', 'campo_nombre']

    def __str__(self):
        return f'{self.patologia.nombre} → {self.campo_label or self.campo_nombre}'


class Informe(models.Model):
    """Clinical pathology report."""

    class Estado(models.TextChoices):
        BORRADOR = 'borrador', 'Borrador'
        FINALIZADO = 'finalizado', 'Finalizado'

    numero_caso = models.CharField(max_length=50, unique=True, verbose_name='Número de caso')
    patologia = models.ForeignKey(
        Patologia,
        on_delete=models.PROTECT,
        related_name='informes',
        verbose_name='Patología',
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='informes',
        verbose_name='Autor',
    )
    fecha = models.DateField(auto_now_add=True, verbose_name='Fecha')
    tipo_muestra = models.CharField(max_length=200, blank=True, verbose_name='Tipo de muestra')
    datos_ingresados = models.JSONField(
        default=dict,
        verbose_name='Datos ingresados',
        help_text='JSON con los valores del formulario dinámico.',
    )
    texto_generado = models.TextField(
        blank=True,
        verbose_name='Texto generado',
        help_text='Descripción macroscópica generada automáticamente.',
    )
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.BORRADOR,
        verbose_name='Estado',
    )
    notas = models.TextField(blank=True, verbose_name='Notas adicionales')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Informe'
        verbose_name_plural = 'Informes'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'Caso {self.numero_caso} — {self.patologia.nombre}'
