from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver


class Trabajo(models.Model):
    fecha = models.DateField()
    faena = models.CharField(max_length=100)
    maquina = models.CharField(max_length=100)
    trabajo = models.CharField(max_length=200)
    horometro_inicial = models.DecimalField(max_digits=5, decimal_places=2)
    horometro_final = models.DecimalField(max_digits=5, decimal_places=2)
    total_horas = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    petroleo_litros = models.FloatField()
    aceite_tipo_litros = models.CharField(max_length=200)
    observaciones = models.TextField()
    supervisor = models.ForeignKey(
        User, related_name='supervisores', on_delete=models.CASCADE)
    trabajador = models.ForeignKey(
        User, related_name='trabajadores', on_delete=models.CASCADE)
    aprobado = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.faena} - {self.maquina} - {self.fecha}"


@receiver(post_save, sender=User)
def add_user_to_default_group(sender, instance, created, **kwargs):
    if created:
        group = Group.objects.get(name='Trabajador')
        instance.groups.add(group)
