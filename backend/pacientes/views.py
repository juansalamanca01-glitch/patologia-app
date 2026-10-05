from django.db.models import ProtectedError, Q
from rest_framework import filters, status, viewsets
from rest_framework.response import Response

from accounts.permissions import EsPatologoOAdmin, EsPatologoOAdminYSoloAdminBorra
from config.catalogos import filtrar_por_activo
from .models import EPS, Paciente
from .serializers import EPSSerializer, PacienteSerializer


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

    def destroy(self, request, *args, **kwargs):
        # Paciente.eps usa PROTECT: una EPS en uso se desactiva, no se borra (D-4, como I-1).
        eps = self.get_object()
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            total = eps.pacientes.count()
            return Response(
                {'detail': f'No se puede eliminar: esta EPS tiene {total} paciente(s) asociado(s). '
                           'Desactívela en su lugar.'},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PacienteViewSet(viewsets.ModelViewSet):
    """
    Pacientes (docs/propuesta-informe-v2.md, 3.1 y 4). Todos leen; patólogo y admin
    crean y editan; solo el admin borra (decisión D-11).
    ?q= busca por documento, nombres y apellidos: cada palabra debe aparecer en
    alguno de los tres, así que "ficticio uno" encuentra a "Paciente Ficticio Uno".
    """
    queryset = Paciente.objects.select_related('eps')
    serializer_class = PacienteSerializer
    permission_classes = [EsPatologoOAdminYSoloAdminBorra]
    # Solo ids numéricos, para que /api/pacientes/eps/ no se tome como un paciente.
    lookup_value_regex = r'\d+'

    def get_queryset(self):
        qs = super().get_queryset()
        for palabra in self.request.query_params.get('q', '').split():
            # El documento se guarda sin puntos: "1.234" también encuentra "1234".
            documento = palabra.replace('.', '')
            qs = qs.filter(
                Q(numero_documento__icontains=documento)
                | Q(nombres__icontains=palabra)
                | Q(apellidos__icontains=palabra)
            )
        return qs
