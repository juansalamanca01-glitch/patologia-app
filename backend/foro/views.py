from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from accounts.permissions import EsAutorOAdminOSoloLectura, EsPatologoOAdmin

from .models import Comentario, ImagenPublicacion, Publicacion, TemaForo
from .serializers import (
    ComentarioSerializer,
    ImagenPublicacionSerializer,
    PublicacionListSerializer,
    PublicacionSerializer,
    TemaForoSerializer,
)

MAX_IMAGENES_POR_PUBLICACION = 6


class TemaForoViewSet(viewsets.ModelViewSet):
    """Temas del foro. Todos leen; crear, editar o borrar requiere patólogo o admin."""

    # El total de publicaciones se cuenta en la misma consulta (auditoría M-4).
    # Con annotate(Count), Django ignora Meta.ordering: el orden se indica aquí.
    queryset = TemaForo.objects.annotate(num_publicaciones=Count('publicaciones')).order_by('nombre')
    serializer_class = TemaForoSerializer
    permission_classes = [EsPatologoOAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre']


class PublicacionViewSet(viewsets.ModelViewSet):
    """
    Publicaciones del foro (notas de investigación, observaciones, casos).
    Admite imágenes adjuntas y comentarios.
    """

    queryset = Publicacion.objects.select_related('autor', 'tema').prefetch_related('imagenes', 'comentarios__autor')
    permission_classes = [EsAutorOAdminOSoloLectura]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['titulo', 'contenido']

    def get_serializer_class(self):
        if self.action == 'list':
            return PublicacionListSerializer
        return PublicacionSerializer

    def get_throttles(self):
        if self.action == 'create':
            self.throttle_scope = 'foro_publicacion'
            return [ScopedRateThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == 'list':
            # El listado solo necesita los totales y la primera imagen, no los
            # comentarios completos (auditoría M-4).
            qs = (
                Publicacion.objects.select_related('autor', 'tema')
                .prefetch_related('imagenes')
                .annotate(
                    num_comentarios=Count('comentarios', distinct=True),
                    num_imagenes=Count('imagenes', distinct=True),
                )
                .order_by('-fijado', '-fecha_creacion')
            )  # annotate ignora Meta.ordering
        tema_id = self.request.query_params.get('tema')
        if tema_id:
            qs = qs.filter(tema_id=tema_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)

    @action(detail=True, methods=['post'], url_path='imagenes')
    def subir_imagenes(self, request, pk=None):
        """Adjunta una o más imágenes a una publicación existente (solo su autor o un admin)."""
        publicacion = self.get_object()
        if request.user.rol != 'admin' and publicacion.autor_id != request.user.id:
            return Response(
                {'detail': 'Solo el autor de la publicación puede añadir imágenes.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        archivos = request.FILES.getlist('imagenes')
        if not archivos:
            return Response({'detail': 'No se recibió ninguna imagen.'}, status=status.HTTP_400_BAD_REQUEST)

        existentes = publicacion.imagenes.count()
        if existentes + len(archivos) > MAX_IMAGENES_POR_PUBLICACION:
            return Response(
                {'detail': f'Máximo {MAX_IMAGENES_POR_PUBLICACION} imágenes por publicación.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Se revisan TODOS los archivos antes de guardar ninguno (auditoría I-6).
        limite = settings.FORO_MAX_TAMANO_IMAGEN
        for archivo in archivos:
            if archivo.size > limite:
                return Response(
                    {'detail': f'«{archivo.name}» supera el tamaño máximo de {limite / (1024 * 1024):g} MB.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                # Abre el archivo con Pillow: rechaza lo que no sea una imagen real,
                # aunque tenga extensión .png (por ejemplo, un HTML disfrazado).
                forms.ImageField().to_python(archivo)
            except ValidationError:
                return Response(
                    {'detail': f'«{archivo.name}» no es una imagen válida.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        with transaction.atomic():
            creadas = [
                ImagenPublicacion.objects.create(publicacion=publicacion, imagen=archivo) for archivo in archivos
            ]

        serializer = ImagenPublicacionSerializer(creadas, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ImagenPublicacionViewSet(mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """Permite borrar una imagen de una publicación (solo su autor o un admin)."""

    queryset = ImagenPublicacion.objects.select_related('publicacion')
    serializer_class = ImagenPublicacionSerializer

    def perform_destroy(self, instance):
        user = self.request.user
        if user.rol != 'admin' and instance.publicacion.autor_id != user.id:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied('Solo el autor de la publicación puede eliminar sus imágenes.')
        instance.imagen.delete(save=False)
        instance.delete()


class ComentarioViewSet(viewsets.ModelViewSet):
    """Comentarios en las publicaciones del foro."""

    queryset = Comentario.objects.select_related('autor', 'publicacion')
    serializer_class = ComentarioSerializer
    permission_classes = [EsAutorOAdminOSoloLectura]

    def get_throttles(self):
        if self.action == 'create':
            self.throttle_scope = 'foro_comentario'
            return [ScopedRateThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        qs = super().get_queryset()
        publicacion_id = self.request.query_params.get('publicacion')
        if publicacion_id:
            qs = qs.filter(publicacion_id=publicacion_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)
