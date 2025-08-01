# Generated by Django 5.2.4 on 2025-07-14 20:36

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('estoque', '0012_remove_equipamento_anexo_certificacao_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Agendamento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_agendamento', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('nome_solicitante', models.CharField(max_length=100)),
                ('matricula', models.CharField(max_length=20)),
                ('setor_solicitante', models.CharField(max_length=100)),
                ('local_uso', models.CharField(max_length=100)),
                ('tipo_operacao', models.TextField()),
                ('data_hora_agendamento', models.DateTimeField()),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='PecaAgendada',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agendamento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pecas_agendadas', to='estoque.agendamento')),
                ('equipamento', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='estoque.equipamento')),
            ],
        ),
    ]
