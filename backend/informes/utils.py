"""
Generación de la descripción macroscópica y exportación del informe a PDF.
"""
import io
from datetime import datetime
from xml.sax.saxutils import escape

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

    # Tabla con los datos generales del informe
    meta_data = [
        ['Número de Caso:', informe.numero_caso],
        ['Fecha:', informe.fecha.strftime('%d/%m/%Y') if informe.fecha else ''],
        ['Patología:', informe.patologia.nombre],
        ['Tipo de Muestra:', informe.tipo_muestra or 'N/A'],
        ['Patólogo:', informe.autor.nombre_visible],
        ['Estado:', informe.get_estado_display()],
    ]

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

    elements.append(Spacer(1, 16))

    # Descripción generada
    if informe.texto_generado:
        elements.append(Paragraph('DESCRIPCIÓN MACROSCÓPICA', styles['Subtitulo']))
        elements.append(HRFlowable(width='100%', thickness=0.5, color=HexColor('#cbd5e0')))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(texto_seguro(informe.texto_generado), styles['CuerpoTexto']))

    # Notas
    if informe.notas:
        elements.append(Spacer(1, 16))
        elements.append(Paragraph('NOTAS ADICIONALES', styles['Subtitulo']))
        elements.append(HRFlowable(width='100%', thickness=0.5, color=HexColor('#cbd5e0')))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(texto_seguro(informe.notas), styles['CuerpoTexto']))

    # Pie de página
    elements.append(Spacer(1, 30))
    elements.append(HRFlowable(width='100%', thickness=1, color=HexColor('#2b6cb0')))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        f'Generado el {datetime.now().strftime("%d/%m/%Y %H:%M")} — '
        'Sistema de Patología Clínica',
        styles['PiePagina'],
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer
