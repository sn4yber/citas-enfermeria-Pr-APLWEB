from abc import ABC, abstractmethod
from typing import List, Optional
from citas.domain.entities import Usuario, Medico, Cita, Paciente

class UsuarioRepository(ABC):
    @abstractmethod
    def save(self, usuario: Usuario) -> Usuario:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[Usuario]:
        pass

class MedicoRepository(ABC):
    @abstractmethod
    def get_all_by_specialty(self, especialidad_id: int) -> List[Medico]:
        pass

class CitaRepository(ABC):
    @abstractmethod
    def save(self, cita: Cita) -> Cita:
        pass

    @abstractmethod
    def get_by_medico_and_datetime(self, medico_id: int, fecha, hora) -> Optional[Cita]:
        pass

    @abstractmethod
    def update_estado(self, cita_id: int, estado: str) -> bool:
        pass
