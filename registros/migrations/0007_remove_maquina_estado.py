# Generated by Django 5.1.6 on 2025-04-16 17:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('registros', '0006_alter_trabajo_aceite_litros_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='maquina',
            name='estado',
        ),
    ]
