"""
Generación de la descripción macroscópica y exportación del informe a PDF.
"""
import io
from functools import partial
from xml.sax.saxutils import escape

from django.utils import timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether, CondPageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

from pacientes.models import Sexo


def texto_seguro(texto) -> str:
    """
    Prepara texto escrito por el usuario para un Paragraph de ReportLab.
    Paragraph interpreta etiquetas como <b> o <font>; al escapar <, > y &
    el texto se muestra literal (auditoría I-3). Los saltos de línea se
    convierten en <br/> para que se respeten en el PDF.
    """
    return escape(str(texto)).replace('\r\n', '\n').replace('\n', '<br/>')


# ── Generador de la descripción macroscópica ────────────────────────────
def generar_descripcion_macroscopica(patologia, datos: dict) -> str:
    """
    Redacta el párrafo de descripción macroscópica a partir del tipo de
    patología y de los datos que llenó el patólogo en el formulario.
    """
    nombre_patologia = patologia.nombre
    partes = [f"Se recibe espécimen para estudio de {nombre_patologia}."]

    # Frase en lenguaje natural para los campos más comunes
    mapeo = {
        'tipo_muestra': 'El tipo de muestra corresponde a {v}.',
        'localizacion': 'La localización anatómica es {v}.',
        'tamanio': 'La pieza mide {v}.',
        'dimensiones': 'Las dimensiones son {v}.',
        'peso': 'El peso registrado es de {v} gramos.',
        'color': 'El color macroscópico observado es {v}.',
        'consistencia': 'La consistencia es {v}.',
        'forma': 'La forma observada es {v}.',
        'superficie': 'La superficie se describe como {v}.',
        'bordes': 'Los bordes se observan {v}.',
        'margenes': 'Los márgenes quirúrgicos se reportan como {v}.',
        'ganglios': 'Se identifican {v} ganglio(s) linfático(s).',
        'hallazgos_adicionales': 'Hallazgos adicionales: {v}.',
        'observaciones': 'Observaciones: {v}.',
        'tumor_tamanio': 'El tamaño tumoral es de {v}.',
        'necrosis': 'Se observa necrosis: {v}.',
        'hemorragia': 'Se observa hemorragia: {v}.',
        'calcificaciones': 'Se identifican calcificaciones: {v}.',
    }

    for campo, plantilla in mapeo.items():
        valor = datos.get(campo)
        if valor and str(valor).strip():
            partes.append(plantilla.format(v=str(valor).strip()))

    # Los campos que no están en el mapa se agregan como "Etiqueta: valor"
    campos_mapeados = set(mapeo.keys())
    for campo, valor in datos.items():
        if campo not in campos_mapeados and valor and str(valor).strip():
            label = campo.replace('_', ' ').capitalize()
            partes.append(f'{label}: {valor}.')

    partes.append(
        'Se procesa el material y se remite para estudio histopatológico.'
    )

    return ' '.join(partes)


# ── Exportación a PDF ───────────────────────────────────────────────────
# Estructura del informe real (docs/propuesta-informe-v2.md, sección 5).

# Encabezado fijo de demostración (respuesta P-9): no copia los datos de ningún
# laboratorio real. Leerlo de la configuración (.env) queda como propuesta futura.
ENCABEZADO_LABORATORIO = 'PathoLab — Laboratorio de Patología (demostración)'
ENCABEZADO_CIUDAD = 'Santiago de Cali, Colombia'

SIN_DATO = '—'
AVISO_BORRADOR = 'BORRADOR — SIN VALIDEZ'
AZUL_OSCURO = HexColor('#1a365d')
AZUL = HexColor('#2b6cb0')
GRIS_TEXTO = HexColor('#2d3748')
GRIS_SUAVE = HexColor('#718096')
GRIS_LINEA = HexColor('#cbd5e0')
ROJO = HexColor('#c53030')


class CanvasNumerado(canvas.Canvas):
    """
    Lienzo que dibuja el pie de cada página al final, cuando ya se sabe el total:
    "N.º de petición … · Página X de Y · Generado el …". `pie` es el texto que va
    antes y después de "Página X de Y".
    """

    def __init__(self, *args, pie=('', ''), **kwargs):
        super().__init__(*args, **kwargs)
        self._pie = pie
        self._paginas = []

    def showPage(self):
        # Guarda la página en vez de cerrarla; se cierra en save() con el pie.
        self._paginas.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._paginas)
        for numero, estado in enumerate(self._paginas, start=1):
            self.__dict__.update(estado)
            antes, despues = self._pie
            self.setFont('Helvetica', 8)
            self.setFillColor(GRIS_SUAVE)
            self.drawCentredString(letter[0] / 2, 1 * cm, f'{antes}Página {numero} de {total}{despues}')
            super().showPage()
        super().save()


def _estilos():
    estilos = getSampleStyleSheet()
    estilos.add(ParagraphStyle(
        'Laboratorio', parent=estilos['Normal'], fontName='Helvetica-Bold', fontSize=13,
        textColor=AZUL_OSCURO, alignment=TA_CENTER, leading=16,
    ))
    estilos.add(ParagraphStyle(
        'Ciudad', parent=estilos['Normal'], fontSize=9, textColor=GRIS_SUAVE, alignment=TA_CENTER,
    ))
    estilos.add(ParagraphStyle('Celda', parent=estilos['Normal'], fontSize=9, leading=12, textColor=GRIS_TEXTO))
    estilos.add(ParagraphStyle(
        'TituloInforme', parent=estilos['Title'], fontSize=15, textColor=AZUL_OSCURO, spaceBefore=14, spaceAfter=4,
    ))
    estilos.add(ParagraphStyle('TipoEstudio', parent=estilos['Normal'], fontSize=11, alignment=TA_CENTER))
    estilos.add(ParagraphStyle(
        'Muestra', parent=estilos['Normal'], fontSize=8.5, textColor=GRIS_SUAVE, alignment=TA_CENTER,
    ))
    estilos.add(ParagraphStyle(
        'Subtitulo', parent=estilos['Heading2'], fontSize=11.5, textColor=GRIS_TEXTO, spaceBefore=12, spaceAfter=4,
    ))
    estilos.add(ParagraphStyle(
        'CuerpoTexto', parent=estilos['BodyText'], fontSize=10, alignment=TA_JUSTIFY, leading=14,
    ))
    estilos.add(ParagraphStyle('Firma', parent=estilos['Normal'], fontSize=10, leading=13, alignment=TA_CENTER))
    estilos.add(ParagraphStyle(
        'AvisoAdendas', parent=estilos['Normal'], fontName='Helvetica-Bold', fontSize=10,
        textColor=ROJO, alignment=TA_CENTER, borderColor=ROJO, borderWidth=0.75, borderPadding=5,
        spaceBefore=8, spaceAfter=6,
    ))
    estilos.add(ParagraphStyle(
        'TituloAdenda', parent=estilos['Normal'], fontName='Helvetica-Bold', fontSize=10.5,
        textColor=GRIS_TEXTO, spaceBefore=18, spaceAfter=4,
    ))
    return estilos


def _encabezado(estilos):
    return [
        Paragraph(ENCABEZADO_LABORATORIO, estilos['Laboratorio']),
        Paragraph(ENCABEZADO_CIUDAD, estilos['Ciudad']),
        Spacer(1, 6),
        HRFlowable(width='100%', thickness=2, color=AZUL),
        Spacer(1, 10),
    ]


def _fecha_de_informe(informe):
    """En un borrador va el aviso de que no tiene validez (sección 5.2)."""
    if not informe.esta_finalizado:
        return AVISO_BORRADOR
    if informe.fecha_informe is None:
        return None
    return timezone.localtime(informe.fecha_informe).strftime('%d/%m/%Y %H:%M')


def _tabla_datos(informe, datos, estilos, ancho):
    """Datos del paciente y de la solicitud en dos columnas, como el formato real."""
    paciente = datos['paciente']

    def celda(etiqueta, valor):
        # El valor lo escribe el usuario (o sale de un catálogo): siempre escapado (I-3).
        return Paragraph(f'<b>{etiqueta}:</b> {texto_seguro(valor) if valor else SIN_DATO}', estilos['Celda'])

    filas = [
        [celda('Paciente', paciente and paciente['nombre_completo']),
         celda('Identificación', paciente and f"{paciente['tipo_documento']} {paciente['numero_documento']}")],
        [celda('Edad', informe.edad_paciente(paciente)),
         celda('Sexo', paciente and Sexo(paciente['sexo']).label)],
        [celda('Médico tratante', informe.medico_tratante), celda('EPS', datos['eps_nombre'])],
        [celda('Servicio', datos['servicio_nombre']), celda('N.º de petición', informe.numero_peticion)],
        [celda('Fecha de ingreso', informe.fecha_ingreso and informe.fecha_ingreso.strftime('%d/%m/%Y')),
         celda('Fecha de informe', _fecha_de_informe(informe))],
    ]
    # Estas filas ocupan todo el ancho.
    if informe.numero_orden_externa:
        filas.append([celda('Orden externa', informe.numero_orden_externa), ''])
    filas.append([celda('Estudios solicitados', informe.estudios_solicitados), ''])

    tabla = Table(filas, colWidths=[ancho / 2, ancho / 2])
    tabla.setStyle(TableStyle(
        [
            ('BOX', (0, 0), (-1, -1), 0.75, GRIS_LINEA),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, GRIS_LINEA),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]
        + [('SPAN', (0, fila), (1, fila)) for fila in range(5, len(filas))]
    ))
    return [tabla]


def _titulo(informe, estilos):
    return [
        Paragraph('INFORME DE ANATOMÍA PATOLÓGICA', estilos['TituloInforme']),
        Paragraph(f'<b>Tipo de estudio:</b> {informe.get_tipo_estudio_display()}', estilos['TipoEstudio']),
        Paragraph(
            f'Patología: {texto_seguro(informe.patologia.nombre)} · '
            f'Tipo de muestra: {texto_seguro(informe.tipo_muestra or SIN_DATO)}',
            estilos['Muestra'],
        ),
        Spacer(1, 4),
    ]


def _seccion(titulo, parrafos, estilos):
    """Título con su línea y los párrafos, ya escapados con texto_seguro (I-3)."""
    return [
        # El título no queda solo al final de una página: si quedan menos de 4 cm,
        # la sección empieza en la siguiente.
        CondPageBreak(4 * cm),
        Paragraph(titulo, estilos['Subtitulo']),
        HRFlowable(width='100%', thickness=0.5, color=GRIS_LINEA),
        Spacer(1, 4),
        *[Paragraph(parrafo, estilos['CuerpoTexto']) for parrafo in parrafos],
    ]


def _lineas_firma(firma, estilos):
    """Línea de firma con nombre, especialidad y registro médico (D-8, D-9)."""
    bloque = [
        Spacer(1, 32),
        HRFlowable(width=7 * cm, thickness=0.75, color=GRIS_TEXTO, spaceAfter=4),
        Paragraph(texto_seguro(firma['nombre']), estilos['Firma']),
    ]
    if firma['especialidad']:
        bloque.append(Paragraph(texto_seguro(firma['especialidad']), estilos['Firma']))
    if firma['registro_medico']:
        bloque.append(Paragraph(f"Registro médico N.º {texto_seguro(firma['registro_medico'])}", estilos['Firma']))
    return bloque


def _firma(firma, estilos):
    """Firma del autor del informe (D-8). Un borrador no lleva firma."""
    # La firma no se parte entre dos páginas.
    return [KeepTogether(_lineas_firma(firma, estilos))]


def _aviso_adendas(total, estilos):
    """Al principio del informe: que nadie lea el diagnóstico original sin saber que se corrigió (3.8)."""
    adendas = 'adenda' if total == 1 else 'adendas'
    return [Paragraph(f'Este informe tiene {total} {adendas}; ver al final.', estilos['AvisoAdendas'])]


def _adendas(adendas, estilos):
    """Sección ADENDAS (decisión D-9): cada una con número, fecha, motivo, texto y su firma congelada."""
    # Sin el CondPageBreak de _seccion: el título va en el bloque de la primera adenda.
    titulo = _seccion('ADENDAS', [], estilos)[1:]
    elementos = []
    for posicion, adenda in enumerate(adendas):
        fecha = timezone.localtime(adenda.fecha).strftime('%d/%m/%Y %H:%M')
        # La adenda va entera en una página si cabe, para que su firma no quede sola,
        # y el título de la sección no queda separado de la primera.
        elementos.append(KeepTogether([
            *(titulo if posicion == 0 else []),
            Paragraph(f'Adenda N.º {adenda.numero} — {fecha}', estilos['TituloAdenda']),
            Paragraph(f'<b>Motivo:</b> {texto_seguro(adenda.motivo)}', estilos['CuerpoTexto']),
            Spacer(1, 4),
            Paragraph(texto_seguro(adenda.texto), estilos['CuerpoTexto']),
            *_lineas_firma(adenda.firma, estilos),
        ]))
    return elementos


def generar_pdf_informe(informe) -> io.BytesIO:
    """Genera el PDF del informe y lo devuelve en un buffer de bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=1.5 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        title=f'Informe {informe.numero_peticion}',
    )
    estilos = _estilos()
    # Paciente, EPS, servicio y firma: congelados si está finalizado (D-10).
    datos = informe.datos_impresos()

    elementos = [
        *_encabezado(estilos),
        *_tabla_datos(informe, datos, estilos, doc.width),
        *_titulo(informe, estilos),
    ]

    # Solo un informe finalizado tiene adendas (D-9).
    adendas = list(informe.adendas.all())
    if adendas:
        elementos += _aviso_adendas(len(adendas), estilos)

    if informe.texto_generado:
        elementos += _seccion('DESCRIPCIÓN MACROSCÓPICA', [texto_seguro(informe.texto_generado)], estilos)

    if informe.descripcion_microscopica:
        elementos += _seccion('DESCRIPCIÓN MICROSCÓPICA', [texto_seguro(informe.descripcion_microscopica)], estilos)

    diagnosticos = list(informe.diagnosticos.all())
    if diagnosticos:
        elementos += _seccion('DIAGNÓSTICOS', [
            f'{d.orden}. {texto_seguro(d.descripcion)}'
            + (f' (CIE-10: {texto_seguro(d.codigo_cie10)})' if d.codigo_cie10 else '')
            for d in diagnosticos
        ], estilos)

    if informe.comentarios:
        elementos += _seccion('COMENTARIOS', [texto_seguro(informe.comentarios)], estilos)

    if informe.esta_finalizado:
        elementos += _firma(datos['firma'], estilos)

    if adendas:
        elementos += _adendas(adendas, estilos)

    # Pie de cada página, para identificar una hoja suelta. La hora es la de
    # settings.TIME_ZONE (America/Bogota), no la del servidor (auditoría M-10).
    generado = timezone.localtime().strftime('%d/%m/%Y %H:%M')
    antes = f'N.º de petición {informe.numero_peticion} · '
    if not informe.esta_finalizado:
        antes = f'{AVISO_BORRADOR} · {antes}'
    doc.build(elementos, canvasmaker=partial(CanvasNumerado, pie=(antes, f' · Generado el {generado}')))
    buffer.seek(0)
    return buffer
