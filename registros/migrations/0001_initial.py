# Generated by Django 5.1.6 on 2025-04-09 02:41

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Empresa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255, unique=True, verbose_name='Nombre de la empresa')),
                ('rut', models.CharField(max_length=20, unique=True, verbose_name='RUT')),
                ('direccion', models.CharField(max_length=255, verbose_name='Dirección')),
                ('logo', models.ImageField(blank=True, null=True, upload_to='empresas/logos/', verbose_name='Logo')),
                ('correo_electronico', models.EmailField(max_length=254, unique=True, verbose_name='Correo electrónico')),
                ('numero_telefono', models.CharField(blank=True, max_length=20, null=True, verbose_name='Teléfono')),
                ('cantidad_maquinas', models.PositiveIntegerField(default=0, editable=False, verbose_name='Máquinas')),
                ('cantidad_faenas', models.PositiveIntegerField(default=0, editable=False, verbose_name='Faenas')),
                ('cantidad_usuarios', models.PositiveIntegerField(default=0, editable=False, verbose_name='Usuarios')),
                ('fecha_creacion', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Fecha de creación')),
                ('activa', models.BooleanField(default=True, verbose_name='Activa')),
                ('administrador', models.ForeignKey(blank=True, limit_choices_to={'groups__name': 'Admin'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='empresas_administradas', to=settings.AUTH_USER_MODEL, verbose_name='Administrador asignado')),
            ],
            options={
                'verbose_name': 'Empresa',
                'verbose_name_plural': 'Empresas',
                'ordering': ['nombre'],
                'permissions': [('gestion_empresa', 'Puede gestionar completamente la empresa')],
            },
        ),
        migrations.CreateModel(
            name='Faena',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(help_text='Nombre descriptivo de la faena', max_length=100, verbose_name='Nombre de la faena')),
                ('ubicacion', models.CharField(default='Sin ubicación especificada', help_text='Ubicación física de la faena', max_length=255, verbose_name='Ubicación')),
                ('descripcion', models.TextField(blank=True, help_text='Detalles adicionales sobre la faena', null=True, verbose_name='Descripción')),
                ('fecha_inicio', models.DateField(default=django.utils.timezone.now, help_text='Fecha en que comienza la faena', verbose_name='Fecha de inicio')),
                ('fecha_termino_estimada', models.DateField(blank=True, help_text='Fecha estimada de finalización', null=True, verbose_name='Fecha término estimada')),
                ('fecha_termino_real', models.DateField(blank=True, help_text='Fecha real de finalización', null=True, verbose_name='Fecha término real')),
                ('estado', models.CharField(choices=[('activa', 'Activa'), ('pausada', 'Pausada'), ('completada', 'Completada'), ('cancelada', 'Cancelada')], default='activa', help_text='Estado actual de la faena', max_length=20, verbose_name='Estado')),
                ('activa', models.BooleanField(default=True, help_text='Indica si la faena está activa en el sistema', verbose_name='Activa')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True, verbose_name='Fecha de actualización')),
                ('empresa', models.ForeignKey(help_text='Empresa a la que pertenece esta faena', on_delete=django.db.models.deletion.CASCADE, related_name='faenas', to='registros.empresa', verbose_name='Empresa')),
                ('responsable', models.ForeignKey(blank=True, help_text='Supervisor responsable de la faena', limit_choices_to={'groups__name': 'Supervisor'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='faenas_responsable', to=settings.AUTH_USER_MODEL, verbose_name='Responsable')),
            ],
            options={
                'verbose_name': 'Faena',
                'verbose_name_plural': 'Faenas',
                'ordering': ['-fecha_inicio', 'nombre'],
                'permissions': [('gestion_faena', 'Puede gestionar completamente las faenas')],
            },
        ),
        migrations.CreateModel(
            name='Maquina',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, verbose_name='Nombre de la máquina')),
                ('modelo', models.CharField(blank=True, max_length=100, null=True, verbose_name='Modelo')),
                ('numero_serie', models.CharField(blank=True, max_length=100, null=True, unique=True, verbose_name='Número de serie')),
                ('fecha_adquisicion', models.DateField(blank=True, null=True, verbose_name='Fecha de adquisición')),
                ('ultimo_mantenimiento', models.DateField(blank=True, null=True, verbose_name='Último mantenimiento')),
                ('proximo_mantenimiento', models.DateField(blank=True, null=True, verbose_name='Próximo mantenimiento')),
                ('estado', models.CharField(choices=[('operativa', 'Operativa'), ('mantenimiento', 'En mantenimiento'), ('reparacion', 'En reparación'), ('baja', 'Dada de baja')], default='operativa', max_length=20, verbose_name='Estado')),
                ('activa', models.BooleanField(default=True, verbose_name='Activa')),
                ('imagen', models.ImageField(blank=True, null=True, upload_to='maquinas/', verbose_name='Imagen')),
                ('horometro_actual', models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Horómetro actual')),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='maquinas', to='registros.empresa', verbose_name='Empresa')),
            ],
            options={
                'verbose_name': 'Máquina',
                'verbose_name_plural': 'Máquinas',
                'ordering': ['nombre'],
                'permissions': [('gestion_maquina', 'Puede gestionar completamente las máquinas')],
            },
        ),
        migrations.CreateModel(
            name='PerfilUsuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cargo', models.CharField(blank=True, max_length=100, null=True, verbose_name='Cargo')),
                ('telefono', models.CharField(blank=True, max_length=20, null=True, verbose_name='Teléfono')),
                ('fecha_ingreso', models.DateField(default=django.utils.timezone.now, verbose_name='Fecha de ingreso')),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usuarios', to='registros.empresa', verbose_name='Empresa')),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='perfil', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Perfil de Usuario',
                'verbose_name_plural': 'Perfiles de Usuarios',
            },
        ),
        migrations.CreateModel(
            name='Trabajo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField(default=django.utils.timezone.now, verbose_name='Fecha del trabajo')),
                ('trabajo', models.CharField(max_length=200, verbose_name='Descripción del trabajo')),
                ('horometro_inicial', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Horómetro inicial')),
                ('horometro_final', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Horómetro final')),
                ('total_horas', models.DecimalField(blank=True, decimal_places=2, editable=False, max_digits=12, null=True, verbose_name='Total de horas')),
                ('petroleo_litros', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Litros de petróleo')),
                ('aceite_tipo', models.CharField(max_length=100, verbose_name='Tipo de aceite')),
                ('aceite_litros', models.DecimalField(decimal_places=2, max_digits=6, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Litros de aceite')),
                ('observaciones', models.TextField(blank=True, null=True, verbose_name='Observaciones')),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente'), ('en_proceso', 'En proceso'), ('completado', 'Completado'), ('rechazado', 'Rechazado')], default='pendiente', max_length=20, verbose_name='Estado')),
                ('tipo_medida', models.CharField(choices=[('Horas', 'Horas'), ('Kilómetros', 'Kilómetros')], default='Horas', max_length=10, verbose_name='Tipo de medida')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True, verbose_name='Fecha de actualización')),
                ('creado_por', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='trabajos_creados', to=settings.AUTH_USER_MODEL, verbose_name='Creado por')),
                ('empresa', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='trabajos', to='registros.empresa', verbose_name='Empresa')),
                ('faena', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='trabajos', to='registros.faena', verbose_name='Faena')),
                ('maquina', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='trabajos', to='registros.maquina', verbose_name='Máquina')),
                ('supervisor', models.ForeignKey(limit_choices_to={'groups__name': 'Supervisor'}, on_delete=django.db.models.deletion.PROTECT, related_name='trabajos_supervisados', to=settings.AUTH_USER_MODEL, verbose_name='Supervisor')),
                ('trabajador', models.ForeignKey(limit_choices_to={'groups__name': 'Trabajador'}, on_delete=django.db.models.deletion.PROTECT, related_name='trabajos_realizados', to=settings.AUTH_USER_MODEL, verbose_name='Trabajador')),
            ],
            options={
                'verbose_name': 'Trabajo',
                'verbose_name_plural': 'Trabajos',
                'ordering': ['-fecha', 'faena'],
                'permissions': [('aprobar_trabajo', 'Puede aprobar trabajos'), ('rechazar_trabajo', 'Puede rechazar trabajos')],
            },
        ),
        migrations.AddConstraint(
            model_name='faena',
            constraint=models.UniqueConstraint(fields=('nombre', 'empresa'), name='unique_nombre_faena_por_empresa'),
        ),
        migrations.AlterUniqueTogether(
            name='maquina',
            unique_together={('nombre', 'empresa')},
        ),
    ]
