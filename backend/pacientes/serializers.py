import re

from rest_framework import serializers
from django.utils import timezone

from config.catalogos import NombreCatalogoMixin
from .models import EPS, Paciente

EDAD_MAXIMA_ANIOS = 130


class EPSSerializer(NombreCatalogoMixin, serializers.ModelSerializer):
    class Meta:
        model = EPS
        fields = ['id', 'nombre', 'activa']
        read_only_fields = ['id']


def _sin_espacios_sobrantes(valor):
    return ' '.join(valor.split())


class PacienteSerializer(serializers.ModelSerializer):
    """
    Paciente (docs/propuesta-informe-v2.md, 3.1). `edad` se calcula a la fecha de
    hoy; el informe la calculará a su fecha de ingreso (etapa 4).
    """
    eps_nombre = serializers.CharField(source='eps.nombre', read_only=True, default=None)
    edad = serializers.CharField(read_only=True)

    class Meta:
        model = Paciente
        fields = [
            'id', 'tipo_documento', 'numero_documento', 'nombres', 'apellidos',
            'fecha_nacimiento', 'edad', 'sexo', 'eps', 'eps_nombre',
            'fecha_creacion', 'fecha_actualizacion',
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']
        # El documento repetido se valida en validate(), con el número ya normalizado
        # y un mensaje en español, en lugar del validador automático de DRF.
        validators = []

    def validate_numero_documento(self, valor):
        valor = re.sub(r'[\s.]', '', valor).upper()
        if not valor:
            raise serializers.ValidationError('Este campo no puede estar en blanco.')
        return valor

    def validate_nombres(self, valor):
        return _sin_espacios_sobrantes(valor)

    def validate_apellidos(self, valor):
        return _sin_espacios_sobrantes(valor)

    def validate_fecha_nacimiento(self, valor):
        hoy = timezone.localdate()
        if valor > hoy:
            raise serializers.ValidationError('La fecha de nacimiento no puede estar en el futuro.')
        anios = hoy.year - valor.year - ((hoy.month, hoy.day) < (valor.month, valor.day))
        if anios > EDAD_MAXIMA_ANIOS:
            raise serializers.ValidationError(
                f'La fecha de nacimiento no puede ser de hace más de {EDAD_MAXIMA_ANIOS} años.'
            )
        return valor

    def validate_eps(self, valor):
        # Una EPS desactivada (D-4) no se asigna, pero el paciente que ya la tenía la conserva.
        if valor is not None and not valor.activa:
            actual = self.instance.eps_id if self.instance is not None else None
            if valor.pk != actual:
                raise serializers.ValidationError('Esta EPS está desactivada.')
        return valor

    def validate(self, attrs):
        tipo = attrs.get('tipo_documento', getattr(self.instance, 'tipo_documento', None))
        numero = attrs.get('numero_documento', getattr(self.instance, 'numero_documento', None))
        repetidos = Paciente.objects.filter(tipo_documento=tipo, numero_documento=numero)
        if self.instance is not None:
            repetidos = repetidos.exclude(pk=self.instance.pk)
        if repetidos.exists():
            raise serializers.ValidationError(
                {'numero_documento': 'Ya existe un paciente con este tipo y número de documento.'}
            )
        return attrs
