from django.db import migrations, models


def numero_caso_desde_peticion(apps, schema_editor):
    """Solo al deshacer la migración: numero_caso vuelve con el número de petición."""
    Informe = apps.get_model('informes', 'Informe')
    for informe in Informe.objects.all():
        informe.numero_caso = informe.numero_peticion
        informe.save(update_fields=['numero_caso'])


class Migration(migrations.Migration):
    """
    numero_peticion pasa a ser obligatorio y único, y se elimina numero_caso
    (decisión D-7, respuesta P-1 del usuario). Antes de eliminarlo, numero_caso
    deja de ser obligatorio y único: así, al deshacer la migración, la columna se
    puede volver a crear vacía y llenarla con el número de petición.
    """

    dependencies = [
        ('informes', '0005_numerar_informes_existentes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='informe',
            name='numero_peticion',
            field=models.CharField(editable=False, max_length=20, unique=True, verbose_name='Número de petición'),
        ),
        migrations.AlterField(
            model_name='informe',
            name='numero_caso',
            field=models.CharField(max_length=50, null=True, verbose_name='Número de caso'),
        ),
        migrations.RunPython(migrations.RunPython.noop, numero_caso_desde_peticion),
        migrations.RemoveField(
            model_name='informe',
            name='numero_caso',
        ),
    ]
