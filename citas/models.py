from django.db import models
from django.contrib.auth.models import AbstractUser


class Especialidad(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Especialidad'
        verbose_name_plural = 'Especialidades'

    def __str__(self):
        return self.nombre


class Usuario(AbstractUser):
    class Rol(models.TextChoices):
        PACIENTE = 'paciente', 'Paciente'
        MEDICO = 'medico', 'Médico'
        ADMIN = 'admin', 'Administrador'

    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.PACIENTE)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(unique=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'


class Cita(models.Model):
    class Estado(models.TextChoices):
        PROGRAMADA = 'programada', 'Programada'
        COMPLETADA = 'completada', 'Completada'
        CANCELADA = 'cancelada', 'Cancelada'
        NO_ASISTIO = 'no_asistio', 'No Asistió'

    paciente = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='citas_paciente'
    )
    medico = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='citas_medico'
    )
    fecha = models.DateField()
    hora = models.TimeField()
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PROGRAMADA
    )
    motivo = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        unique_together = ['medico', 'fecha', 'hora']

    def __str__(self):
        return f"Cita {self.id} - {self.paciente.username} con {self.medico.username}"