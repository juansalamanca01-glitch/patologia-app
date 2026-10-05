# Informe v2, etapa 6: registro médico del usuario, que firma los informes (decisión D-8).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='registro_medico',
            field=models.CharField(blank=True, max_length=30, verbose_name='Registro médico'),
        ),
    ]
