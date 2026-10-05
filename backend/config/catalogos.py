"""
Piezas comunes de los catálogos editables (EPS y servicios, informe v2 etapa 2).
Se desactivan en lugar de borrarse (decisión D-4) y los administran patólogos y
admin (D-11).
"""
from rest_framework import serializers


class NombreCatalogoMixin:
    """
    Serializer con un campo `nombre` único sin importar mayúsculas ni espacios:
    "Sura" y " SURA " cuentan como el mismo nombre. Guarda el nombre sin espacios
    sobrantes.
    """

    def validate_nombre(self, valor):
        valor = ' '.join(valor.split())
        repetidos = self.Meta.model.objects.filter(nombre__iexact=valor)
        if self.instance is not None:
            repetidos = repetidos.exclude(pk=self.instance.pk)
        if repetidos.exists():
            raise serializers.ValidationError('Ya existe un elemento con este nombre.')
        return valor


def filtrar_por_activo(queryset, request, campo):
    """Aplica ?<campo>=true / ?<campo>=false; sin el parámetro devuelve todo."""
    valor = request.query_params.get(campo)
    if valor in ('true', 'false'):
        queryset = queryset.filter(**{campo: valor == 'true'})
    return queryset
