from rest_framework import serializers
from .models import Categoria, Patologia, Plantilla, Informe


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
    total_patologias = serializers.IntegerField(source='patologias.count', read_only=True)

    class Meta:
        model = Categoria
        fields = [
            'id', 'nombre', 'descripcion', 'color', 'activa',
            'total_patologias', 'fecha_creacion',
        ]
        read_only_fields = ['id', 'fecha_creacion']


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
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True, default=None)

    class Meta:
        model = Patologia
        fields = [
            'id', 'nombre', 'categoria', 'categoria_nombre', 'descripcion',
            'protocolo_medico', 'activa', 'plantillas',
            'fecha_creacion', 'fecha_actualizacion',
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']


class PatologiaListSerializer(serializers.ModelSerializer):
    """Versión resumida para listas y menús desplegables."""
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True, default=None)

    class Meta:
        model = Patologia
        fields = ['id', 'nombre', 'categoria', 'categoria_nombre', 'activa']


class InformeSerializer(serializers.ModelSerializer):
    patologia_nombre = serializers.CharField(source='patologia.nombre', read_only=True)
    autor_nombre = serializers.CharField(source='autor.nombre_visible', read_only=True)

    class Meta:
        model = Informe
        fields = [
            'id', 'numero_caso', 'patologia', 'patologia_nombre',
            'autor', 'autor_nombre', 'fecha', 'tipo_muestra',
            'datos_ingresados', 'texto_generado', 'estado', 'notas',
            'fecha_creacion', 'fecha_actualizacion',
        ]
        read_only_fields = ['id', 'autor', 'texto_generado', 'fecha', 'fecha_creacion', 'fecha_actualizacion']

    def validate(self, data):
        """Comprueba que estén llenos los campos obligatorios de la plantilla de la patología."""
        patologia = data.get('patologia') or (self.instance and self.instance.patologia)
        # Si la petición no trae datos_ingresados (p. ej. un PATCH que solo cambia las
        # notas), se validan los datos ya guardados del informe.
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
                raise serializers.ValidationError({
                    'datos_ingresados': f'Faltan campos obligatorios: {", ".join(faltantes)}'
                })

        return data


class InformeListSerializer(serializers.ModelSerializer):
    """Versión resumida para el listado de informes."""
    patologia_nombre = serializers.CharField(source='patologia.nombre', read_only=True)
    autor_nombre = serializers.CharField(source='autor.nombre_visible', read_only=True)

    class Meta:
        model = Informe
        fields = [
            'id', 'numero_caso', 'patologia_nombre', 'autor', 'autor_nombre',
            'fecha', 'tipo_muestra', 'estado', 'fecha_creacion',
        ]
