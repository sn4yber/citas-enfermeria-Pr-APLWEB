import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from citas.models import Usuario

admin = Usuario.objects.filter(rol='admin').first()
print(f"Admin: {admin.email if admin else 'None'}")

medico = Usuario.objects.filter(rol='medico').last()
if not medico:
    print("No medico found")
    sys.exit(0)

print(f"Medico {medico.id} ({medico.email}) is_active: {medico.is_active}")
medico.is_active = not medico.is_active
medico.save()

medico.refresh_from_db()
print(f"Medico {medico.id} after save is_active: {medico.is_active}")

