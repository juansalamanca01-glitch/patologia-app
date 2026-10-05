# Informe v2, etapa 6: firma y finalización (docs/propuesta-informe-v2.md, 3.7 y 6.1;
# decisiones D-8 y D-10).

from django.db import migrations, models


def completar_finalizados(apps, schema_editor):
    """
    Los informes que ya estaban finalizados no tienen fecha de informe ni datos
    congelados. fecha_informe toma la fecha de la última modificación, que es la
    mejor aproximación disponible (después de finalizar ya no se podían editar), y
    datos_finalizacion se llena con los datos actuales. Se usa update() para no
    cambiar fecha_actualizacion (auto_now).

    Repite a propósito la forma de Informe.datos_para_congelar(): una migración no
    debe depender del código actual de los modelos, que puede cambiar después.
    """
    Informe = apps.get_model('informes', 'Informe')
    finalizados = Informe.objects.filter(estado='finalizado').select_related('paciente', 'eps', 'servicio', 'autor')
    for informe in finalizados:
        paciente = informe.paciente
        autor = informe.autor
        datos = {
            'paciente': None if paciente is None else {
                'id': paciente.id,
                'nombre_completo': f'{paciente.nombres} {paciente.apellidos}',
                'tipo_documento': paciente.tipo_documento,
                'numero_documento': paciente.numero_documento,
                'fecha_nacimiento': paciente.fecha_nacimiento.isoformat(),
                'sexo': paciente.sexo,
            },
            'eps_nombre': informe.eps.nombre if informe.eps else None,
            'servicio_nombre': informe.servicio.nombre if informe.servicio else None,
            'firma': {
                'nombre': autor.nombre_completo or autor.username,
                'especialidad': autor.especialidad,
                'registro_medico': autor.registro_medico,
            },
        }
        Informe.objects.filter(pk=informe.pk).update(
            fecha_informe=informe.fecha_actualizacion, datos_finalizacion=datos,
        )


def vaciar_finalizados(apps, schema_editor):
    """Reversa: los campos se eliminan, así que basta con dejarlos vacíos."""
    apps.get_model('informes', 'Informe').objects.update(fecha_informe=None, datos_finalizacion=None)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_registro_medico'),
        ('informes', '0009_contenido'),
    ]

    operations = [
        migrations.AddField(
            model_name='informe',
            name='datos_finalizacion',
            field=models.JSONField(blank=True, editable=False, null=True, verbose_name='Datos congelados al finalizar'),
        ),
        migrations.AddField(
            model_name='informe',
            name='fecha_informe',
            field=models.DateTimeField(blank=True, editable=False, null=True, verbose_name='Fecha de informe'),
        ),
        migrations.RunPython(completar_finalizados, vaciar_finalizados),
    ]
