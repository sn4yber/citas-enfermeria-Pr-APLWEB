from datetime import date, time
from citas.models import Cita
from citas.infrastructure.adapters.django_repositories import CitaRepository, UsuarioRepository
from citas.domain.exceptions import AppointmentConflictException, UserNotFoundException


class ScheduleAppointmentUseCase:
    def __init__(self, cita_repository: CitaRepository):
        self.cita_repository = cita_repository

    def execute(self, paciente_id: int, medico_id: int, fecha: date, hora: time, motivo: str) -> Cita:
        existing = self.cita_repository.get_by_medico_and_datetime(medico_id, fecha, hora)
        
        if existing and existing.estado != 'cancelada':
            raise AppointmentConflictException("El médico ya tiene una cita programada en ese horario.")

        cita = Cita(
            paciente_id=paciente_id,
            medico_id=medico_id,
            fecha=fecha,
            hora=hora,
            estado='programada',
            motivo=motivo
        )
        return self.cita_repository.save(cita)


class CancelAppointmentUseCase:
    def __init__(self, cita_repository: CitaRepository):
        self.cita_repository = cita_repository

    def execute(self, cita_id: int) -> bool:
        cita = self.cita_repository.get_by_id(cita_id)
        if not cita:
            return False
        cita.estado = 'cancelada'
        self.cita_repository.update(cita)
        return True


class UpdateAppointmentStatusUseCase:
    def __init__(self, cita_repository: CitaRepository):
        self.cita_repository = cita_repository

    def execute(self, cita_id: int, estado: str) -> bool:
        cita = self.cita_repository.get_by_id(cita_id)
        if not cita:
            return False
        cita.estado = estado
        self.cita_repository.update(cita)
        return True


class GetAppointmentsByPatientUseCase:
    def __init__(self, cita_repository: CitaRepository):
        self.cita_repository = cita_repository

    def execute(self, paciente_id: int):
        return self.cita_repository.get_by_paciente(paciente_id)


class GetAppointmentsByDoctorUseCase:
    def __init__(self, cita_repository: CitaRepository):
        self.cita_repository = cita_repository

    def execute(self, medico_id: int, fecha: date = None):
        if fecha:
            return self.cita_repository.get_by_medico_and_fecha(medico_id, fecha)
        return self.cita_repository.get_by_medico(medico_id)