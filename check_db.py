import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from citas.models import Cita
for c in Cita.objects.all():
    print(f"Cita ID: {c.id}, Paciente: {c.paciente_id}, Medico: {c.medico_id}, Fecha: {c.fecha}, Hora: {c.hora}, Estado: {c.estado}")
