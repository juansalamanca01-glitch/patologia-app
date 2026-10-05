from datetime import date

from django.db import IntegrityError, models, transaction
from django.db.models import F
from django.conf import settings
from django.utils import timezone

from pacientes.models import edad_en_texto


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

    # Lista fija que también se ofrece en GET /api/opciones/ (docs/propuesta-informe-v2.md, 3.3).
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
    # Datos de la solicitud (informe v2, etapa 4). paciente admite null solo por los
    # informes de antes de la etapa 4; la API lo exige al crear.
    paciente = models.ForeignKey(
        'pacientes.Paciente',
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='informes',
        verbose_name='Paciente',
    )
    medico_tratante = models.CharField(max_length=200, blank=True, verbose_name='Médico tratante')
    fecha_ingreso = models.DateField(null=True, blank=True, verbose_name='Fecha de ingreso')
    # La EPS del momento del estudio, no la actual del paciente (que puede cambiar).
    eps = models.ForeignKey(
        'pacientes.EPS',
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='informes',
        verbose_name='EPS',
    )
    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='informes',
        verbose_name='Servicio',
    )
    estudios_solicitados = models.TextField(blank=True, verbose_name='Estudios solicitados')
    tipo_estudio = models.CharField(
        max_length=30,
        choices=TipoEstudio.choices,
        default=TipoEstudio.HISTOLOGIA,
        verbose_name='Tipo de estudio',
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
    descripcion_microscopica = models.TextField(blank=True, verbose_name='Descripción microscópica')
    # Antes se llamaba `notas` (P-5); la migración 0009 conserva lo que ya estaba escrito.
    comentarios = models.TextField(blank=True, verbose_name='Comentarios')
    # Los dos los llena solo `finalizar` (informe v2, etapa 6); no se escriben por la API ni en /admin/.
    fecha_informe = models.DateTimeField(null=True, blank=True, editable=False, verbose_name='Fecha de informe')
    # Paciente, EPS, servicio y firma tal como estaban al finalizar (decisión D-10).
    datos_finalizacion = models.JSONField(
        null=True, blank=True, editable=False, verbose_name='Datos congelados al finalizar',
    )
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

    @property
    def esta_finalizado(self):
        return self.estado == self.Estado.FINALIZADO

    def requisitos_faltantes(self):
        """Lo que le falta al informe para poder finalizarse (decisión D-8). Vacío si nada."""
        faltantes = []
        if self.paciente_id is None:
            faltantes.append('El informe no tiene paciente.')
        if not self.diagnosticos.exists():
            faltantes.append('El informe debe tener al menos un diagnóstico.')
        if self.tipo_estudio == self.TipoEstudio.HISTOLOGIA and not self.descripcion_microscopica.strip():
            faltantes.append('En un estudio de histología, la descripción microscópica es obligatoria.')
        # La firma es siempre la del autor, aunque finalice un admin (D-8).
        if not self.autor.registro_medico.strip():
            faltantes.append('El patólogo autor no tiene registro médico; un administrador debe registrarlo.')
        return faltantes

    def firma_actual(self):
        """Firma con los datos de hoy del autor; al finalizar se congela (D-10)."""
        return {
            'nombre': self.autor.nombre_visible,
            'especialidad': self.autor.especialidad,
            'registro_medico': self.autor.registro_medico,
        }

    def datos_para_congelar(self):
        """
        Lo que se guarda en datos_finalizacion al finalizar (decisión D-10). La edad
        no se guarda: se calcula con la fecha de nacimiento congelada y la fecha de
        ingreso, que tampoco cambia en un informe finalizado.
        """
        paciente = self.paciente
        return {
            'paciente': None if paciente is None else {
                'id': paciente.id,
                'nombre_completo': paciente.nombre_completo,
                'tipo_documento': paciente.tipo_documento,
                'numero_documento': paciente.numero_documento,
                'fecha_nacimiento': paciente.fecha_nacimiento.isoformat(),
                'sexo': paciente.sexo,
            },
            'eps_nombre': self.eps.nombre if self.eps else None,
            'servicio_nombre': self.servicio.nombre if self.servicio else None,
            'firma': self.firma_actual(),
        }

    def datos_impresos(self):
        """Los datos que muestran la API y el PDF: congelados si está finalizado (D-10), actuales si no."""
        if self.esta_finalizado and self.datos_finalizacion:
            return self.datos_finalizacion
        return self.datos_para_congelar()

    def edad_paciente(self, paciente):
        """
        Edad del paciente impreso (el diccionario de datos_impresos()) a la fecha de
        ingreso, no a hoy: así no cambia al reimprimir el informe. Los informes
        antiguos sin fecha de ingreso usan la de creación. None si no hay paciente.
        """
        if paciente is None:
            return None
        fecha = self.fecha_ingreso or timezone.localdate(self.fecha_creacion)
        return edad_en_texto(date.fromisoformat(paciente['fecha_nacimiento']), fecha)


class Diagnostico(models.Model):
    """
    Diagnóstico del informe (informe v2, etapa 5). Un informe tiene varios, en el
    orden en que se imprimen; el código CIE-10 es opcional.
    """

    informe = models.ForeignKey(
        Informe,
        on_delete=models.CASCADE,
        related_name='diagnosticos',
        verbose_name='Informe',
    )
    orden = models.PositiveSmallIntegerField(verbose_name='Orden')
    descripcion = models.TextField(verbose_name='Descripción')
    codigo_cie10 = models.CharField(max_length=7, blank=True, verbose_name='Código CIE-10')

    class Meta:
        verbose_name = 'Diagnóstico'
        verbose_name_plural = 'Diagnósticos'
        ordering = ['informe', 'orden']
        constraints = [
            models.UniqueConstraint(fields=['informe', 'orden'], name='diagnostico_orden_unico'),
        ]

    def __str__(self):
        codigo = f' ({self.codigo_cie10})' if self.codigo_cie10 else ''
        return f'{self.orden}. {self.descripcion}{codigo}'
