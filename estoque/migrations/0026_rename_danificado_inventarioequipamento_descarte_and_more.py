# Generated by Django 5.2.4 on 2025-07-25 19:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('estoque', '0025_remove_inventarioequipamento_data_validacao_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='inventarioequipamento',
            old_name='danificado',
            new_name='descarte',
        ),
        migrations.RenameField(
            model_name='inventarioequipamento',
            old_name='falta',
            new_name='perda',
        ),
    ]
