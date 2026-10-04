from rest_framework import viewsets, mixins, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.throttling import ScopedRateThrottle

from accounts.permissions import EsPatologoOAdmin, EsAutorOAdminOSoloLectura
from .models import TemaForo, Publicacion, ImagenPublicacion, Comentario
from .serializers import (
    TemaForoSerializer,
    PublicacionSerializer, PublicacionListSerializer,
    ImagenPublicacionSerializer,
    ComentarioSerializer,
)

MAX_IMAGENES_POR_PUBLICACION = 6


class TemaForoViewSet(viewsets.ModelViewSet):
    """CRUD for forum topics. Only patólogo/admin can create, edit or delete."""
    queryset = TemaForo.objects.all()
    serializer_class = TemaForoSerializer
    permission_classes = [EsPatologoOAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre']


class PublicacionViewSet(viewsets.ModelViewSet):
    """
    CRUD for forum posts shared by pathologists (research notes, observations).
    Supports attaching images and nested comments.
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
        tema_id = self.request.query_params.get('tema')
        if tema_id:
            qs = qs.filter(tema_id=tema_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)

    @action(detail=True, methods=['post'], url_path='imagenes')
    def subir_imagenes(self, request, pk=None):
        """Attach one or more images to an existing post (author or admin only)."""
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

        creadas = []
        for archivo in archivos:
            imagen = ImagenPublicacion.objects.create(publicacion=publicacion, imagen=archivo)
            creadas.append(imagen)

        serializer = ImagenPublicacionSerializer(creadas, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ImagenPublicacionViewSet(mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """Allows removing a single image from a post (author or admin only)."""
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
    """CRUD for comments on forum posts."""
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
