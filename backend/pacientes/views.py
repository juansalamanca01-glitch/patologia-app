from rest_framework import filters, viewsets

from accounts.permissions import EsPatologoOAdmin
from config.catalogos import filtrar_por_activo
from .models import EPS
from .serializers import EPSSerializer


class EPSViewSet(viewsets.ModelViewSet):
    """Catálogo de EPS. Todos leen; patólogo o admin lo administran (decisión D-11)."""
    queryset = EPS.objects.all()
    serializer_class = EPSSerializer
    permission_classes = [EsPatologoOAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre']

    def get_queryset(self):
        # ?activa=true: los formularios ofrecen solo las EPS activas (D-4).
        return filtrar_por_activo(super().get_queryset(), self.request, 'activa')
