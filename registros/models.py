# Archivo: registros/models.py
from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

class Empresa(models.Model):
    nombre = models.CharField(max_length=255, unique=True, verbose_name="Nombre de la empresa")
    rut = models.CharField(max_length=20, unique=True, verbose_name="RUT")
    direccion = models.CharField(max_length=255, verbose_name="Dirección")
    logo = models.ImageField(upload_to='empresas/logos/', blank=True, null=True, verbose_name="Logo")
    correo_electronico = models.EmailField(unique=True, verbose_name="Correo electrónico")
    numero_telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    max_faenas = models.PositiveIntegerField(default=0, verbose_name="Máximo de Faenas Permitidas")
    max_usuarios = models.PositiveIntegerField(default=0, verbose_name="Máximo de Usuarios Permitidos")
    max_maquinas = models.PositiveIntegerField(default=0, verbose_name="Máximo de Máquinas Permitidas")
    administrador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='empresas_administradas',
        limit_choices_to={'groups__name': 'Admin'}, # Aseguramos que solo los del grupo Admin puedan ser administradores
        verbose_name="Administrador asignado"
    )
    fecha_creacion = models.DateTimeField(default=timezone.now, verbose_name="Fecha de creación")
    activa = models.BooleanField(default=True, verbose_name="Activa")

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ['nombre']
        permissions = [
            ("gestion_empresa", "Puede gestionar completamente la empresa"),
        ]

    def __str__(self):
        return self.nombre

    def clean(self):
        if self.administrador and not self.administrador.groups.filter(name='Admin').exists():
            raise ValidationError("El administrador asignado debe pertenecer al grupo Admin")

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.strip()
        self.rut = self.rut.strip()
        super().save(*args, **kwargs)

    @property
    def maquinas_activas(self):
        return self.maquinas.filter(activa=True).count()

    @property
    def faenas_activas(self):
        return self.faenas.filter(activa=True).count()

    def actualizar_contadores(self):
        self.cantidad_maquinas = self.maquinas.count()
        self.cantidad_faenas = self.faenas.count()
        self.cantidad_usuarios = User.objects.filter(
            models.Q(groups__name='Trabajador') | 
            models.Q(groups__name='Supervisor'),
            perfil__empresa=self
        ).distinct().count()
        self.save(update_fields=['cantidad_maquinas', 'cantidad_faenas', 'cantidad_usuarios'])


class PerfilUsuario(models.Model): 
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    empresa = models.ForeignKey(Empresa, null=True, blank=True, on_delete=models.SET_NULL, related_name='usuarios')
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    fecha_ingreso = models.DateField(default=timezone.now, verbose_name="Fecha de ingreso")
    # Eliminamos el campo es_administrador
    
    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuarios"

    def __str__(self):
        return f"{self.usuario.username} - {self.empresa.nombre if self.empresa else 'Sin empresa'}"

class Maquina(models.Model):
    ESTADO_CHOICES = [
        ('operativa', 'Operativa'),
        ('mantenimiento', 'En mantenimiento'),
        ('reparacion', 'En reparación'),
        ('baja', 'Dada de baja'),
    ]

    nombre = models.CharField(max_length=100, verbose_name="Nombre de la máquina")
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='maquinas',
        verbose_name="Empresa"
    )
    modelo = models.CharField(max_length=100, blank=True, null=True, verbose_name="Modelo")
    numero_serie = models.CharField(max_length=100, blank=True, null=True, unique=True, verbose_name="Número de serie")
    fecha_adquisicion = models.DateField(blank=True, null=True, verbose_name="Fecha de adquisición")
    ultimo_mantenimiento = models.DateField(blank=True, null=True, verbose_name="Último mantenimiento")
    proximo_mantenimiento = models.DateField(blank=True, null=True, verbose_name="Próximo mantenimiento")
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='operativa',
        verbose_name="Estado"
    )
    activa = models.BooleanField(default=True, verbose_name="Activa")
    imagen = models.ImageField(upload_to='maquinas/', blank=True, null=True, verbose_name="Imagen")
    horometro_actual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Horómetro actual"
    )

    class Meta:
        verbose_name = "Máquina"
        verbose_name_plural = "Máquinas"
        unique_together = ('nombre', 'empresa')
        ordering = ['nombre']
        permissions = [
            ("gestion_maquina", "Puede gestionar completamente las máquinas"),
        ]

    def __str__(self):
        return f"{self.nombre} - {self.empresa.nombre}"

    def clean(self):
        if self.proximo_mantenimiento and self.ultimo_mantenimiento:
            if self.proximo_mantenimiento <= self.ultimo_mantenimiento:
                raise ValidationError("La fecha de próximo mantenimiento debe ser posterior al último mantenimiento")

    def save(self, *args, **kwargs):
        is_new = not self.pk
        super().save(*args, **kwargs)
        if is_new:
            self.empresa.actualizar_contadores()


class Faena(models.Model):
    class Estado(models.TextChoices):
        ACTIVA = 'activa', _('Activa')
        PAUSADA = 'pausada', _('Pausada')
        COMPLETADA = 'completada', _('Completada')
        CANCELADA = 'cancelada', _('Cancelada')

    nombre = models.CharField(
        max_length=100,
        verbose_name=_("Nombre de la faena"),
        help_text=_("Nombre descriptivo de la faena")
    )
    
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='faenas',
        verbose_name=_("Empresa"),
        help_text=_("Empresa a la que pertenece esta faena")
    )
    
    ubicacion = models.CharField(
        max_length=255,
        verbose_name=_("Ubicación"),
        help_text=_("Ubicación física de la faena"),
        default="Sin ubicación especificada"
    )
    
    descripcion = models.TextField(
        verbose_name=_("Descripción"),
        help_text=_("Detalles adicionales sobre la faena"),
        blank=True,
        null=True
    )
    
    fecha_inicio = models.DateField(
        verbose_name=_("Fecha de inicio"),
        help_text=_("Fecha en que comienza la faena"),
        default=timezone.now
    )
    
    fecha_termino_estimada = models.DateField(
        verbose_name=_("Fecha término estimada"),
        help_text=_("Fecha estimada de finalización"),
        blank=True,
        null=True
    )
    
    fecha_termino_real = models.DateField(
        verbose_name=_("Fecha término real"),
        help_text=_("Fecha real de finalización"),
        blank=True,
        null=True
    )
    
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.ACTIVA,
        verbose_name=_("Estado"),
        help_text=_("Estado actual de la faena")
    )
    
    activa = models.BooleanField(
        default=True,
        verbose_name=_("Activa"),
        help_text=_("Indica si la faena está activa en el sistema")
    )
    
    responsable = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'groups__name': 'Supervisor'},
        related_name='faenas_responsable',
        verbose_name=_("Responsable"),
        help_text=_("Supervisor responsable de la faena")
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Fecha de creación")
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Fecha de actualización")
    )

    class Meta:
        verbose_name = _("Faena")
        verbose_name_plural = _("Faenas")
        constraints = [
            models.UniqueConstraint(
                fields=['nombre', 'empresa'],
                name='unique_nombre_faena_por_empresa'
            )
        ]
        ordering = ['-fecha_inicio', 'nombre']
        permissions = [
            ("gestion_faena", _("Puede gestionar completamente las faenas")),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.empresa.nombre})"

    def clean(self):
        errors = {}
        
        # Validación de fechas
        if self.fecha_termino_real and self.fecha_inicio:
            if self.fecha_termino_real < self.fecha_inicio:
                errors['fecha_termino_real'] = _("La fecha de término real no puede ser anterior a la fecha de inicio")
        
        if self.fecha_termino_estimada and self.fecha_inicio:
            if self.fecha_termino_estimada < self.fecha_inicio:
                errors['fecha_termino_estimada'] = _("La fecha de término estimada no puede ser anterior a la fecha de inicio")
        
        # Validar que el responsable pertenezca a la misma empresa
        if self.responsable and hasattr(self.responsable, 'perfil'):
            if self.responsable.perfil.empresa != self.empresa:
                errors['responsable'] = _("El responsable debe pertenecer a la misma empresa")
        
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Lógica de estado
        if self.fecha_termino_real and self.estado != self.Estado.COMPLETADA:
            self.estado = self.Estado.COMPLETADA
        
        is_new = not self.pk
        super().save(*args, **kwargs)
        
        # Actualización de contadores para nueva faena
        if is_new:
            self.empresa.actualizar_contadores()



class Trabajo(models.Model):
    TIPO_MEDIDA_CHOICES = [
        ('Horas', 'Horas'),
        ('Kilómetros', 'Kilómetros'),
    ]

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En proceso'),
        ('completado', 'Completado'),
        ('rechazado', 'Rechazado'),
    ]

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='trabajos',
        editable=False,
        verbose_name="Empresa"
    )
    faena = models.ForeignKey(
        Faena,
        on_delete=models.PROTECT,
        related_name='trabajos',
        verbose_name="Faena"
    )
    maquina = models.ForeignKey(
        Maquina,
        on_delete=models.PROTECT,
        related_name='trabajos',
        verbose_name="Máquina"
    )
    fecha = models.DateField(default=timezone.now, verbose_name="Fecha del trabajo")
    trabajo = models.CharField(max_length=200, verbose_name="Descripción del trabajo")
    horometro_inicial = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Horómetro inicial"
    )
    horometro_final = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Horómetro final"
    )
    total_horas = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        editable=False,
        verbose_name="Total de horas"
    )
    petroleo_litros = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Litros de petróleo"
    )
    aceite_tipo = models.CharField(max_length=100, verbose_name="Tipo de aceite")
    aceite_litros = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Litros de aceite"
    )
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    supervisor = models.ForeignKey(
        User,
        related_name='trabajos_supervisados',
        on_delete=models.PROTECT,
        limit_choices_to={'groups__name': 'Supervisor'},
        verbose_name="Supervisor"
    )
    trabajador = models.ForeignKey(
        User,
        related_name='trabajos_realizados',
        on_delete=models.PROTECT,
        limit_choices_to={'groups__name': 'Trabajador'},
        verbose_name="Trabajador"
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente',
        verbose_name="Estado"
    )
    tipo_medida = models.CharField(
        max_length=10,
        choices=TIPO_MEDIDA_CHOICES,
        default='Horas',
        verbose_name="Tipo de medida"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")
    creado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='trabajos_creados',
        verbose_name="Creado por"
    )

    class Meta:
        verbose_name = "Trabajo"
        verbose_name_plural = "Trabajos"
        ordering = ['-fecha', 'faena']
        permissions = [
            ("aprobar_trabajo", "Puede aprobar trabajos"),
            ("rechazar_trabajo", "Puede rechazar trabajos"),
        ]

    def __str__(self):
        return f"{self.faena.nombre} - {self.maquina.nombre} - {self.fecha}"

    def clean(self):
        errors = {}
        
        # Validar que faena y máquina pertenezcan a la misma empresa
        if self.faena.empresa != self.maquina.empresa:
            errors['maquina'] = "La faena y la máquina deben pertenecer a la misma empresa"
        
        # Asegurarse que el horómetro final sea mayor que el inicial
        if self.horometro_final <= self.horometro_inicial:
            errors['horometro_final'] = "El horómetro final debe ser mayor que el inicial"
        
        # Validar que trabajador y supervisor sean diferentes
        if self.trabajador == self.supervisor:
            errors['supervisor'] = "El trabajador y el supervisor no pueden ser la misma persona"
        
        # Validar que el trabajador y supervisor pertenezcan a la empresa
        if hasattr(self.trabajador, 'perfil') and self.faena.empresa != self.trabajador.perfil.empresa:
            errors['trabajador'] = "El trabajador debe pertenecer a la misma empresa que la faena"
            
        if hasattr(self.supervisor, 'perfil') and self.faena.empresa != self.supervisor.perfil.empresa:
            errors['supervisor'] = "El supervisor debe pertenecer a la misma empresa que la faena"
        
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Calcular total de horas automáticamente
        self.total_horas = self.horometro_final - self.horometro_inicial
        
        # Actualizar horómetro actual de la máquina
        if self.estado == 'completado' and self.horometro_final > self.maquina.horometro_actual:
            self.maquina.horometro_actual = self.horometro_final
            self.maquina.save()
        
        # Asignar empresa automáticamente de la faena
        self.empresa = self.faena.empresa
            
        super().save(*args, **kwargs)

