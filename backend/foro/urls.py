from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'temas', views.TemaForoViewSet, basename='tema-foro')
router.register(r'publicaciones', views.PublicacionViewSet, basename='publicacion')
router.register(r'imagenes', views.ImagenPublicacionViewSet, basename='imagen-publicacion')
router.register(r'comentarios', views.ComentarioViewSet, basename='comentario')

urlpatterns = [
    path('', include(router.urls)),
]
