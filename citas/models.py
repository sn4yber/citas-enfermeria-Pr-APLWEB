from django.db import models
from django.contrib.auth.models import AbstractUser


class EPS(models.Model):
    nombre = models.CharField(max_length=150)
    codigo_rnos = models.CharField(max_length=20, unique=True)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'EPS'
        verbose_name_plural = 'EPS'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


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

    class TipoDocumento(models.TextChoices):
        CC = 'CC', 'Cédula de Ciudadanía'
        TI = 'TI', 'Tarjeta de Identidad'
        CE = 'CE', 'Cédula de Extranjería'
        PA = 'PA', 'Pasaporte'

    class Regimen(models.TextChoices):
        CONTRIBUTIVO = 'contributivo', 'Contributivo'
        SUBSIDIADO = 'subsidiado', 'Subsidiado'

    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.PACIENTE)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(unique=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    especialidad = models.ForeignKey(
        'Especialidad', on_delete=models.SET_NULL, null=True, blank=True, related_name='medicos'
    )
    tipo_documento = models.CharField(
        max_length=2, choices=TipoDocumento.choices, default=TipoDocumento.CC, blank=True
    )
    numero_documento = models.CharField(max_length=20, blank=True, null=True, unique=True)
    eps = models.ForeignKey(
        'EPS', on_delete=models.SET_NULL, null=True, blank=True, related_name='afiliados'
    )
    regimen = models.CharField(
        max_length=15, choices=Regimen.choices, null=True, blank=True
    )

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'


class OrdenMedica(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente_autorizacion', 'Pendiente de Autorización'
        AUTORIZADA = 'autorizada', 'Autorizada'
        RECHAZADA = 'rechazada', 'Rechazada'
        VENCIDA = 'vencida', 'Vencida'

    cita_origen = models.ForeignKey(
        'Cita', on_delete=models.SET_NULL, null=True, blank=True, related_name='ordenes_generadas'
    )
    paciente = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='ordenes_medicas'
    )
    medico_solicitante = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, related_name='ordenes_emitidas'
    )
    especialidad_solicitada = models.ForeignKey(
        Especialidad, on_delete=models.SET_NULL, null=True, related_name='ordenes'
    )
    fecha_emision = models.DateField(auto_now_add=True)
    vigencia_dias = models.IntegerField(default=30)
    estado = models.CharField(
        max_length=25, choices=Estado.choices, default=Estado.PENDIENTE
    )
    observaciones = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Orden Médica'
        verbose_name_plural = 'Órdenes Médicas'
        ordering = ['-creado_en']

    def __str__(self):
        return f"Orden #{self.id} - {self.paciente.get_full_name()} → {self.especialidad_solicitada}"


class AutorizacionEPS(models.Model):
    class Estado(models.TextChoices):
        APROBADA = 'aprobada', 'Aprobada'
        NEGADA = 'negada', 'Negada'
        VENCIDA = 'vencida', 'Vencida'

    orden = models.OneToOneField(
        OrdenMedica, on_delete=models.CASCADE, related_name='autorizacion'
    )
    eps = models.ForeignKey(
        EPS, on_delete=models.SET_NULL, null=True, related_name='autorizaciones'
    )
    numero_autorizacion = models.CharField(max_length=50)
    fecha_autorizacion = models.DateField()
    fecha_vigencia = models.DateField()
    estado = models.CharField(
        max_length=10, choices=Estado.choices, default=Estado.APROBADA
    )
    servicios_autorizados = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Autorización EPS'
        verbose_name_plural = 'Autorizaciones EPS'
        ordering = ['-creado_en']

    def __str__(self):
        return f"Autorización {self.numero_autorizacion} - {self.estado}"


class Cita(models.Model):
    class Estado(models.TextChoices):
        PROGRAMADA = 'programada', 'Programada'
        PENDIENTE_AUTORIZACION = 'pendiente_autorizacion', 'Pendiente de Autorización'
        COMPLETADA = 'completada', 'Completada'
        CANCELADA = 'cancelada', 'Cancelada'
        NO_ASISTIO = 'no_asistio', 'No Asistió'

    class TipoCita(models.TextChoices):
        GENERAL = 'general', 'Medicina General'
        ESPECIALIZADA = 'especializada', 'Especializada'
        PRIORITARIA = 'prioritaria', 'Prioritaria'

    class CanalSolicitud(models.TextChoices):
        WEB = 'web', 'Página Web / App'
        WHATSAPP = 'whatsapp', 'WhatsApp'
        TELEFONICA = 'telefonica', 'Línea Telefónica'
        PRESENCIAL = 'presencial', 'Presencial'

    paciente = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='citas_paciente'
    )
    medico = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='citas_medico'
    )
    fecha = models.DateField()
    hora = models.TimeField()
    estado = models.CharField(
        max_length=25, choices=Estado.choices, default=Estado.PROGRAMADA
    )
    tipo_cita = models.CharField(
        max_length=15, choices=TipoCita.choices, default=TipoCita.GENERAL
    )
    motivo = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)
    orden_medica = models.ForeignKey(
        OrdenMedica, on_delete=models.SET_NULL, null=True, blank=True, related_name='citas'
    )
    autorizacion = models.ForeignKey(
        AutorizacionEPS, on_delete=models.SET_NULL, null=True, blank=True, related_name='citas'
    )
    cuota_moderadora = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    exento_cuota = models.BooleanField(default=False)
    canal_solicitud = models.CharField(
        max_length=15, choices=CanalSolicitud.choices, default=CanalSolicitud.WEB
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        unique_together = ['medico', 'fecha', 'hora']

    def __str__(self):
        return f"Cita {self.id} - {self.paciente.username} con {self.medico.username} ({self.tipo_cita})"


class HistoriaClinica(models.Model):
    class TipoDiagnostico(models.TextChoices):
        CONFIRMADO = 'confirmado', 'Confirmado'
        PRESUNTIVO = 'presuntivo', 'Presuntivo'
        DESCARTADO = 'descartado', 'Descartado'

    cita = models.OneToOneField(
        Cita, on_delete=models.CASCADE, related_name='historia_clinica'
    )
    medico = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='historias_creadas'
    )
    paciente = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='historias_clinicas'
    )

    # Anamnesis
    motivo_consulta = models.TextField()
    enfermedad_actual = models.TextField(blank=True)
    antecedentes_personales = models.TextField(blank=True)
    revision_sistemas = models.TextField(blank=True)

    # Signos vitales
    tension_arterial = models.CharField(max_length=20, blank=True)
    frecuencia_cardiaca = models.IntegerField(null=True, blank=True)
    frecuencia_respiratoria = models.IntegerField(null=True, blank=True)
    temperatura = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    peso_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    talla_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    saturacion_o2 = models.IntegerField(null=True, blank=True)

    # Examen físico
    examen_fisico = models.TextField(blank=True)

    # Diagnóstico
    diagnostico_principal = models.CharField(max_length=300)
    codigo_cie10 = models.CharField(max_length=10, blank=True)
    tipo_diagnostico = models.CharField(
        max_length=15, choices=TipoDiagnostico.choices, default=TipoDiagnostico.PRESUNTIVO
    )

    # Plan
    conducta = models.TextField(blank=True)
    indicaciones = models.TextField(blank=True)
    proximo_control = models.DateField(null=True, blank=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Historia Clínica'
        verbose_name_plural = 'Historias Clínicas'

    def __str__(self):
        return f"HC {self.id} - {self.paciente.get_full_name()} ({self.cita.fecha})"


class ItemReceta(models.Model):
    FORMAS = [
        ('tableta', 'Tableta'), ('capsula', 'Cápsula'), ('jarabe', 'Jarabe'),
        ('ampolla', 'Ampolla'), ('crema', 'Crema'), ('gotas', 'Gotas'),
        ('inhalador', 'Inhalador'), ('supositorio', 'Supositorio'), ('otro', 'Otro'),
    ]

    historia_clinica = models.ForeignKey(
        HistoriaClinica, on_delete=models.CASCADE, related_name='receta'
    )
    medicamento = models.CharField(max_length=200)
    concentracion = models.CharField(max_length=100, blank=True)
    forma_farmaceutica = models.CharField(max_length=20, choices=FORMAS, blank=True)
    dosis = models.CharField(max_length=100)
    frecuencia = models.CharField(max_length=100)
    duracion = models.CharField(max_length=100)
    cantidad = models.CharField(max_length=50, blank=True)
    indicaciones = models.TextField(blank=True)

    def __str__(self):
        return f"{self.medicamento} {self.concentracion}"


class OrdenLaboratorio(models.Model):
    historia_clinica = models.ForeignKey(
        HistoriaClinica, on_delete=models.CASCADE, related_name='laboratorios'
    )
    examen = models.CharField(max_length=200)
    indicacion = models.CharField(max_length=500, blank=True)
    urgente = models.BooleanField(default=False)

    def __str__(self):
        return self.examen
