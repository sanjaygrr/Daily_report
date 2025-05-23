# Generated by Django 5.1.6 on 2025-04-10 04:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registros', '0002_alter_perfilusuario_empresa'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='empresa',
            name='cantidad_faenas',
        ),
        migrations.RemoveField(
            model_name='empresa',
            name='cantidad_maquinas',
        ),
        migrations.RemoveField(
            model_name='empresa',
            name='cantidad_usuarios',
        ),
        migrations.RemoveField(
            model_name='perfilusuario',
            name='cargo',
        ),
        migrations.AddField(
            model_name='empresa',
            name='max_faenas',
            field=models.PositiveIntegerField(default=0, verbose_name='Máximo de Faenas Permitidas'),
        ),
        migrations.AddField(
            model_name='empresa',
            name='max_maquinas',
            field=models.PositiveIntegerField(default=0, verbose_name='Máximo de Máquinas Permitidas'),
        ),
        migrations.AddField(
            model_name='empresa',
            name='max_usuarios',
            field=models.PositiveIntegerField(default=0, verbose_name='Máximo de Usuarios Permitidos'),
        ),
    ]
