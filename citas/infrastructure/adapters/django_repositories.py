from typing import List, Optional
from django.contrib.auth import get_user_model
from citas.models import Cita, Especialidad, EPS, OrdenMedica, AutorizacionEPS

Usuario = get_user_model()


class UsuarioRepository:
    def save(self, usuario: Usuario) -> Usuario:
        usuario.save()
        return usuario

    def get_by_id(self, usuario_id: int) -> Optional[Usuario]:
        try:
            return Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            return None

    def get_by_email(self, email: str) -> Optional[Usuario]:
        try:
            return Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return None

    def get_all(self) -> List[Usuario]:
        return list(Usuario.objects.all())

    def get_by_rol(self, rol: str) -> List[Usuario]:
        return list(Usuario.objects.filter(rol=rol))

    def update(self, usuario: Usuario) -> Usuario:
        usuario.save()
        return usuario

    def delete(self, usuario_id: int) -> bool:
        try:
            usuario = Usuario.objects.get(id=usuario_id)
            usuario.delete()
            return True
        except Usuario.DoesNotExist:
            return False


class CitaRepository:
    def save(self, cita: Cita) -> Cita:
        cita.save()
        return cita

    def get_by_id(self, cita_id: int) -> Optional[Cita]:
        try:
            return Cita.objects.get(id=cita_id)
        except Cita.DoesNotExist:
            return None

    def get_by_paciente(self, paciente_id: int) -> List[Cita]:
        return list(Cita.objects.filter(paciente_id=paciente_id).order_by('fecha', 'hora'))

    def get_by_medico(self, medico_id: int) -> List[Cita]:
        return list(Cita.objects.filter(medico_id=medico_id).order_by('fecha', 'hora'))

    def get_by_medico_and_fecha(self, medico_id: int, fecha) -> List[Cita]:
        return list(Cita.objects.filter(medico_id=medico_id, fecha=fecha).order_by('hora'))

    def get_by_medico_and_datetime(self, medico_id: int, fecha, hora) -> Optional[Cita]:
        try:
            return Cita.objects.get(medico_id=medico_id, fecha=fecha, hora=hora)
        except Cita.DoesNotExist:
            return None

    def get_all(self) -> List[Cita]:
        return list(Cita.objects.all().order_by('fecha', 'hora'))

    def update(self, cita: Cita) -> Cita:
        cita.save()
        return cita

    def delete(self, cita_id: int) -> bool:
        try:
            cita = Cita.objects.get(id=cita_id)
            cita.delete()
            return True
        except Cita.DoesNotExist:
            return False


class EPSRepository:
    def get_all_activas(self) -> List[EPS]:
        return list(EPS.objects.filter(activa=True).order_by('nombre'))

    def get_all(self) -> List[EPS]:
        return list(EPS.objects.all().order_by('nombre'))

    def get_by_id(self, eps_id: int) -> Optional[EPS]:
        try:
            return EPS.objects.get(id=eps_id)
        except EPS.DoesNotExist:
            return None

    def save(self, eps: EPS) -> EPS:
        eps.save()
        return eps


class OrdenMedicaRepository:
    def get_all(self) -> List[OrdenMedica]:
        return list(OrdenMedica.objects.select_related(
            'paciente', 'medico_solicitante', 'especialidad_solicitada'
        ).order_by('-creado_en'))

    def get_by_paciente(self, paciente_id: int) -> List[OrdenMedica]:
        return list(OrdenMedica.objects.filter(
            paciente_id=paciente_id
        ).select_related('especialidad_solicitada').order_by('-creado_en'))

    def get_pendientes(self) -> List[OrdenMedica]:
        return list(OrdenMedica.objects.filter(
            estado='pendiente_autorizacion'
        ).select_related('paciente', 'medico_solicitante', 'especialidad_solicitada').order_by('-creado_en'))

    def get_by_id(self, orden_id: int) -> Optional[OrdenMedica]:
        try:
            return OrdenMedica.objects.select_related(
                'paciente', 'medico_solicitante', 'especialidad_solicitada'
            ).get(id=orden_id)
        except OrdenMedica.DoesNotExist:
            return None

    def save(self, orden: OrdenMedica) -> OrdenMedica:
        orden.save()
        return orden


class AutorizacionEPSRepository:
    def get_by_orden(self, orden_id: int) -> Optional[AutorizacionEPS]:
        try:
            return AutorizacionEPS.objects.get(orden_id=orden_id)
        except AutorizacionEPS.DoesNotExist:
            return None

    def get_by_id(self, autorizacion_id: int) -> Optional[AutorizacionEPS]:
        try:
            return AutorizacionEPS.objects.select_related('eps', 'orden').get(id=autorizacion_id)
        except AutorizacionEPS.DoesNotExist:
            return None

    def save(self, autorizacion: AutorizacionEPS) -> AutorizacionEPS:
        autorizacion.save()
        return autorizacion


class EspecialidadRepository:
    def save(self, especialidad: Especialidad) -> Especialidad:
        especialidad.save()
        return especialidad

    def get_by_id(self, especialidad_id: int) -> Optional[Especialidad]:
        try:
            return Especialidad.objects.get(id=especialidad_id)
        except Especialidad.DoesNotExist:
            return None

    def get_all(self) -> List[Especialidad]:
        return list(Especialidad.objects.all())

    def update(self, especialidad: Especialidad) -> Especialidad:
        especialidad.save()
        return especialidad

    def delete(self, especialidad_id: int) -> bool:
        try:
            especialidad = Especialidad.objects.get(id=especialidad_id)
            especialidad.delete()
            return True
        except Especialidad.DoesNotExist:
            return False