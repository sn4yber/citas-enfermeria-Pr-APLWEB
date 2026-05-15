# Sistema de Gestión de Citas Médicas — SGSSS Colombia

## Proyecto
Sistema web para IPS multi-EPS que gestiona citas médicas siguiendo el flujo del Sistema General de Seguridad Social en Salud (SGSSS) colombiano, basado en la Ley 100 de 1993.

## Stack Tecnológico
- **Frontend**: Astro + Tailwind CSS
- **Backend**: Django + Django REST Framework
- **Auth**: JWT (SimpleJWT)
- **DB**: PostgreSQL (dev: SQLite)
- **Zona horaria**: America/Bogota

## Actores
| Rol | Permisos |
|-----|----------|
| Paciente | Registrarse (con EPS/régimen), agendar, cancelar, ver historial |
| Médico | Ver agenda, emitir órdenes médicas, actualizar estado citas |
| Administrador | Gestionar EPS, autorizar órdenes, supervisar sistema |

## Flujo SGSSS
1. **Registro**: Paciente se registra con tipo/número de documento, EPS y régimen (contributivo/subsidiado)
2. **Cita General**: Acceso directo — agenda cita con médico general u odontología
3. **Orden Médica**: Médico emite orden tras cita general → estado `pendiente_autorizacion`
4. **Autorización EPS**: Admin registra la autorización recibida → orden pasa a `autorizada`
5. **Cita Especialista**: Paciente agenda con especialista presentando autorización vigente
6. **Cita Prioritaria**: Acceso directo sin orden previa (presentar documento de identidad)
7. **Excepciones**: Menores de 18 → Pediatría directa; gestantes → Ginecobstetricia directa

## Tipos de Cita
- `general`: Medicina general/odontología/enfermería — cuota moderadora aplica
- `especializada`: Requiere orden médica + autorización EPS vigente
- `prioritaria`: Sin orden previa, acceso directo

## Cuotas Moderadoras (2026)
- Contributivo (< 2 SMMLV): $5.000
- Contributivo (>= 2 SMMLV): $20.100
- Subsidiado: $0 (exento)

## Tiempos máximos (Resolución 1552/2013)
- Medicina general / odontología: 3 días hábiles
- Cita especializada: 5 días hábiles desde solicitud

## Entidades del dominio
- `EPS`: nombre, codigo_rnos, activa
- `Usuario`: tipo_documento (CC/TI/CE/PA), numero_documento, eps, regimen (contributivo/subsidiado)
- `Especialidad`
- `OrdenMedica`: paciente, medico_solicitante, especialidad_solicitada, estado, vigencia_dias
- `AutorizacionEPS`: orden, eps, numero_autorizacion, fecha_vigencia, estado
- `Cita`: tipo_cita, orden_medica, autorizacion, cuota_moderadora, canal_solicitud

## Estructura
```
/citas-enfermeria-Pr-APLWEB
├── core/           # Config Django (TIME_ZONE: America/Bogota)
├── citas/          # App principal (hexagonal)
│   ├── domain/       # Entidades, ports
│   ├── application/  # Use cases (ScheduleAppointment, CreateOrdenMedica, RegisterAutorizacion)
│   └── infrastructure/ # Models, views, serializers, repositories
├── frontend/       # Astro
│   └── src/pages/
│       ├── auth/register.astro  # Con campos EPS/régimen/documento
│       ├── dashboard/agendar.astro  # Flujo 5 pasos (tipo → autorización → especialidad → médico → fecha)
│       ├── dashboard/citas.astro    # Con tipo, EPS, cuota, autorización
│       ├── medical/agenda.astro     # Con botón "Emitir Orden Médica"
│       └── admin/citas.astro        # Tabs: Citas | Órdenes | EPS
└── docs/           # Documentación UML
```

## API Endpoints clave
- `GET/POST /api/eps/`
- `GET/POST /api/ordenes-medicas/`
- `POST /api/ordenes-medicas/<id>/autorizar/`
- `GET/POST /api/citas/create/` — con tipo_cita, canal_solicitud, autorizacion_id
- `GET/POST /api/especialidades/`

## Pendiente
- [ ] SLA con días hábiles colombianos (festivos)
- [ ] Notificaciones por canal (WhatsApp/email)
- [ ] Reportes RIPS
- [ ] Expiración automática de órdenes médicas vencidas
