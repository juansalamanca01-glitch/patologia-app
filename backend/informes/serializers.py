import re

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from config.catalogos import NombreCatalogoMixin
from .models import Adenda, Categoria, Diagnostico, Patologia, Plantilla, Informe, Servicio

MAX_DIAGNOSTICOS = 20
# Letra, dos cifras y, opcionalmente, un punto con uno o dos caracteres: C44, C44.3, M80.90.
PATRON_CIE10 = re.compile(r'^[A-Z][0-9]{2}(\.[0-9A-Z]{1,2})?$')


def esta_vacio(valor):
    """
    Indica si un campo del formulario quedó sin responder. 0 y False son
    respuestas válidas (por ejemplo, "0 ganglios" o "No").
    """
    if valor is None:
        return True
    if isinstance(valor, str):
        return not valor.strip()
    if isinstance(valor, (list, dict)):
        return len(valor) == 0
    return False


class CategoriaSerializer(serializers.ModelSerializer):
    total_patologias = serializers.SerializerMethodField()

    class Meta:
        model = Categoria
        fields = [
            'id',
            'nombre',
            'descripcion',
            'color',
            'activa',
            'total_patologias',
            'fecha_creacion',
        ]
        read_only_fields = ['id', 'fecha_creacion']

    def get_total_patologias(self, obj):
        # En el listado viene contado en la misma consulta (annotate, auditoría M-4);
        # al crear o editar una sola categoría se cuenta aparte.
        anotado = getattr(obj, 'num_patologias', None)
        return anotado if anotado is not None else obj.patologias.count()


class PlantillaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plantilla
        fields = [
            'id',
            'patologia',
            'campo_nombre',
            'campo_label',
            'tipo_campo',
            'obligatorio',
            'opciones',
            'orden',
            'valor_defecto',
        ]
        read_only_fields = ['id']


class PatologiaSerializer(serializers.ModelSerializer):
    plantillas = PlantillaSerializer(many=True, read_only=True)
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True, default=None)

    class Meta:
        model = Patologia
        fields = [
            'id',
            'nombre',
            'categoria',
            'categoria_nombre',
            'descripcion',
            'protocolo_medico',
            'activa',
            'plantillas',
            'fecha_creacion',
            'fecha_actualizacion',
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']


class PatologiaListSerializer(serializers.ModelSerializer):
    """Versión resumida para listas y menús desplegables."""

    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True, default=None)

    class Meta:
        model = Patologia
        fields = ['id', 'nombre', 'categoria', 'categoria_nombre', 'activa']


class ServicioSerializer(NombreCatalogoMixin, serializers.ModelSerializer):
    class Meta:
        model = Servicio
        fields = ['id', 'nombre', 'activo']
        read_only_fields = ['id']


def _rechazar_si_desactivado(valor, actual_id, mensaje):
    """
    Un elemento de catálogo desactivado (D-4) no se asigna, pero el informe que ya
    lo tenía lo conserva, para poder corregir sus otros datos.
    """
    activo = getattr(valor, 'activa', getattr(valor, 'activo', True))
    if valor is not None and not activo and valor.pk != actual_id:
        raise serializers.ValidationError(mensaje)
    return valor


class DiagnosticoSerializer(serializers.ModelSerializer):
    """Un diagnóstico dentro del informe. El orden es el de la lista que se envía."""

    class Meta:
        model = Diagnostico
        fields = ['orden', 'descripcion', 'codigo_cie10']
        read_only_fields = ['orden']
        extra_kwargs = {
            'descripcion': {'error_messages': {'blank': 'Escriba la descripción del diagnóstico.'}},
        }

    def validate_codigo_cie10(self, valor):
        """Mayúsculas, sin espacios y con el punto que falte: "c443" se guarda como "C44.3"."""
        codigo = re.sub(r'\s', '', valor or '').upper()
        if not codigo:
            return ''
        if '.' not in codigo and len(codigo) > 3:
            codigo = f'{codigo[:3]}.{codigo[3:]}'
        if not PATRON_CIE10.match(codigo):
            raise serializers.ValidationError(
                'Código CIE-10 no válido. Use una letra, dos cifras y, si aplica, la subcategoría (ej.: C44.3).'
            )
        return codigo


class AdendaSerializer(serializers.ModelSerializer):
    """
    Adenda de un informe finalizado (decisión D-9). Solo se escriben el motivo y el
    texto: el número, el autor y la firma los pone la acción `adendas` de InformeViewSet.
    """

    class Meta:
        model = Adenda
        fields = ['id', 'numero', 'motivo', 'texto', 'autor', 'fecha', 'firma']
        read_only_fields = ['id', 'numero', 'autor', 'fecha', 'firma']


class InformeSerializer(serializers.ModelSerializer):
    patologia_nombre = serializers.CharField(source='patologia.nombre', read_only=True)
    autor_nombre = serializers.CharField(source='autor.nombre_visible', read_only=True)
    # `paciente` es el id (para escribirlo); `paciente_datos`, lo que muestra el informe.
    # En un informe finalizado, estos cuatro salen de los datos congelados (decisión D-10).
    paciente_datos = serializers.SerializerMethodField()
    eps_nombre = serializers.SerializerMethodField()
    servicio_nombre = serializers.SerializerMethodField()
    firma = serializers.SerializerMethodField()
    # Si se envía, reemplaza la lista anterior; si no se envía (p. ej. un PATCH), no cambia.
    diagnosticos = DiagnosticoSerializer(many=True, required=False)
    # Se agregan con POST /api/informes/{id}/adendas/; aquí solo se leen (D-9).
    adendas = AdendaSerializer(many=True, read_only=True)

    class Meta:
        model = Informe
        fields = [
            'id',
            'numero_peticion',
            'numero_orden_externa',
            'paciente',
            'paciente_datos',
            'medico_tratante',
            'fecha_ingreso',
            'eps',
            'eps_nombre',
            'servicio',
            'servicio_nombre',
            'estudios_solicitados',
            'tipo_estudio',
            'patologia',
            'patologia_nombre',
            'autor',
            'autor_nombre',
            'fecha',
            'tipo_muestra',
            'datos_ingresados',
            'texto_generado',
            'descripcion_microscopica',
            'diagnosticos',
            'comentarios',
            'estado',
            'fecha_informe',
            'firma',
            'adendas',
            'fecha_creacion',
            'fecha_actualizacion',
        ]
        # numero_peticion lo asigna el sistema y no se puede cambiar (decisión D-7).
        read_only_fields = [
            'id',
            'numero_peticion',
            'autor',
            'texto_generado',
            'fecha',
            'fecha_creacion',
            'fecha_actualizacion',
        ]

    def get_paciente_datos(self, informe):
        paciente = informe.datos_impresos()['paciente']
        if paciente is None:  # informe de antes de la etapa 4
            return None
        return {**paciente, 'edad': informe.edad_paciente(paciente)}

    def get_eps_nombre(self, informe):
        return informe.datos_impresos()['eps_nombre']

    def get_servicio_nombre(self, informe):
        return informe.datos_impresos()['servicio_nombre']

    def get_firma(self, informe):
        return informe.datos_impresos()['firma']

    def validate_fecha_ingreso(self, valor):
        if valor is not None and valor > timezone.localdate():
            raise serializers.ValidationError('La fecha de ingreso no puede estar en el futuro.')
        return valor

    def validate_eps(self, valor):
        return _rechazar_si_desactivado(valor, getattr(self.instance, 'eps_id', None), 'Esta EPS está desactivada.')

    def validate_servicio(self, valor):
        return _rechazar_si_desactivado(
            valor,
            getattr(self.instance, 'servicio_id', None),
            'Este servicio está desactivado.',
        )

    def validate_diagnosticos(self, valor):
        if len(valor) > MAX_DIAGNOSTICOS:
            raise serializers.ValidationError(f'Un informe admite como máximo {MAX_DIAGNOSTICOS} diagnósticos.')
        return valor

    def validate(self, data):
        self._validar_paciente_y_fecha_ingreso(data)
        self._validar_campos_obligatorios(data)
        return data

    # El informe y sus diagnósticos se guardan juntos: si algo falla, no queda ninguno a medias.
    def create(self, validated_data):
        diagnosticos = validated_data.pop('diagnosticos', [])
        with transaction.atomic():
            informe = super().create(validated_data)
            self._guardar_diagnosticos(informe, diagnosticos)
        return informe

    def update(self, instance, validated_data):
        diagnosticos = validated_data.pop('diagnosticos', None)
        with transaction.atomic():
            informe = super().update(instance, validated_data)
            if diagnosticos is not None:
                self._guardar_diagnosticos(informe, diagnosticos)
        return informe

    def _guardar_diagnosticos(self, informe, diagnosticos):
        """Reemplaza los diagnósticos del informe; el orden es el de la lista (1, 2, 3...)."""
        informe.diagnosticos.all().delete()
        Diagnostico.objects.bulk_create(
            Diagnostico(informe=informe, orden=orden, **datos) for orden, datos in enumerate(diagnosticos, start=1)
        )

    def _validar_paciente_y_fecha_ingreso(self, data):
        creando = self.instance is None
        paciente = data['paciente'] if 'paciente' in data else getattr(self.instance, 'paciente', None)
        # Obligatorio al crear. Un informe antiguo sin paciente se puede seguir editando,
        # pero a un informe que ya tiene paciente no se le puede quitar.
        if paciente is None and (creando or 'paciente' in data):
            raise serializers.ValidationError({'paciente': 'Seleccione un paciente.'})

        if creando:
            if not data.get('fecha_ingreso'):
                data['fecha_ingreso'] = timezone.localdate()
            # Si no se envía la EPS, se usa la actual del paciente, siempre que siga activa.
            if 'eps' not in self.initial_data and paciente.eps is not None and paciente.eps.activa:
                data['eps'] = paciente.eps

        fecha = data['fecha_ingreso'] if 'fecha_ingreso' in data else getattr(self.instance, 'fecha_ingreso', None)
        if paciente is not None and fecha is not None and fecha < paciente.fecha_nacimiento:
            raise serializers.ValidationError(
                {'fecha_ingreso': 'La fecha de ingreso no puede ser anterior a la fecha de nacimiento del paciente.'}
            )

    def _validar_campos_obligatorios(self, data):
        """Comprueba que estén llenos los campos obligatorios de la plantilla de la patología."""
        patologia = data.get('patologia') or (self.instance and self.instance.patologia)
        # Si la petición no trae datos_ingresados (p. ej. un PATCH que solo cambia las
        # comentarios), se validan los datos ya guardados del informe.
        if 'datos_ingresados' in data:
            datos = data['datos_ingresados'] or {}
        else:
            datos = self.instance.datos_ingresados if self.instance else {}

        # Antes era "if patologia and datos": con datos vacíos no se validaba nada (auditoría I-2).
        if patologia:
            faltantes = [
                campo.campo_label or campo.campo_nombre
                for campo in patologia.plantillas.filter(obligatorio=True)
                if esta_vacio(datos.get(campo.campo_nombre))
            ]
            if faltantes:
                raise serializers.ValidationError(
                    {'datos_ingresados': f'Faltan campos obligatorios: {", ".join(faltantes)}'}
                )


class InformeListSerializer(serializers.ModelSerializer):
    """Versión resumida para el listado de informes."""

    patologia_nombre = serializers.CharField(source='patologia.nombre', read_only=True)
    autor_nombre = serializers.CharField(source='autor.nombre_visible', read_only=True)
    # None en los informes de antes de la etapa 4, que no tienen paciente.
    paciente_nombre = serializers.CharField(source='paciente.nombre_completo', read_only=True, default=None)
    paciente_documento = serializers.CharField(source='paciente.documento', read_only=True, default=None)

    class Meta:
        model = Informe
        fields = [
            'id',
            'numero_peticion',
            'numero_orden_externa',
            'paciente',
            'paciente_nombre',
            'paciente_documento',
            'tipo_estudio',
            'patologia_nombre',
            'autor',
            'autor_nombre',
            'fecha',
            'tipo_muestra',
            'estado',
            'fecha_creacion',
        ]
