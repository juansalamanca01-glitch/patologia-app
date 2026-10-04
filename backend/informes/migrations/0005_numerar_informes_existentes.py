from django.db import migrations
from django.utils import timezone


def numerar_informes(apps, schema_editor):
    """
    Asigna P-AÑO-NNNNN a los informes que ya existían, en orden de creación y por
    año de creación en la hora de Bogotá (TIME_ZONE), y deja cada contador en el
    último número usado para que los informes nuevos continúen la numeración.
    """
    Informe = apps.get_model('informes', 'Informe')
    ConsecutivoPeticion = apps.get_model('informes', 'ConsecutivoPeticion')

    ultimos = {}
    for informe in Informe.objects.order_by('fecha_creacion', 'id'):
        anio = timezone.localtime(informe.fecha_creacion).year
        ultimos[anio] = ultimos.get(anio, 0) + 1
        informe.numero_peticion = f'P-{anio}-{ultimos[anio]:05d}'
        informe.save(update_fields=['numero_peticion'])

    for anio, ultimo in ultimos.items():
        ConsecutivoPeticion.objects.update_or_create(anio=anio, defaults={'ultimo': ultimo})


def quitar_numeracion(apps, schema_editor):
    apps.get_model('informes', 'Informe').objects.update(numero_peticion=None)
    apps.get_model('informes', 'ConsecutivoPeticion').objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('informes', '0004_numero_peticion'),
    ]

    operations = [
        migrations.RunPython(numerar_informes, quitar_numeracion),
    ]
