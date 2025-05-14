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
    
    @property
    def cantidad_maquinas(self):
        """Propiedad que reemplaza al campo eliminado"""
        return self.maquinas.count()
    
    @property
    def cantidad_faenas(self):
        """Propiedad que reemplaza al campo eliminado"""
        return self.faenas.count()
    
    @property
    def cantidad_usuarios(self):
        """Propiedad que reemplaza al campo eliminado"""
        return User.objects.filter(
            models.Q(groups__name='Trabajador') | 
            models.Q(groups__name='Supervisor'),
            perfil__empresa=self
        ).distinct().count()

    def actualizar_contadores(self):
        """
        Este método ahora solo cuenta pero no actualiza campos que ya no existen.
        """
        # Ya no se actualizan los campos en la base de datos, 
        # pues fueron eliminados en una migración anterior
        
        # Solo para fines de registro o depuración
        maquinas_count = self.maquinas.count()
        faenas_count = self.faenas.count()
        usuarios_count = User.objects.filter(
            models.Q(groups__name='Trabajador') | 
            models.Q(groups__name='Supervisor'),
            perfil__empresa=self
        ).distinct().count()
        
        # Se puede hacer un print() para debugging pero no se requiere guardar
        # print(f"Empresa {self.nombre}: {maquinas_count} máquinas, {faenas_count} faenas, {usuarios_count} usuarios")
        
        # Ya NO se actualiza la BD con estos contadores


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
        modelo_str = f" | Modelo: {self.modelo}" if self.modelo else ""
        serie_str = f" | Serie: {self.numero_serie}" if self.numero_serie else ""
        return f"{self.nombre}{modelo_str}{serie_str} - {self.empresa.nombre}"

    def clean(self):
        if self.proximo_mantenimiento and self.ultimo_mantenimiento:
            if self.proximo_mantenimiento <= self.ultimo_mantenimiento:
                raise ValidationError("La fecha de próximo mantenimiento debe ser posterior al último mantenimiento")

    def save(self, *args, **kwargs):
        is_new = not self.pk
        super().save(*args, **kwargs)
        # Se intenta llamar al método de forma segura para evitar errores
        if is_new and hasattr(self.empresa, 'actualizar_contadores'):
            try:
                self.empresa.actualizar_contadores()
            except Exception as e:
                # Si ocurre un error, lo registramos pero no interrumpimos el guardado
                print(f"Error al actualizar contadores de empresa: {e}")


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
        # Llama al clean del padre si estás heredando (buena práctica)
        super().clean()

        # Verifica que los campos necesarios para la validación existan y tengan valor
        if self.responsable and hasattr(self.responsable, 'perfil') and self.responsable.perfil and self.empresa_id:
            try:
                # Es más seguro también usar el _id para la empresa del perfil
                responsable_empresa_id = self.responsable.perfil.empresa_id
                if responsable_empresa_id != self.empresa_id:
                    raise ValidationError({
                        'responsable': 'La empresa del responsable asignado no coincide con la empresa de la faena.',
                    })
            except AttributeError:
                # Maneja el caso donde 'perfil' o 'perfil.empresa_id' no existan como se espera
                pass
            except Exception as e:
                 # Captura otras posibles excepciones al acceder a los atributos
                 raise ValidationError(f"Error al validar la empresa del responsable: {e}")

    def save(self, *args, **kwargs):
        # Lógica de estado
        if self.fecha_termino_real and self.estado != self.Estado.COMPLETADA:
            self.estado = self.Estado.COMPLETADA
        
        is_new = not self.pk
        super().save(*args, **kwargs)
        
        # Actualización de contadores para nueva faena de forma segura
        if is_new and hasattr(self.empresa, 'actualizar_contadores'):
            try:
                self.empresa.actualizar_contadores()
            except Exception as e:
                # Si hay error, lo registramos pero no interrumpimos
                print(f"Error al actualizar contadores para faena: {e}")



class Trabajo(models.Model):
    TIPO_MEDIDA_CHOICES = [
        ('Horas', 'Horas'),
        ('Kilómetros', 'Kilómetros'),
    ]
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'), 
        ('rechazado', 'Rechazado'),
    ]

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='trabajos',
        editable=False,
        verbose_name="Empresa",
        null=True # Permitir nulo temporalmente hasta que se asigne
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
        verbose_name="Horómetro/Km inicial"
    )
    horometro_final = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Horómetro/Km final"
    )
    total_horas = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        editable=False,
        verbose_name="Total Horas/Km"
    )
    petroleo_litros = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Litros de petróleo",
        null=True, blank=True
    )
    aceite_tipo = models.CharField(max_length=100, verbose_name="Tipo de aceite", null=True, blank=True)
    aceite_litros = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Litros de aceite",
        null=True, blank=True
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
        on_delete=models.SET_NULL,
        related_name='trabajos_creados',
        verbose_name="Creado por",
        null=True,
        blank=True
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
        faena_nombre = self.faena.nombre if self.faena else "Sin Faena"
        maquina_nombre = self.maquina.nombre if self.maquina else "Sin Máquina"
        fecha_str = self.fecha.strftime("%Y-%m-%d") if self.fecha else "Sin Fecha"
        return f"{faena_nombre} - {maquina_nombre} - {fecha_str}"

    def clean(self):
        errors = {}

        # Validar relaciones y campos solo si tienen valor
        if self.faena and self.maquina and self.faena.empresa != self.maquina.empresa:
            errors['maquina'] = "La faena y la máquina deben pertenecer a la misma empresa."

        if self.horometro_inicial is not None and self.horometro_final is not None:
            if self.horometro_final < self.horometro_inicial:
                errors['horometro_final'] = "El horómetro/Km final debe ser mayor que el inicial."

        # Validar pertenencia a empresa solo si el usuario tiene perfil y faena asignada
        empresa_trabajo = self.faena.empresa if self.faena else None
        if empresa_trabajo:
            if self.trabajador and hasattr(self.trabajador, 'perfil') and self.trabajador.perfil and self.trabajador.perfil.empresa != empresa_trabajo:
                 errors['trabajador'] = f"El trabajador '{self.trabajador.username}' debe pertenecer a la empresa '{empresa_trabajo.nombre}'."

            if self.supervisor and hasattr(self.supervisor, 'perfil') and self.supervisor.perfil and self.supervisor.perfil.empresa != empresa_trabajo:
                 errors['supervisor'] = f"El supervisor '{self.supervisor.username}' debe pertenecer a la empresa '{empresa_trabajo.nombre}'."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Calcular total de horas/km si ambos valores están presentes
        if self.horometro_inicial is not None and self.horometro_final is not None:
            self.total_horas = self.horometro_final - self.horometro_inicial
        else:
            self.total_horas = None

        # Asignar empresa automáticamente desde la faena (siempre que haya faena)
        if self.faena:
             self.empresa = self.faena.empresa
        elif self.maquina: # Plan B: desde la máquina si no hay faena
             self.empresa = self.maquina.empresa

        super().save(*args, **kwargs)