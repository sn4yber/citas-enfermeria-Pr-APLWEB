from datetime import date, time, timedelta
from decimal import Decimal
from citas.models import Cita, OrdenMedica, AutorizacionEPS
from citas.infrastructure.adapters.django_repositories import CitaRepository, UsuarioRepository
from citas.domain.exceptions import AppointmentConflictException, UserNotFoundException

# Cuotas moderadoras 2026 (Resolución vigente)
CUOTAS_MODERADORAS = {
    'contributivo_bajo': Decimal('5000'),    # < 2 SMMLV
    'contributivo_alto': Decimal('20100'),   # >= 2 SMMLV
    'subsidiado': Decimal('0'),
}

ESPECIALIDADES_ACCESO_DIRECTO = {
    'pediatria': {'edad_max': 18},
    'ginecobstetricia': {'requiere_gestante': True},
}


def _calcular_cuota_moderadora(paciente, tipo_cita: str) -> Decimal:
    """Calcula la cuota moderadora según régimen del paciente y tipo de cita."""
    if not paciente or not paciente.regimen:
        return CUOTAS_MODERADORAS['contributivo_bajo']
    if paciente.regimen == 'subsidiado' or getattr(paciente, 'exento_cuota', False):
        return Decimal('0')
    return CUOTAS_MODERADORAS['contributivo_bajo']


def _tiene_acceso_directo_especialidad(paciente, especialidad_nombre: str) -> bool:
    """Verifica si el paciente tiene acceso directo a la especialidad (menores/gestantes)."""
    nombre_lower = (especialidad_nombre or '').lower()
    if 'pediatr' in nombre_lower:
        if paciente.fecha_nacimiento:
            edad = (date.today() - paciente.fecha_nacimiento).days // 365
            if edad < 18:
                return True
    if 'ginec' in nombre_lower or 'obstetric' in nombre_lower:
        return True
    return False


class ScheduleAppointmentUseCase:
    def __init__(self, cita_repository: CitaRepository):
        self.cita_repository = cita_repository

    def execute(
        self,
        paciente_id: int,
        medico_id: int,
        fecha: date,
        hora: time,
        motivo: str,
        tipo_cita: str = 'general',
        canal_solicitud: str = 'web',
        orden_medica_id: int = None,
        autorizacion_id: int = None,
    ) -> Cita:
        from django.contrib.auth import get_user_model
        Usuario = get_user_model()

        existing = self.cita_repository.get_by_medico_and_datetime(medico_id, fecha, hora)
        if existing and existing.estado != 'cancelada':
            raise AppointmentConflictException("El médico ya tiene una cita programada en ese horario.")

        paciente = None
        try:
            paciente = Usuario.objects.select_related('especialidad', 'eps').get(id=paciente_id)
        except Usuario.DoesNotExist:
            raise UserNotFoundException("Paciente no encontrado.")

        medico = None
        try:
            medico = Usuario.objects.select_related('especialidad').get(id=medico_id)
        except Usuario.DoesNotExist:
            raise UserNotFoundException("Médico no encontrado.")

        especialidad_nombre = getattr(medico.especialidad, 'nombre', '') if medico.especialidad else ''

        if tipo_cita == 'especializada':
            acceso_directo = _tiene_acceso_directo_especialidad(paciente, especialidad_nombre)
            if not acceso_directo:
                if not autorizacion_id:
                    raise ValueError(
                        "Las citas especializadas requieren una autorización EPS vigente."
                    )
                try:
                    autorizacion = AutorizacionEPS.objects.get(id=autorizacion_id)
                    if autorizacion.estado != 'aprobada':
                        raise ValueError("La autorización EPS no está aprobada.")
                    if autorizacion.fecha_vigencia < date.today():
                        raise ValueError("La autorización EPS está vencida.")
                except AutorizacionEPS.DoesNotExist:
                    raise ValueError("Autorización EPS no encontrada.")

        cuota = _calcular_cuota_moderadora(paciente, tipo_cita)
        exento = paciente.regimen == 'subsidiado' if paciente.regimen else False

        cita = Cita(
            paciente_id=paciente_id,
            medico_id=medico_id,
            fecha=fecha,
            hora=hora,
            estado='programada',
            motivo=motivo,
            tipo_cita=tipo_cita,
            canal_solicitud=canal_solicitud,
            orden_medica_id=orden_medica_id,
            autorizacion_id=autorizacion_id,
            cuota_moderadora=cuota,
            exento_cuota=exento,
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


class CreateOrdenMedicaUseCase:
    """El médico emite una orden médica tras una cita general."""

    def execute(
        self,
        paciente_id: int,
        medico_solicitante_id: int,
        especialidad_solicitada_id: int,
        cita_origen_id: int = None,
        vigencia_dias: int = 30,
        observaciones: str = '',
    ) -> OrdenMedica:
        orden = OrdenMedica(
            paciente_id=paciente_id,
            medico_solicitante_id=medico_solicitante_id,
            especialidad_solicitada_id=especialidad_solicitada_id,
            cita_origen_id=cita_origen_id,
            vigencia_dias=vigencia_dias,
            observaciones=observaciones,
            estado='pendiente_autorizacion',
        )
        orden.save()
        return orden


class RegisterAutorizacionEPSUseCase:
    """El administrador registra la autorización recibida de la EPS."""

    def execute(
        self,
        orden_id: int,
        eps_id: int,
        numero_autorizacion: str,
        fecha_autorizacion: date,
        fecha_vigencia: date,
        servicios_autorizados: str = '',
    ) -> AutorizacionEPS:
        try:
            orden = OrdenMedica.objects.get(id=orden_id)
        except OrdenMedica.DoesNotExist:
            raise ValueError("Orden médica no encontrada.")

        autorizacion = AutorizacionEPS(
            orden=orden,
            eps_id=eps_id,
            numero_autorizacion=numero_autorizacion,
            fecha_autorizacion=fecha_autorizacion,
            fecha_vigencia=fecha_vigencia,
            estado='aprobada',
            servicios_autorizados=servicios_autorizados,
        )
        autorizacion.save()

        orden.estado = 'autorizada'
        orden.save()

        return autorizacion
