from django.db import IntegrityError, models, transaction
from django.db.models import F
from django.conf import settings
from django.utils import timezone


class Categoria(models.Model):
    """Categoría para agrupar tipos de patología (p. ej. Dermatopatología, Hematopatología)."""

    nombre = models.CharField(max_length=150, unique=True, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    color = models.CharField(
        max_length=7, blank=True, default='#2563eb',
        verbose_name='Color', help_text='Color hexadecimal para distinguirla en la interfaz.',
    )
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Patologia(models.Model):
    """Tipo de patología con su protocolo médico. Sus campos de formulario están en Plantilla."""

    nombre = models.CharField(max_length=200, unique=True, verbose_name='Nombre')
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='patologias',
        verbose_name='Categoría',
    )
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
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
    """Campo del formulario dinámico de una patología (texto, número, lista, etc.)."""

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


class Servicio(models.Model):
    """Servicio que remite la muestra. Catálogo editable; se desactiva en lugar de borrarse (D-4)."""

    nombre = models.CharField(max_length=150, unique=True, verbose_name='Nombre')
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class ConsecutivoPeticion(models.Model):
    """Último número de petición usado en cada año (decisión D-7)."""

    anio = models.PositiveIntegerField(primary_key=True, verbose_name='Año')
    ultimo = models.PositiveIntegerField(default=0, verbose_name='Último consecutivo')

    class Meta:
        verbose_name = 'Consecutivo de petición'
        verbose_name_plural = 'Consecutivos de petición'

    def __str__(self):
        return f'{self.anio}: {self.ultimo}'


def siguiente_numero_peticion():
    """
    Reserva el siguiente número de petición del año: P-AÑO-NNNNN (decisión D-7).
    Debe llamarse dentro de la transacción que guarda el informe. El UPDATE
    bloquea el contador (la fila en PostgreSQL, la base entera en SQLite) hasta
    el COMMIT, así que dos informes creados a la vez nunca reciben el mismo
    número. Se empieza con UPDATE y no con SELECT porque en SQLite una
    transacción que lee y luego escribe falla en lugar de esperar su turno.
    """
    anio = timezone.localdate().year
    if not ConsecutivoPeticion.objects.filter(anio=anio).update(ultimo=F('ultimo') + 1):
        try:
            with transaction.atomic():  # primer informe del año
                ConsecutivoPeticion.objects.create(anio=anio, ultimo=1)
        except IntegrityError:  # otro usuario creó el contador del año al mismo tiempo
            ConsecutivoPeticion.objects.filter(anio=anio).update(ultimo=F('ultimo') + 1)
    ultimo = ConsecutivoPeticion.objects.get(anio=anio).ultimo
    return f'P-{anio}-{ultimo:05d}'


class Informe(models.Model):
    """Informe de anatomía patológica."""

    class Estado(models.TextChoices):
        BORRADOR = 'borrador', 'Borrador'
        FINALIZADO = 'finalizado', 'Finalizado'

    # Lista fija que se ofrece en GET /api/opciones/. El campo tipo_estudio se
    # agrega en la etapa 4 del informe v2 (docs/propuesta-informe-v2.md, 3.3).
    class TipoEstudio(models.TextChoices):
        HISTOLOGIA = 'histologia', 'Histología'
        CITOLOGIA_NO_GINECOLOGICA = 'citologia_no_ginecologica', 'Citología no ginecológica'
        CITOLOGIA_CERVICOVAGINAL = 'citologia_cervicovaginal', 'Citología cérvico-vaginal'
        INMUNOHISTOQUIMICA = 'inmunohistoquimica', 'Inmunohistoquímica'
        INTRAOPERATORIO = 'intraoperatorio', 'Estudio intraoperatorio por congelación'
        REVISION_LAMINAS = 'revision_laminas', 'Revisión de láminas (segunda opinión)'

    # Lo asigna save() al crear el informe; no se puede cambiar (decisión D-7).
    numero_peticion = models.CharField(
        max_length=20, unique=True, editable=False, verbose_name='Número de petición',
    )
    numero_orden_externa = models.CharField(
        max_length=50, blank=True,
        verbose_name='Número de orden externa',
        help_text='Número de orden de la institución remitente (opcional).',
    )
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
        return f'{self.numero_peticion} — {self.patologia.nombre}'

    def save(self, *args, **kwargs):
        if self.pk is None and not self.numero_peticion:
            # El número y el informe se guardan en la misma transacción: el
            # contador queda bloqueado hasta que el informe existe.
            with transaction.atomic():
                self.numero_peticion = siguiente_numero_peticion()
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)
