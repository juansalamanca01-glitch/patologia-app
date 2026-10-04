from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

from accounts.permissions import EsPatologoOAdmin, EsAutorOAdminOSoloLectura
from .models import Categoria, Patologia, Plantilla, Informe
from .serializers import (
    CategoriaSerializer,
    PatologiaSerializer, PatologiaListSerializer,
    PlantillaSerializer,
    InformeSerializer, InformeListSerializer,
)
from .utils import generar_descripcion_macroscopica, generar_pdf_informe


class CategoriaViewSet(viewsets.ModelViewSet):
    """CRUD for pathology categories. Only patólogo/admin can create, edit or delete."""
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [EsPatologoOAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre']

    def destroy(self, request, *args, **kwargs):
        categoria = self.get_object()
        if categoria.patologias.exists():
            return Response(
                {'detail': 'No se puede eliminar: hay patologías asociadas a esta categoría.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)


class PatologiaViewSet(viewsets.ModelViewSet):
    """CRUD for pathology types. Write access requires admin or patologo role."""
    queryset = Patologia.objects.select_related('categoria').prefetch_related('plantillas').all()
    permission_classes = [EsPatologoOAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre']

    def get_queryset(self):
        qs = super().get_queryset()
        categoria_id = self.request.query_params.get('categoria')
        if categoria_id:
            qs = qs.filter(categoria_id=categoria_id)
        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return PatologiaListSerializer
        return PatologiaSerializer


class PlantillaViewSet(viewsets.ModelViewSet):
    """CRUD for dynamic form field templates."""
    queryset = Plantilla.objects.select_related('patologia').all()
    serializer_class = PlantillaSerializer
    permission_classes = [EsPatologoOAdmin]

    def get_queryset(self):
        qs = super().get_queryset()
        patologia_id = self.request.query_params.get('patologia')
        if patologia_id:
            qs = qs.filter(patologia_id=patologia_id)
        return qs


class InformeViewSet(viewsets.ModelViewSet):
    """
    CRUD for clinical pathology reports.
    - Auto-assigns the author on creation
    - Generates macroscopic description on save
    - Provides PDF export and search

    Reglas (docs/decisiones.md, D-2 y D-3):
    - solo el autor o un admin puede editar, borrar o finalizar un informe;
    - un informe finalizado no se puede editar ni borrar, ni siquiera un admin.
    """
    queryset = Informe.objects.select_related('patologia', 'autor').all()
    permission_classes = [EsAutorOAdminOSoloLectura]

    def _rechazar_si_finalizado(self, informe):
        if informe.estado == Informe.Estado.FINALIZADO:
            return Response(
                {'detail': 'El informe está finalizado y no se puede modificar.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return None

    def update(self, request, *args, **kwargs):
        # get_object() comprueba primero el permiso (autor o admin → si no, 403).
        rechazo = self._rechazar_si_finalizado(self.get_object())
        return rechazo or super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        rechazo = self._rechazar_si_finalizado(self.get_object())
        return rechazo or super().destroy(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action == 'list':
            return InformeListSerializer
        return InformeSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params

        # Search filters
        q = params.get('q')
        if q:
            qs = qs.filter(
                Q(numero_caso__icontains=q) |
                Q(patologia__nombre__icontains=q) |
                Q(tipo_muestra__icontains=q)
            )

        fecha_desde = params.get('fecha_desde')
        if fecha_desde:
            qs = qs.filter(fecha__gte=fecha_desde)

        fecha_hasta = params.get('fecha_hasta')
        if fecha_hasta:
            qs = qs.filter(fecha__lte=fecha_hasta)

        estado = params.get('estado')
        if estado:
            qs = qs.filter(estado=estado)

        patologia_id = params.get('patologia')
        if patologia_id:
            qs = qs.filter(patologia_id=patologia_id)

        return qs

    def perform_create(self, serializer):
        informe = serializer.save(autor=self.request.user)
        # Auto-generate macroscopic description
        texto = generar_descripcion_macroscopica(
            informe.patologia, informe.datos_ingresados
        )
        informe.texto_generado = texto
        informe.save(update_fields=['texto_generado'])

    def perform_update(self, serializer):
        informe = serializer.save()
        # Regenerate description on update
        texto = generar_descripcion_macroscopica(
            informe.patologia, informe.datos_ingresados
        )
        informe.texto_generado = texto
        informe.save(update_fields=['texto_generado'])

    @action(detail=True, methods=['get'], url_path='pdf')
    def exportar_pdf(self, request, pk=None):
        """Export the report as a PDF file."""
        informe = self.get_object()
        buffer = generar_pdf_informe(informe)
        safe_name = informe.numero_caso.replace(' ', '_')
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="informe_{safe_name}.pdf"'
        return response

    @action(detail=True, methods=['post'], url_path='finalizar')
    def finalizar(self, request, pk=None):
        """Mark a report as finalized."""
        informe = self.get_object()
        if informe.estado == Informe.Estado.FINALIZADO:
            return Response(
                {'detail': 'El informe ya está finalizado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        informe.estado = Informe.Estado.FINALIZADO
        informe.save(update_fields=['estado'])
        return Response(InformeSerializer(informe).data)


@csrf_exempt
def descargar_pdf(request, informe_id, filename):
    """Standalone PDF download view with filename in URL path."""
    from rest_framework_simplejwt.tokens import AccessToken

    token = request.GET.get('token')
    if not token:
        return HttpResponse('Token requerido', status=401)
    try:
        AccessToken(token)
    except Exception:
        return HttpResponse('Token invalido', status=401)

    try:
        informe = Informe.objects.select_related('patologia', 'autor').get(id=informe_id)
    except Informe.DoesNotExist:
        return HttpResponse('Informe no encontrado', status=404)

    buffer = generar_pdf_informe(informe)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
