"""
Utility functions for macroscopic description generation and PDF export.
"""
import io
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY


# ── Macroscopic description generator ────────────────────────────
def generar_descripcion_macroscopica(patologia, datos: dict) -> str:
    """
    Build a macroscopic description paragraph from the pathology type
    and the form data entered by the pathologist.
    """
    nombre_patologia = patologia.nombre
    partes = [f"Se recibe espécimen para estudio de {nombre_patologia}."]

    # Map common field groups to natural-language fragments
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

    # Include any extra fields not in the map
    campos_mapeados = set(mapeo.keys())
    for campo, valor in datos.items():
        if campo not in campos_mapeados and valor and str(valor).strip():
            label = campo.replace('_', ' ').capitalize()
            partes.append(f'{label}: {valor}.')

    partes.append(
        'Se procesa el material y se remite para estudio histopatológico.'
    )

    return ' '.join(partes)


# ── PDF export ───────────────────────────────────────────────────
def generar_pdf_informe(informe) -> io.BytesIO:
    """Generate a PDF report and return the bytes buffer."""
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

    # Custom styles
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

    # Header
    elements.append(Paragraph('INFORME DE PATOLOGÍA CLÍNICA', styles['TituloInforme']))
    elements.append(HRFlowable(width='100%', thickness=2, color=HexColor('#2b6cb0')))
    elements.append(Spacer(1, 12))

    # Report metadata table
    meta_data = [
        ['Número de Caso:', informe.numero_caso],
        ['Fecha:', informe.fecha.strftime('%d/%m/%Y') if informe.fecha else ''],
        ['Patología:', informe.patologia.nombre],
        ['Tipo de Muestra:', informe.tipo_muestra or 'N/A'],
        ['Patólogo:', informe.autor.nombre_completo or informe.autor.username],
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

    # Form data
    if informe.datos_ingresados:
        elements.append(Paragraph('DATOS CLÍNICOS', styles['Subtitulo']))
        elements.append(HRFlowable(width='100%', thickness=0.5, color=HexColor('#cbd5e0')))
        elements.append(Spacer(1, 6))

        for campo, valor in informe.datos_ingresados.items():
            if valor and str(valor).strip():
                label = campo.replace('_', ' ').capitalize()
                elements.append(Paragraph(
                    f'<b>{label}:</b> {valor}',
                    styles['CuerpoTexto'],
                ))

    elements.append(Spacer(1, 16))

    # Generated description
    if informe.texto_generado:
        elements.append(Paragraph('DESCRIPCIÓN MACROSCÓPICA', styles['Subtitulo']))
        elements.append(HRFlowable(width='100%', thickness=0.5, color=HexColor('#cbd5e0')))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(informe.texto_generado, styles['CuerpoTexto']))

    # Notes
    if informe.notas:
        elements.append(Spacer(1, 16))
        elements.append(Paragraph('NOTAS ADICIONALES', styles['Subtitulo']))
        elements.append(HRFlowable(width='100%', thickness=0.5, color=HexColor('#cbd5e0')))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(informe.notas, styles['CuerpoTexto']))

    # Footer
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
