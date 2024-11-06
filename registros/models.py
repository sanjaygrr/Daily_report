from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver

# Modelo de Empresa


class Empresa(models.Model):
    nombre = models.CharField(max_length=255)
    rut = models.CharField(max_length=20, unique=True)
    direccion = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    limite_faenas = models.PositiveIntegerField(default=0)
    limite_maquinas = models.PositiveIntegerField(default=0)
    limite_usuarios = models.PositiveIntegerField(default=0)  # Nuevo campo

    def __str__(self):
        return self.nombre

# Extensión del modelo User para añadir el perfil de la empresa


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    empresa = models.ForeignKey(
        Empresa, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.empresa.nombre if self.empresa else 'Sin empresa'}"

# Crear un perfil al crear un usuario


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Crear un perfil para el usuario, pero sin empresa si es superuser
        Profile.objects.create(user=instance)

# Guardar el perfil del usuario al guardar el usuario


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        # Crear el perfil si no existe al momento de guardar
        Profile.objects.create(user=instance)

# Modelo de Máquina con referencia a la Empresa


class Maquina(models.Model):
    nombre = models.CharField(max_length=100)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre

# Modelo de Faena con referencia a la Empresa


class Faena(models.Model):
    nombre = models.CharField(max_length=100)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre

# Modelo de Trabajo con relación a la Faena, Máquina, Empresa y usuarios asignados


class Trabajo(models.Model):
    fecha = models.DateField()
    faena = models.ForeignKey(Faena, on_delete=models.CASCADE)
    maquina = models.ForeignKey(Maquina, on_delete=models.CASCADE)
    trabajo = models.CharField(max_length=200)
    horometro_inicial = models.DecimalField(max_digits=10, decimal_places=2)
    horometro_final = models.DecimalField(max_digits=10, decimal_places=2)
    total_horas = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True)
    petroleo_litros = models.DecimalField(max_digits=10, decimal_places=2)
    aceite_tipo_litros = models.CharField(max_length=200)
    observaciones = models.TextField()
    supervisor = models.ForeignKey(
        User, related_name='supervisores', on_delete=models.CASCADE)
    trabajador = models.ForeignKey(
        User, related_name='trabajadores', on_delete=models.CASCADE)
    aprobado = models.BooleanField(default=False)
    tipo_medida = models.CharField(max_length=10, choices=[(
        'Horas', 'Horas'), ('Kilómetros', 'Kilómetros')], default='Horas')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.faena} - {self.maquina} - {self.fecha}"

# Añadir usuarios al grupo por defecto


@receiver(post_save, sender=User)
def add_user_to_default_group(sender, instance, created, **kwargs):
    if created and not instance.is_superuser:
        group, created = Group.objects.get_or_create(name='Trabajador')
        instance.groups.add(group)
