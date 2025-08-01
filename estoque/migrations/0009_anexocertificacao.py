# Generated by Django 5.2.4 on 2025-07-11 20:02

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('estoque', '0008_equipamento_anexo_certificacao_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnexoCertificacao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('arquivo', models.FileField(upload_to='certificacoes/')),
                ('descricao', models.CharField(blank=True, max_length=255)),
                ('equipamento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='anexos', to='estoque.equipamento')),
            ],
        ),
    ]
