# Decisión D-15: el encabezado del PDF se congela al finalizar, como los datos de D-10.

from django.db import migrations

# El único encabezado que existió antes de hacerlo configurable (respuesta P-9). Se
# escribe aquí, y no se lee de settings, para que el resultado no dependa del .env
# del equipo donde se ejecute la migración.
ENCABEZADO_DEMOSTRACION = {
    'nombre': 'PathoLab — Laboratorio de Patología (demostración)',
    'direccion': 'Santiago de Cali, Colombia',
    'telefono': '',
}


def congelar_encabezado(apps, schema_editor):
    """
    Los informes ya finalizados se imprimieron con el encabezado de demostración:
    se agrega a sus datos congelados. Los que ya lo tienen no se tocan. Se usa
    update() para no cambiar fecha_actualizacion (auto_now).
    """
    Informe = apps.get_model('informes', 'Informe')
    for informe in Informe.objects.filter(estado='finalizado', datos_finalizacion__isnull=False):
        datos = informe.datos_finalizacion
        if 'laboratorio' in datos:
            continue
        Informe.objects.filter(pk=informe.pk).update(
            datos_finalizacion={**datos, 'laboratorio': ENCABEZADO_DEMOSTRACION},
        )


def quitar_encabezado(apps, schema_editor):
    """Reversa: quita el encabezado congelado de los datos de cada informe."""
    Informe = apps.get_model('informes', 'Informe')
    for informe in Informe.objects.filter(datos_finalizacion__isnull=False):
        datos = informe.datos_finalizacion
        if 'laboratorio' in datos:
            datos = {clave: valor for clave, valor in datos.items() if clave != 'laboratorio'}
            Informe.objects.filter(pk=informe.pk).update(datos_finalizacion=datos)


class Migration(migrations.Migration):

    dependencies = [
        ('informes', '0011_adenda'),
    ]

    operations = [
        migrations.RunPython(congelar_encabezado, quitar_encabezado),
    ]
