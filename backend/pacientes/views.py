from django.db.models import ProtectedError, Q
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
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
            # Puede estar en uso por pacientes (su EPS actual) o por informes (la del estudio).
            pacientes, informes = eps.pacientes.count(), eps.informes.count()
            return Response(
                {'detail': f'No se puede eliminar: esta EPS tiene {pacientes} paciente(s) y '
                           f'{informes} informe(s) asociado(s). Desactívela en su lugar.'},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PacienteViewSet(viewsets.ModelViewSet):
    """
    Pacientes (docs/propuesta-informe-v2.md, 3.1 y 4). Todos leen; patólogo y admin
    crean y editan; solo el admin borra, y solo si no tiene informes (decisión D-11).
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

    def destroy(self, request, *args, **kwargs):
        # Informe.paciente usa PROTECT: se responde 400 en lugar de un error 500 (como I-1).
        paciente = self.get_object()
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            total = paciente.informes.count()
            return Response(
                {'detail': f'No se puede eliminar: este paciente tiene {total} informe(s) asociado(s).'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=['get'])
    def informes(self, request, pk=None):
        """GET /api/pacientes/{id}/informes/: historial de informes del paciente, paginado."""
        # Import local: la app informes ya importa de pacientes.
        from informes.models import Informe
        from informes.serializers import InformeListSerializer

        paciente = self.get_object()
        qs = Informe.objects.filter(paciente=paciente).select_related('patologia', 'autor', 'paciente')
        pagina = self.paginate_queryset(qs)
        return self.get_paginated_response(InformeListSerializer(pagina, many=True).data)
