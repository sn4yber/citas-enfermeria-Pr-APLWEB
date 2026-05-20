# Sistema de Gestión de Citas Médicas — SGSSS Colombia

Aplicación web para la gestión de citas médicas en una IPS (Institución Prestadora de Servicios de Salud) que atiende pacientes afiliados a distintas EPS, modelando el flujo de atención del **Sistema General de Seguridad Social en Salud (SGSSS)** en Colombia.

El sistema separa el acceso directo a medicina general del acceso restringido a especialistas, incorporando órdenes médicas y autorizaciones EPS como requisitos previos para la atención especializada.

---

## Despliegue en producción

| Componente | Plataforma | URL |
|------------|------------|-----|
| Frontend | Vercel | https://citas-enfermeria-pr-aplweb.vercel.app |
| API REST | Render | https://citas-enfermeria-pr-aplweb.onrender.com |
| Documentación API | Render (Swagger) | https://citas-enfermeria-pr-aplweb.onrender.com/swagger/ |
| Base de datos | Neon (PostgreSQL) | Servicio externo conectado vía `DATABASE_URL` |

---

## Stack tecnológico

| Capa | Tecnología |
|------|------------|
| Frontend | Astro 5, Tailwind CSS 3 |
| Backend | Django 6, Django REST Framework |
| Autenticación | JSON Web Tokens (SimpleJWT) |
| Base de datos | PostgreSQL en producción; SQLite en desarrollo local |
| Documentación API | drf-yasg (Swagger / ReDoc) |
| Servidor WSGI | Gunicorn + WhiteNoise |
| Zona horaria | `America/Bogota` |
| Idioma del sistema | Español (Colombia) — `es-co` |

---

## Arquitectura del software

El backend sigue una **arquitectura hexagonal** (ports & adapters) dentro de la app `citas`:

```
citas/
├── domain/           # Entidades de dominio, excepciones y puertos (interfaces)
├── application/      # Casos de uso y DTOs
└── infrastructure/   # Adaptadores Django: modelos ORM, repositorios, serializers, vistas, rutas
```

La capa de infraestructura expone la API REST; la lógica de negocio relevante (validación de autorizaciones, cuotas moderadoras, conflictos de agenda) reside en los casos de uso de la capa de aplicación.

El frontend es una aplicación **Astro estática** (`output: static`) que consume la API mediante `fetch` autenticado con JWT. La URL base de la API se inyecta en tiempo de build mediante `PUBLIC_API_URL` y queda disponible globalmente como `window.__API__`.

---

## Actores y roles

| Rol | Descripción |
|-----|-------------|
| **Paciente** | Usuario afiliado a una EPS. Puede registrarse, agendar citas de acceso directo (general/prioritaria), consultar sus citas y órdenes, y agendar especialistas cuando dispone de autorización vigente. |
| **Médico** | Profesional vinculado a una especialidad. Consulta su agenda, atiende citas, actualiza estados y emite órdenes médicas de remisión a especialistas. |
| **Administrador** | Operador de la IPS. Supervisa citas, gestiona EPS, especialidades, médicos y pacientes, y registra las autorizaciones emitidas por las EPS sobre las órdenes médicas pendientes. |

La autenticación utiliza **correo electrónico** como identificador de usuario (`AUTH_USER_MODEL = citas.Usuario`).

---

## Flujo de atención SGSSS

El flujo principal de la aplicación reproduce la ruta de atención en salud regulada en Colombia:

```
1. Registro del paciente
   └── Documento de identidad, EPS, régimen (contributivo / subsidiado)

2. Cita de Medicina General o Prioritaria
   └── Acceso directo sin orden previa
   └── Cuota moderadora según régimen

3. Atención médica
   └── El médico completa la consulta o remite al paciente

4. Orden médica (si aplica remisión)
   └── Estado: pendiente_autorizacion
   └── Especialidad destino definida por el médico tratante

5. Autorización EPS
   └── El administrador registra la respuesta de la EPS
   └── Estado de la orden: autorizada / rechazada

6. Cita con especialista
   └── El paciente agenda desde "Mis Órdenes" presentando autorización vigente
   └── Validación de vigencia y estado aprobado
```

### Excepciones de acceso directo a especialista

Sin orden médica previa, el sistema permite acceso directo en estos casos:

- **Pediatría**: pacientes menores de 18 años.
- **Ginecobstetricia**: acceso directo para población gestante (regla de negocio simplificada).

### Tipos de cita

| Tipo | Código | Requisitos |
|------|--------|------------|
| Medicina General | `general` | Acceso directo |
| Prioritaria | `prioritaria` | Acceso directo; identificación en ventanilla |
| Especializada | `especializada` | Orden médica + autorización EPS aprobada y vigente |

### Canales de solicitud

Las citas registran el canal por el cual se solicitó: `web`, `whatsapp`, `telefonica`, `presencial`. En la interfaz del paciente el canal web queda fijado como predeterminado.

### Cuotas moderadoras

El motor de citas calcula la cuota moderadora al agendar:

| Régimen / condición | Valor referencia (2026) |
|---------------------|-------------------------|
| Contributivo (bajo) | $5.000 COP |
| Contributivo (alto) | $20.100 COP |
| Subsidiado | $0 (exento) |

### Tiempos máximos de espera (referencia normativa)

Según la Resolución 1552 de 2013:

- Medicina general / odontología: **3 días hábiles**
- Cita especializada: **5 días hábiles** desde la solicitud

*(La aplicación documenta estos plazos; la validación automática con calendario de festivos colombianos está pendiente de implementación.)*

---

## Modelo de datos

### EPS
Entidad pagadora del SGSSS. Campos: nombre, código RNOS, estado activo/inactivo.

### Usuario
Extiende `AbstractUser`. Campos adicionales: rol, teléfono, fecha de nacimiento, tipo y número de documento, EPS afiliada, régimen, especialidad (solo médicos).

**Tipos de documento:** CC, TI, CE, PA.  
**Regímenes:** contributivo, subsidiado.

### Especialidad
Catálogo de especialidades médicas disponibles en la IPS.

### Cita
Núcleo operativo del sistema. Relaciona paciente, médico, fecha, hora, estado, tipo de cita, motivo, observaciones, orden médica asociada, autorización EPS, cuota moderadora, exención de cuota y canal de solicitud.

**Estados:** programada, pendiente_autorizacion, completada, cancelada, no_asistio.

**Restricción:** un médico no puede tener dos citas activas en la misma fecha y hora (`unique_together`).

### Orden Médica
Documento de remisión emitido por un médico tras una consulta. Vincula paciente, médico solicitante, especialidad destino, cita origen, vigencia en días y observaciones.

**Estados:** pendiente_autorizacion, autorizada, rechazada, vencida.

### Autorización EPS
Respuesta formal de la EPS sobre una orden médica. Incluye número de autorización, fechas de emisión y vigencia, EPS emisora, servicios autorizados y estado (aprobada, negada, vencida).

Relación uno-a-uno con `OrdenMedica`.

### Historia Clínica, ItemReceta, OrdenLaboratorio
Modelos disponibles en el backend para registro clínico estructurado (anamnesis, signos vitales, diagnóstico CIE-10, receta, órdenes de laboratorio). La interfaz médica actual utiliza un flujo simplificado de atención y remisión; el módulo completo de historia clínica existe a nivel de API y persistencia pero no está expuesto en toda su extensión en el frontend.

---

## Casos de uso (capa de aplicación)

| Caso de uso | Responsabilidad |
|-------------|-----------------|
| `ScheduleAppointmentUseCase` | Agenda citas validando conflictos de horario, autorización EPS (especializadas), acceso directo y cuota moderadora |
| `CancelAppointmentUseCase` | Cancela una cita existente |
| `UpdateAppointmentStatusUseCase` | Actualiza el estado de una cita (completada, no asistió, etc.) |
| `GetAppointmentsByPatientUseCase` | Lista citas de un paciente |
| `GetAppointmentsByDoctorUseCase` | Lista citas de un médico (opcionalmente filtradas por fecha) |
| `CreateOrdenMedicaUseCase` | Emite orden médica en estado pendiente de autorización |
| `RegisterAutorizacionEPSUseCase` | Registra autorización EPS y actualiza el estado de la orden |

---

## API REST

Base path: `/api/`

### Autenticación (JWT)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/token/` | Obtiene par de tokens (access + refresh) |
| POST | `/api/token/refresh/` | Renueva access token |
| POST | `/api/token/blacklist/` | Invalida refresh token |

### Usuarios y registro

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Registro de nuevos usuarios |
| GET | `/api/usuarios/` | Listado de usuarios |
| GET | `/api/medicos/` | Listado de médicos |

### Citas y disponibilidad

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/citas/` | Listado de citas (filtrado por rol) |
| POST | `/api/citas/create/` | Creación de cita |
| GET/PATCH/DELETE | `/api/citas/<id>/` | Detalle, actualización y eliminación |
| GET | `/api/disponibilidad/` | Consulta de disponibilidad médica |

### Catálogos

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET/POST | `/api/especialidades/` | Especialidades |
| GET/PATCH/DELETE | `/api/especialidades/<id>/` | Detalle de especialidad |
| GET/POST | `/api/eps/` | EPS registradas |
| GET/PATCH/DELETE | `/api/eps/<id>/` | Detalle de EPS |

### Órdenes y autorizaciones SGSSS

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET/POST | `/api/ordenes-medicas/` | Órdenes médicas |
| GET/PATCH | `/api/ordenes-medicas/<id>/` | Detalle de orden |
| POST | `/api/ordenes-medicas/<id>/autorizar/` | Registro de autorización EPS |

### Historia clínica

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET/POST | `/api/historias/` | Historias clínicas |
| GET/PATCH | `/api/historias/<id>/` | Detalle de historia |
| GET | `/api/citas/<id>/historia/` | Historia asociada a una cita |

### Documentación interactiva

- **Swagger UI:** `/swagger/`
- **ReDoc:** `/redoc/`
- **Panel Django Admin:** `/admin/`

La API utiliza autenticación Bearer JWT por defecto (`IsAuthenticated`), con throttling configurado para usuarios anónimos y autenticados.

---

## Frontend — estructura de pantallas

### Público

| Ruta | Pantalla |
|------|----------|
| `/` | Landing page del sistema |
| `/auth/login` | Inicio de sesión paciente |
| `/auth/register` | Registro de paciente (EPS, régimen, documento) |

### Portal paciente (`/dashboard/`)

| Ruta | Pantalla |
|------|----------|
| `/dashboard/` | Inicio con resumen y camino de atención SGSSS |
| `/dashboard/agendar` | Agendamiento de cita general o prioritaria |
| `/dashboard/citas` | Historial y gestión de citas del paciente |
| `/dashboard/ordenes` | Órdenes médicas autorizadas; agendamiento de especialista |

### Portal médico (`/medical/`)

| Ruta | Pantalla |
|------|----------|
| `/medical/login` | Inicio de sesión médico |
| `/medical/dashboard` | Panel del médico |
| `/medical/agenda` | Agenda diaria; atención de citas y emisión de órdenes médicas |
| `/medical/historial` | Historial de atenciones |
| `/medical/pacientes` | Consulta de pacientes |

### Portal administrador (`/admin/`)

| Ruta | Pantalla |
|------|----------|
| `/admin/login` | Inicio de sesión administrador |
| `/admin/register` | Registro de usuarios administrativos |
| `/admin/dashboard` | Panel de indicadores |
| `/admin/citas` | Gestión de citas, órdenes médicas y autorizaciones EPS |
| `/admin/especialidades` | Catálogo de especialidades |
| `/admin/medicos` | Gestión de médicos |
| `/admin/pacientes` | Gestión de pacientes |

### Layouts

- `BaseLayout`: estructura HTML base e inyección de configuración API
- `DashboardLayout`, `MedicalLayout`, `AdminLayout`: navegación lateral por rol

---

## Seguridad y configuración

- **SECRET_KEY**, **DEBUG**, **DATABASE_URL**, **ALLOWED_HOSTS** y **CORS_ALLOWED_ORIGINS** se configuran mediante variables de entorno (`django-environ`).
- En producción, CORS restringe el origen del frontend en Vercel; se admite regex para despliegues preview (`*.vercel.app`).
- Los tokens JWT tienen vigencia de 1 hora (access) y 1 día (refresh), con rotación de refresh tokens habilitada.
- WhiteNoise sirve los archivos estáticos del panel de administración Django en el despliegue.

---

## Estructura del repositorio

```
citas-enfermeria-Pr-APLWEB/
├── core/                  # Proyecto Django (settings, urls, backends, wsgi)
├── citas/                 # Aplicación principal (hexagonal)
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   ├── migrations/
│   └── tests/
├── frontend/              # Cliente Astro + Tailwind
│   └── src/
│       ├── components/
│       ├── layouts/
│       └── pages/
├── docs/                  # Diagramas UML (componentes, clases, secuencias, actividades)
├── render.yaml            # Blueprint de despliegue Render (API)
├── requirements.txt       # Dependencias Python
└── manage.py
```

---

## Documentación complementaria

En la carpeta `docs/` se incluyen diagramas de arquitectura y el documento de especificación del sistema (`Sistema_Gestion_Citas_Medicas.pdf`). El archivo `AGENT.md` contiene referencia técnica adicional orientada a agentes de desarrollo.

---

## Alcance y limitaciones conocidas

Funcionalidades contempladas en el diseño pero no implementadas o parcialmente implementadas:

- Validación de SLA con calendario de días hábiles y festivos colombianos
- Notificaciones automáticas por WhatsApp, SMS o correo
- Generación de reportes RIPS
- Expiración automática de órdenes médicas vencidas
- Interfaz completa de historia clínica (backend disponible; UI simplificada en agenda médica)

---

## Contexto académico

Proyecto desarrollado como aplicación web de gestión de citas médicas adaptada al marco del SGSSS colombiano, integrando conceptos de arquitectura de software, API REST, autenticación JWT y modelado de procesos de salud regulados.

**Integrantes:** Luis Betancur, Ian Pérez Oliveira, Snayber Madrid, Santiago Forero
