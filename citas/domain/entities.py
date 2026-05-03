from dataclasses import dataclass
from typing import Optional
from datetime import datetime, date, time

@dataclass
class Usuario:
    id: Optional[int]
    nombre: str
    email: str
    password_hash: str
    rol: str
    fecha_creacion: Optional[datetime] = None

@dataclass
class Paciente(Usuario):
    telefono: str = ""
    fecha_nacimiento: Optional[date] = None

@dataclass
class Especialidad:
    id: Optional[int]
    nombre: str
    descripcion: str

@dataclass
class Medico(Usuario):
    # kwargs_only para solucionar herencia
    especialidad_id: int = 0
    telefono: str = ""
    disponible: bool = True

@dataclass
class Cita:
    id: Optional[int]
    paciente_id: int
    medico_id: int
    fecha: date
    hora: time
    estado: str  # 'Programada', 'Completada', 'Cancelada', etc.
    motivo: str
    fecha_creacion: Optional[datetime] = None