from rest_framework import serializers
from .models import TemaForo, Publicacion, ImagenPublicacion, Comentario


class TemaForoSerializer(serializers.ModelSerializer):
    total_publicaciones = serializers.IntegerField(source='publicaciones.count', read_only=True)

    class Meta:
        model = TemaForo
        fields = ['id', 'nombre', 'descripcion', 'activo', 'total_publicaciones', 'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion']


class ImagenPublicacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagenPublicacion
        fields = ['id', 'imagen', 'descripcion', 'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion']


class ComentarioSerializer(serializers.ModelSerializer):
    autor_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Comentario
        fields = ['id', 'publicacion', 'autor', 'autor_nombre', 'contenido', 'fecha_creacion']
        read_only_fields = ['id', 'autor', 'fecha_creacion']

    def get_fields(self):
        campos = super().get_fields()
        # La publicación se elige al crear el comentario; al editarlo no se puede
        # cambiar, para que nadie mueva su comentario a otra publicación (auditoría I-8).
        if self.instance is not None:
            campos['publicacion'].read_only = True
        return campos

    def get_autor_nombre(self, obj):
        return obj.autor.nombre_completo or obj.autor.username

    def validate_contenido(self, value):
        if not value.strip():
            raise serializers.ValidationError('El comentario no puede estar vacío.')
        if len(value) > 3000:
            raise serializers.ValidationError('El comentario es demasiado largo (máx. 3000 caracteres).')
        return value


class PublicacionSerializer(serializers.ModelSerializer):
    autor_nombre = serializers.SerializerMethodField()
    tema_nombre = serializers.CharField(source='tema.nombre', read_only=True, default=None)
    imagenes = ImagenPublicacionSerializer(many=True, read_only=True)
    comentarios = ComentarioSerializer(many=True, read_only=True)
    total_comentarios = serializers.IntegerField(source='comentarios.count', read_only=True)

    class Meta:
        model = Publicacion
        fields = [
            'id', 'tema', 'tema_nombre', 'autor', 'autor_nombre', 'titulo', 'contenido',
            'fijado', 'imagenes', 'comentarios', 'total_comentarios',
            'fecha_creacion', 'fecha_actualizacion',
        ]
        read_only_fields = ['id', 'autor', 'fecha_creacion', 'fecha_actualizacion']

    def get_fields(self):
        campos = super().get_fields()
        # Solo un admin puede fijar o desfijar publicaciones (auditoría I-8).
        # Depende de quién hace la petición, por eso no va en read_only_fields.
        request = self.context.get('request')
        if not (request and request.user.is_authenticated and request.user.rol == 'admin'):
            campos['fijado'].read_only = True
        return campos

    def get_autor_nombre(self, obj):
        return obj.autor.nombre_completo or obj.autor.username

    def validate_titulo(self, value):
        if not value.strip():
            raise serializers.ValidationError('El título no puede estar vacío.')
        return value

    def validate_contenido(self, value):
        if not value.strip():
            raise serializers.ValidationError('El contenido no puede estar vacío.')
        return value


class PublicacionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for the forum feed."""
    autor_nombre = serializers.SerializerMethodField()
    tema_nombre = serializers.CharField(source='tema.nombre', read_only=True, default=None)
    total_comentarios = serializers.IntegerField(source='comentarios.count', read_only=True)
    total_imagenes = serializers.IntegerField(source='imagenes.count', read_only=True)
    portada = serializers.SerializerMethodField()

    class Meta:
        model = Publicacion
        fields = [
            'id', 'tema', 'tema_nombre', 'autor_nombre', 'titulo', 'fijado',
            'total_comentarios', 'total_imagenes', 'portada', 'fecha_creacion',
        ]

    def get_autor_nombre(self, obj):
        return obj.autor.nombre_completo or obj.autor.username

    def get_portada(self, obj):
        primera = obj.imagenes.first()
        if not primera:
            return None
        request = self.context.get('request')
        url = primera.imagen.url
        return request.build_absolute_uri(url) if request else url
