import re

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse
from django.db.models import Count, Q, ProtectedError

from accounts.permissions import EsPatologoOAdmin, EsAutorOAdminOSoloLectura
from config.catalogos import filtrar_por_activo
from pacientes.models import Sexo, TipoDocumento
from .models import Categoria, Patologia, Plantilla, Informe, Servicio
from .serializers import (
    CategoriaSerializer,
    PatologiaSerializer, PatologiaListSerializer,
    PlantillaSerializer,
    ServicioSerializer,
    InformeSerializer, InformeListSerializer,
)
from .utils import generar_descripcion_macroscopica, generar_pdf_informe


class CategoriaViewSet(viewsets.ModelViewSet):
    """Categorías de patologías. Todos leen; crear, editar o borrar requiere patólogo o admin."""
    # El total de patologías se cuenta en la misma consulta (auditoría M-4).
    # Con annotate(Count), Django ignora Meta.ordering: el orden se indica aquí.
    queryset = Categoria.objects.annotate(num_patologias=Count('patologias')).order_by('nombre')
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
    """Tipos de patología. Todos leen; crear, editar o borrar requiere patólogo o admin."""
    queryset = Patologia.objects.select_related('categoria').prefetch_related('plantillas').all()
    permission_classes = [EsPatologoOAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre']

    def get_queryset(self):
        qs = super().get_queryset()
        categoria_id = self.request.query_params.get('categoria')
        if categoria_id:
            qs = qs.filter(categoria_id=categoria_id)
        # ?activa=true / ?activa=false (decisión D-4): "Nuevo informe" pide solo las activas.
        activa = self.request.query_params.get('activa')
        if activa in ('true', 'false'):
            qs = qs.filter(activa=(activa == 'true'))
        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return PatologiaListSerializer
        return PatologiaSerializer

    def destroy(self, request, *args, **kwargs):
        # Informe.patologia usa PROTECT: si hay informes, Django lanza ProtectedError
        # antes de borrar nada. Se responde 400 en lugar de un error 500 (auditoría I-1).
        patologia = self.get_object()
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            total = patologia.informes.count()
            return Response(
                {'detail': f'No se puede eliminar: esta patología tiene {total} informe(s) asociado(s).'},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PlantillaViewSet(viewsets.ModelViewSet):
    """Campos de los formularios dinámicos (plantillas)."""
    queryset = Plantilla.objects.select_related('patologia').all()
    serializer_class = PlantillaSerializer
    permission_classes = [EsPatologoOAdmin]

    def get_queryset(self):
        qs = super().get_queryset()
        patologia_id = self.request.query_params.get('patologia')
        if patologia_id:
            qs = qs.filter(patologia_id=patologia_id)
        return qs


class ServicioViewSet(viewsets.ModelViewSet):
    """Catálogo de servicios. Todos leen; patólogo o admin lo administran (decisión D-11)."""
    queryset = Servicio.objects.all()
    serializer_class = ServicioSerializer
    permission_classes = [EsPatologoOAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre']

    def get_queryset(self):
        # ?activo=true: los formularios ofrecen solo los servicios activos (D-4).
        return filtrar_por_activo(super().get_queryset(), self.request, 'activo')

    def destroy(self, request, *args, **kwargs):
        # Informe.servicio usa PROTECT: un servicio en uso se desactiva, no se borra (D-4, como I-1).
        servicio = self.get_object()
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            total = servicio.informes.count()
            return Response(
                {'detail': f'No se puede eliminar: este servicio tiene {total} informe(s) asociado(s). '
                           'Desactívelo en su lugar.'},
                status=status.HTTP_400_BAD_REQUEST,
            )


def _opciones(choices):
    return [{'valor': valor, 'etiqueta': etiqueta} for valor, etiqueta in choices.choices]


class OpcionesView(APIView):
    """
    GET /api/opciones/: listas fijas sacadas de los TextChoices, para que el
    frontend no las copie (docs/propuesta-informe-v2.md, 3.3). Las EPS y los
    servicios son catálogos editables y tienen sus propios endpoints.
    """

    def get(self, request):
        return Response({
            'sexos': _opciones(Sexo),
            'tipos_documento': _opciones(TipoDocumento),
            'tipos_estudio': _opciones(Informe.TipoEstudio),
        })


class InformeViewSet(viewsets.ModelViewSet):
    """
    Informes de patología.
    - Al crear un informe, su autor es el usuario que hace la petición.
    - Al guardar, se genera la descripción macroscópica.
    - Permite buscar, ver estadísticas y exportar a PDF.

    Reglas (docs/decisiones.md, D-2 y D-3):
    - solo el autor o un admin puede editar, borrar o finalizar un informe;
    - un informe finalizado no se puede editar ni borrar, ni siquiera un admin.
    """
    queryset = Informe.objects.select_related('patologia', 'autor', 'paciente', 'eps', 'servicio').all()
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

        # Filtros de búsqueda
        # Cada palabra de ?q= debe aparecer en alguno de los campos: así "ficticio uno"
        # encuentra a "Paciente Ficticio Uno" aunque esté repartido en nombres y apellidos.
        for palabra in params.get('q', '').split():
            qs = qs.filter(
                Q(numero_peticion__icontains=palabra) |
                Q(numero_orden_externa__icontains=palabra) |
                Q(patologia__nombre__icontains=palabra) |
                Q(tipo_muestra__icontains=palabra) |
                # El documento se guarda sin puntos: "1.234" también encuentra "1234".
                Q(paciente__numero_documento__icontains=palabra.replace('.', '')) |
                Q(paciente__nombres__icontains=palabra) |
                Q(paciente__apellidos__icontains=palabra)
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

        paciente_id = params.get('paciente')
        if paciente_id:
            qs = qs.filter(paciente_id=paciente_id)

        return qs

    def perform_create(self, serializer):
        informe = serializer.save(autor=self.request.user)
        # Genera la descripción macroscópica
        texto = generar_descripcion_macroscopica(
            informe.patologia, informe.datos_ingresados
        )
        informe.texto_generado = texto
        informe.save(update_fields=['texto_generado'])

    def perform_update(self, serializer):
        informe = serializer.save()
        # Vuelve a generar la descripción al editar
        texto = generar_descripcion_macroscopica(
            informe.patologia, informe.datos_ingresados
        )
        informe.texto_generado = texto
        informe.save(update_fields=['texto_generado'])

    @action(detail=False, methods=['get'], url_path='estadisticas')
    def estadisticas(self, request):
        """
        Totales de informes por estado, contando todos los informes y no solo
        una página del listado (auditoría I-4). Respeta los mismos filtros que
        el listado (q, fechas, estado, patologia).
        """
        por_estado = dict(
            self.get_queryset()
            .order_by()  # sin el orden por fecha, para que el GROUP BY sea solo por estado
            .values_list('estado')
            .annotate(total=Count('id'))
        )
        return Response({
            'total': sum(por_estado.values()),
            'borradores': por_estado.get(Informe.Estado.BORRADOR, 0),
            'finalizados': por_estado.get(Informe.Estado.FINALIZADO, 0),
        })

    @action(detail=True, methods=['get'], url_path='pdf')
    def exportar_pdf(self, request, pk=None):
        """Descarga el informe en PDF."""
        informe = self.get_object()
        buffer = generar_pdf_informe(informe)
        # El número de petición lo genera el sistema (D-7), pero se sigue limpiando:
        # unas comillas o un punto y coma romperían la cabecera Content-Disposition (I-5).
        # El nombre del archivo nunca lleva datos del paciente.
        safe_name = re.sub(r'[^A-Za-z0-9\-]', '_', informe.numero_peticion)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="informe_{safe_name}.pdf"'
        return response

    @action(detail=True, methods=['post'], url_path='finalizar')
    def finalizar(self, request, pk=None):
        """Marca el informe como finalizado (después ya no se puede editar)."""
        informe = self.get_object()
        if informe.estado == Informe.Estado.FINALIZADO:
            return Response(
                {'detail': 'El informe ya está finalizado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        informe.estado = Informe.Estado.FINALIZADO
        informe.save(update_fields=['estado'])
        return Response(InformeSerializer(informe).data)

