from rest_framework import serializers

from config.catalogos import NombreCatalogoMixin
from .models import EPS


class EPSSerializer(NombreCatalogoMixin, serializers.ModelSerializer):
    class Meta:
        model = EPS
        fields = ['id', 'nombre', 'activa']
        read_only_fields = ['id']
