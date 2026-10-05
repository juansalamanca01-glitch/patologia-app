from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categorias', views.CategoriaViewSet, basename='categoria')
router.register(r'patologias', views.PatologiaViewSet, basename='patologia')
router.register(r'plantillas', views.PlantillaViewSet, basename='plantilla')
router.register(r'informes', views.InformeViewSet, basename='informe')
router.register(r'servicios', views.ServicioViewSet, basename='servicio')

urlpatterns = [
    path('opciones/', views.OpcionesView.as_view(), name='opciones'),
    path('', include(router.urls)),
]
