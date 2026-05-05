import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from citas.models import Cita
from citas.infrastructure.serializers.appointment_serializers import CitaSerializer

cita = Cita.objects.get(id=2)
try:
    print(CitaSerializer(cita).data)
except Exception as e:
    import traceback
    traceback.print_exc()
