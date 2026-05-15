from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, date, time


@dataclass
class EPS:
    id: Optional[int]
    nombre: str
    codigo_rnos: str
    activa: bool = True


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
    tipo_documento: str = "CC"
    numero_documento: Optional[str] = None
    eps_id: Optional[int] = None
    regimen: Optional[str] = None


@dataclass
class Especialidad:
    id: Optional[int]
    nombre: str
    descripcion: str


@dataclass
class Medico(Usuario):
    especialidad_id: int = 0
    telefono: str = ""
    disponible: bool = True


@dataclass
class OrdenMedica:
    id: Optional[int]
    paciente_id: int
    medico_solicitante_id: int
    especialidad_solicitada_id: int
    estado: str = "pendiente_autorizacion"
    cita_origen_id: Optional[int] = None
    vigencia_dias: int = 30
    observaciones: str = ""
    fecha_emision: Optional[date] = None
    fecha_creacion: Optional[datetime] = None


@dataclass
class AutorizacionEPS:
    id: Optional[int]
    orden_id: int
    eps_id: int
    numero_autorizacion: str
    fecha_autorizacion: date
    fecha_vigencia: date
    estado: str = "aprobada"
    servicios_autorizados: str = ""
    fecha_creacion: Optional[datetime] = None


@dataclass
class Cita:
    id: Optional[int]
    paciente_id: int
    medico_id: int
    fecha: date
    hora: time
    estado: str
    motivo: str
    tipo_cita: str = "general"
    canal_solicitud: str = "web"
    orden_medica_id: Optional[int] = None
    autorizacion_id: Optional[int] = None
    cuota_moderadora: Optional[float] = None
    exento_cuota: bool = False
    fecha_creacion: Optional[datetime] = None
