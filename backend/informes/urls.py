from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'patologias', views.PatologiaViewSet, basename='patologia')
router.register(r'plantillas', views.PlantillaViewSet, basename='plantilla')
router.register(r'informes', views.InformeViewSet, basename='informe')

urlpatterns = [
    path('descargar-pdf/<int:informe_id>/<str:filename>', views.descargar_pdf, name='descargar_pdf'),
    path('', include(router.urls)),
]
