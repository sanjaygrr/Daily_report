from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver


class Maquina(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class Faena(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Empresa(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    rut = models.CharField(max_length=20, unique=True)
    direccion = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    correo_electronico = models.EmailField(unique=True)
    numero_telefono = models.CharField(max_length=20, blank=True, null=True)
    cantidad_maquinas = models.PositiveIntegerField(default=0)
    cantidad_faenas = models.PositiveIntegerField(default=0)
    cantidad_usuarios = models.PositiveIntegerField(default=0)
    administrador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='empresas_administradas')



    def __str__(self):
        return self.nombre

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

    def __str__(self):
        return f"{self.faena} - {self.maquina} - {self.fecha}"


@receiver(post_save, sender=User)
def add_user_to_default_group(sender, instance, created, **kwargs):
    if created and not instance.is_superuser:
        group, created = Group.objects.get_or_create(name='Trabajador')
        instance.groups.add(group)
