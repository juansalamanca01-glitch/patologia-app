from rest_framework import serializers
from .models import Patologia, Plantilla, Informe


class PlantillaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plantilla
        fields = [
            'id', 'patologia', 'campo_nombre', 'campo_label',
            'tipo_campo', 'obligatorio', 'opciones', 'orden', 'valor_defecto',
        ]
        read_only_fields = ['id']


class PatologiaSerializer(serializers.ModelSerializer):
    plantillas = PlantillaSerializer(many=True, read_only=True)

    class Meta:
        model = Patologia
        fields = [
            'id', 'nombre', 'descripcion', 'campos_requeridos',
            'protocolo_medico', 'activa', 'plantillas',
            'fecha_creacion', 'fecha_actualizacion',
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']


class PatologiaListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for dropdowns."""
    class Meta:
        model = Patologia
        fields = ['id', 'nombre', 'activa']


class InformeSerializer(serializers.ModelSerializer):
    patologia_nombre = serializers.CharField(source='patologia.nombre', read_only=True)
    autor_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Informe
        fields = [
            'id', 'numero_caso', 'patologia', 'patologia_nombre',
            'autor', 'autor_nombre', 'fecha', 'tipo_muestra',
            'datos_ingresados', 'texto_generado', 'estado', 'notas',
            'fecha_creacion', 'fecha_actualizacion',
        ]
        read_only_fields = ['id', 'autor', 'texto_generado', 'fecha', 'fecha_creacion', 'fecha_actualizacion']

    def get_autor_nombre(self, obj):
        return obj.autor.nombre_completo or obj.autor.username

    def validate(self, data):
        """Validate required fields defined in the Plantilla for this pathology."""
        patologia = data.get('patologia') or (self.instance and self.instance.patologia)
        datos = data.get('datos_ingresados', {})

        if patologia and datos:
            campos_obligatorios = patologia.plantillas.filter(obligatorio=True)
            faltantes = []
            for campo in campos_obligatorios:
                valor = datos.get(campo.campo_nombre)
                if not valor or (isinstance(valor, str) and not valor.strip()):
                    faltantes.append(campo.campo_label or campo.campo_nombre)
            if faltantes:
                raise serializers.ValidationError({
                    'datos_ingresados': f'Faltan campos obligatorios: {", ".join(faltantes)}'
                })

        return data


class InformeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    patologia_nombre = serializers.CharField(source='patologia.nombre', read_only=True)
    autor_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Informe
        fields = [
            'id', 'numero_caso', 'patologia_nombre', 'autor_nombre',
            'fecha', 'tipo_muestra', 'estado', 'fecha_creacion',
        ]

    def get_autor_nombre(self, obj):
        return obj.autor.nombre_completo or obj.autor.username
