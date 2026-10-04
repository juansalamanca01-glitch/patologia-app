from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Etapa 1 del informe v2 (decisión D-7): contador de números de petición y
    campos nuevos. numero_peticion se crea vacío; la migración 0005 lo llena y la
    0006 lo vuelve obligatorio y único.
    """

    dependencies = [
        ('informes', '0003_quitar_campos_requeridos'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConsecutivoPeticion',
            fields=[
                ('anio', models.PositiveIntegerField(primary_key=True, serialize=False, verbose_name='Año')),
                ('ultimo', models.PositiveIntegerField(default=0, verbose_name='Último consecutivo')),
            ],
            options={
                'verbose_name': 'Consecutivo de petición',
                'verbose_name_plural': 'Consecutivos de petición',
            },
        ),
        migrations.AddField(
            model_name='informe',
            name='numero_peticion',
            field=models.CharField(editable=False, max_length=20, null=True, verbose_name='Número de petición'),
        ),
        migrations.AddField(
            model_name='informe',
            name='numero_orden_externa',
            field=models.CharField(
                blank=True, default='', max_length=50,
                help_text='Número de orden de la institución remitente (opcional).',
                verbose_name='Número de orden externa',
            ),
            preserve_default=False,
        ),
    ]
