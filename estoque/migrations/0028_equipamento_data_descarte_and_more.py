# Generated by Django 5.2.4 on 2025-07-26 21:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('estoque', '0027_rename_descarte_inventarioequipamento_avaria_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipamento',
            name='data_descarte',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='inventarioequipamento',
            name='validado',
            field=models.BooleanField(default=False),
        ),
    ]
