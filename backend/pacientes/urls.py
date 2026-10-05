from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# "eps" va antes que los pacientes, cuya ruta empieza en la raíz (/api/pacientes/).
router.register(r'eps', views.EPSViewSet, basename='eps')
router.register(r'', views.PacienteViewSet, basename='paciente')

urlpatterns = [
    path('', include(router.urls)),
]
