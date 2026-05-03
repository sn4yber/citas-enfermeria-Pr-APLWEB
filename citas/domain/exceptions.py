class DomainException(Exception):
    """Excepción base para reglas de negocio del dominio."""
    pass

class AppointmentConflictException(DomainException):
    def __init__(self, message="El médico ya tiene una cita programada en ese horario."):
        super().__init__(message)

class UserNotFoundException(DomainException):
    def __init__(self, message="Usuario no encontrado."):
        super().__init__(message)
