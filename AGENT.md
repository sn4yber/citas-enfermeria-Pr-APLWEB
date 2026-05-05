# Sistema de Gestión de Citas Médicas

## Proyecto
Sistema web para gestionar citas médicas en una institución de salud.

## Stack Tecnológico
- **Frontend**: Astro
- **Backend**: Django (Python)
- **API**: Django REST Framework
- **DB**: PostgreSQL

## Actores
| Rol | Permisos |
|-----|----------|
| Paciente | Registrarse, agendar, cancelar, ver historial |
| Médico | Ver agenda, consultar pacientes, actualizar estado citas |
| Administrador | Gestionar médicos, especialidades, supervisar sistema |

## Requerimientos Funcionales
1. Registro e inicio de sesión
2. Consultar médicos por especialidad
3. Agendar citas (sin duplicados)
4. Cancelar/modificar citas
5. Panel médico (agenda diaria)
6. Gestión admin (médicos, especialidades)
7. Historial de citas

## Estructura Actual
```
/citas-enfermeria-Pr-APLWEB
├── core/           # Config Django
├── citas/          # App principal (hexagonal)
│   ├── domain/       # Entidades, ports
│   ├── application/  # DTOs, lógica
│   └── infrastructure/ # Models, views, serializers
├── frontend/       # Astro (vacío)
└── docs/           # Documentación UML
```

## Entidades (domain/entities.py)
- `Usuario` (base)
- `Paciente` (hereda Usuario)
- `Medico` (hereda Usuario) + especialidad_id, disponible
- `Especialidad`
- `Cita` + paciente_id, medico_id, fecha, hora, estado, motivo

## Pendiente
1. [x] Backend Django completo
2. [x] Frontend Astro (Auth + Dashboard paciente)
3. [x] Rutas /admin/* y /medical/*
4. [ ] Dashboard admin/medico
5. [ ] Agendar citas (frontend)
6. [ ] Conexión con backend