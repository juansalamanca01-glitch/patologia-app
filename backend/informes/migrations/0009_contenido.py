# Informe v2, etapa 5: contenido del informe (docs/propuesta-informe-v2.md, 3.4 y 3.6).
# `notas` se renombra a `comentarios` (P-5) con RenameField, que conserva lo escrito.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('informes', '0008_datos_solicitud'),
    ]

    operations = [
        migrations.RenameField(
            model_name='informe',
            old_name='notas',
            new_name='comentarios',
        ),
        migrations.AlterField(
            model_name='informe',
            name='comentarios',
            field=models.TextField(blank=True, verbose_name='Comentarios'),
        ),
        migrations.AddField(
            model_name='informe',
            name='descripcion_microscopica',
            field=models.TextField(blank=True, verbose_name='Descripción microscópica'),
        ),
        migrations.CreateModel(
            name='Diagnostico',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('orden', models.PositiveSmallIntegerField(verbose_name='Orden')),
                ('descripcion', models.TextField(verbose_name='Descripción')),
                ('codigo_cie10', models.CharField(blank=True, max_length=7, verbose_name='Código CIE-10')),
                ('informe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='diagnosticos', to='informes.informe', verbose_name='Informe')),
            ],
            options={
                'verbose_name': 'Diagnóstico',
                'verbose_name_plural': 'Diagnósticos',
                'ordering': ['informe', 'orden'],
            },
        ),
        migrations.AddConstraint(
            model_name='diagnostico',
            constraint=models.UniqueConstraint(fields=('informe', 'orden'), name='diagnostico_orden_unico'),
        ),
    ]
