"""
Generación de la descripción macroscópica y exportación del informe a PDF.
"""
import io
from xml.sax.saxutils import escape

from django.utils import timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY


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
def generar_pdf_informe(informe) -> io.BytesIO:
    """Genera el PDF del informe y lo devuelve en un buffer de bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    # Estilos propios
    styles.add(ParagraphStyle(
        'TituloInforme',
        parent=styles['Title'],
        fontSize=18,
        textColor=HexColor('#1a365d'),
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        'Subtitulo',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=HexColor('#2d3748'),
        spaceBefore=12,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        'CuerpoTexto',
        parent=styles['BodyText'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        leading=14,
    ))
    styles.add(ParagraphStyle(
        'PiePagina',
        parent=styles['Normal'],
        fontSize=8,
        textColor=HexColor('#718096'),
        alignment=TA_CENTER,
    ))

    elements = []

    # Encabezado
    elements.append(Paragraph('INFORME DE PATOLOGÍA CLÍNICA', styles['TituloInforme']))
    elements.append(HRFlowable(width='100%', thickness=2, color=HexColor('#2b6cb0')))
    elements.append(Spacer(1, 12))

    # Tabla con los datos generales del informe. La firma de un informe finalizado
    # sale de los datos congelados (D-10); la estructura completa llega en la etapa 7.
    firma = informe.datos_impresos()['firma']
    meta_data = [
        ['N.º de petición:', informe.numero_peticion],
        ['Fecha:', informe.fecha.strftime('%d/%m/%Y') if informe.fecha else ''],
        ['Patología:', informe.patologia.nombre],
        ['Tipo de Muestra:', informe.tipo_muestra or 'N/A'],
        ['Patólogo:', firma['nombre']],
        ['Estado:', informe.get_estado_display()],
    ]
    if firma['registro_medico']:
        meta_data.insert(5, ['Registro médico:', firma['registro_medico']])
    if informe.fecha_informe:
        meta_data.append(['Fecha de informe:', timezone.localtime(informe.fecha_informe).strftime('%d/%m/%Y %H:%M')])
    if informe.numero_orden_externa:
        meta_data.insert(1, ['Orden externa:', informe.numero_orden_externa])

    meta_table = Table(meta_data, colWidths=[3.5 * cm, 13 * cm])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#2d3748')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 16))

    # Datos clínicos del formulario
    if informe.datos_ingresados:
        elements.append(Paragraph('DATOS CLÍNICOS', styles['Subtitulo']))
        elements.append(HRFlowable(width='100%', thickness=0.5, color=HexColor('#cbd5e0')))
        elements.append(Spacer(1, 6))

        for campo, valor in informe.datos_ingresados.items():
            if valor and str(valor).strip():
                label = campo.replace('_', ' ').capitalize()
                elements.append(Paragraph(
                    f'<b>{texto_seguro(label)}:</b> {texto_seguro(valor)}',
                    styles['CuerpoTexto'],
                ))

    def seccion(titulo, parrafos):
        """Título con su línea y los párrafos, ya escapados con texto_seguro (I-3)."""
        elements.append(Spacer(1, 16))
        elements.append(Paragraph(titulo, styles['Subtitulo']))
        elements.append(HRFlowable(width='100%', thickness=0.5, color=HexColor('#cbd5e0')))
        elements.append(Spacer(1, 6))
        for parrafo in parrafos:
            elements.append(Paragraph(parrafo, styles['CuerpoTexto']))

    # Contenido en el orden del informe real (informe v2, etapa 5). La estructura
    # completa del PDF (encabezado, firma, numeración de páginas) llega en la etapa 7.
    if informe.texto_generado:
        seccion('DESCRIPCIÓN MACROSCÓPICA', [texto_seguro(informe.texto_generado)])

    if informe.descripcion_microscopica:
        seccion('DESCRIPCIÓN MICROSCÓPICA', [texto_seguro(informe.descripcion_microscopica)])

    diagnosticos = list(informe.diagnosticos.all())
    if diagnosticos:
        seccion('DIAGNÓSTICOS', [
            f'{d.orden}. {texto_seguro(d.descripcion)}'
            + (f' (CIE-10: {texto_seguro(d.codigo_cie10)})' if d.codigo_cie10 else '')
            for d in diagnosticos
        ])

    if informe.comentarios:
        seccion('COMENTARIOS', [texto_seguro(informe.comentarios)])

    # Pie de página
    elements.append(Spacer(1, 30))
    elements.append(HRFlowable(width='100%', thickness=1, color=HexColor('#2b6cb0')))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        # Hora en la zona de settings.TIME_ZONE (America/Bogota), no la del servidor (auditoría M-10).
        f'Generado el {timezone.localtime().strftime("%d/%m/%Y %H:%M")} — '
        'Sistema de Patología Clínica',
        styles['PiePagina'],
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer
