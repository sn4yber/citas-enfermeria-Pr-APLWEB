from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, time, timedelta

from citas.models import Cita, Especialidad, EPS, OrdenMedica, AutorizacionEPS, HistoriaClinica, ItemReceta, OrdenLaboratorio
from citas.application.use_cases.manage_appointments import (
    ScheduleAppointmentUseCase, CancelAppointmentUseCase,
    UpdateAppointmentStatusUseCase, GetAppointmentsByPatientUseCase,
    GetAppointmentsByDoctorUseCase, CreateOrdenMedicaUseCase,
    RegisterAutorizacionEPSUseCase,
)
from citas.application.use_cases.manage_users import RegisterUserUseCase
from citas.infrastructure.adapters.django_repositories import (
    CitaRepository, UsuarioRepository, EspecialidadRepository,
    EPSRepository, OrdenMedicaRepository, AutorizacionEPSRepository,
)
from citas.infrastructure.serializers.appointment_serializers import (
    UsuarioSerializer, UsuarioCreateSerializer,
    CitaSerializer, CitaCreateSerializer, CitaUpdateSerializer,
    EspecialidadSerializer, EPSSerializer,
    OrdenMedicaSerializer, OrdenMedicaCreateSerializer,
    AutorizacionEPSSerializer, AutorizacionEPSCreateSerializer,
    HistoriaClinicaSerializer, HistoriaClinicaCreateSerializer,
    ItemRecetaSerializer, OrdenLaboratorioSerializer,
)

Usuario = get_user_model()
HORA_INICIO = time(8, 0)
HORA_FIN = time(18, 0)
DURACION_CITA = timedelta(minutes=30)


class AuthRegisterView(APIView):
    permission_classes = [AllowAny]
    MAX_ADMINS = 5

    def post(self, request):
        serializer = UsuarioCreateSerializer(data=request.data)
        if serializer.is_valid():
            rol = serializer.validated_data.get('rol', 'paciente')

            if rol == 'admin':
                admin_count = Usuario.objects.filter(rol='admin').count()
                if admin_count >= self.MAX_ADMINS:
                    return Response(
                        {'error': f'No se pueden crear más de {self.MAX_ADMINS} administradores.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            usuario_repo = UsuarioRepository()
            use_case = RegisterUserUseCase(usuario_repo)
            try:
                usuario = use_case.execute(
                    first_name=serializer.validated_data['first_name'],
                    last_name=serializer.validated_data.get('last_name', ''),
                    email=serializer.validated_data['email'],
                    password=serializer.validated_data['password'],
                    rol=rol,
                    telefono=serializer.validated_data.get('telefono', ''),
                    tipo_documento=serializer.validated_data.get('tipo_documento', 'CC'),
                    numero_documento=serializer.validated_data.get('numero_documento'),
                    eps_id=serializer.validated_data.get('eps_id'),
                    regimen=serializer.validated_data.get('regimen'),
                )
                return Response(UsuarioSerializer(usuario).data, status=status.HTTP_201_CREATED)
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UsuarioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.rol == 'admin':
            usuarios = Usuario.objects.select_related('especialidad', 'eps').all()
            return Response(UsuarioSerializer(usuarios, many=True).data)
        return Response(UsuarioSerializer(request.user).data)

    def put(self, request):
        if request.user.rol != 'admin':
            return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)

        usuario_id = request.data.get('id')
        try:
            usuario = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        for field in ['first_name', 'last_name', 'email', 'telefono', 'tipo_documento',
                      'numero_documento', 'regimen']:
            if field in request.data:
                setattr(usuario, field, request.data[field])
        if 'eps_id' in request.data:
            usuario.eps_id = request.data['eps_id'] or None
        if 'is_active' in request.data:
            usuario.is_active = request.data['is_active']

        usuario.save()
        return Response(UsuarioSerializer(usuario).data)

    def delete(self, request):
        if request.user.rol != 'admin':
            return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)

        usuario_id = request.query_params.get('id')
        try:
            usuario = Usuario.objects.get(id=usuario_id, rol='paciente')
            usuario.delete()
            return Response({'message': 'Paciente eliminado'})
        except Usuario.DoesNotExist:
            return Response({'error': 'Paciente no encontrado'}, status=status.HTTP_404_NOT_FOUND)


class MedicoView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if hasattr(request.user, 'rol') and request.user.rol == 'admin':
            medicos = Usuario.objects.filter(rol='medico')
        else:
            medicos = Usuario.objects.filter(rol='medico', is_active=True)

        especialidad_id = request.query_params.get('especialidad')
        if especialidad_id:
            medicos = medicos.filter(especialidad_id=especialidad_id)

        return Response(UsuarioSerializer(medicos.select_related('especialidad', 'eps'), many=True).data)

    def post(self, request):
        if request.user.rol != 'admin':
            return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)

        serializer = UsuarioCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                esp_id = request.data.get('especialidad_id') or None
                if esp_id:
                    esp_id = int(esp_id)

                usuario = Usuario.objects.create_user(
                    username=serializer.validated_data['email'],
                    email=serializer.validated_data['email'],
                    password=serializer.validated_data['password'],
                    first_name=serializer.validated_data['first_name'],
                    last_name=serializer.validated_data.get('last_name', ''),
                    telefono=serializer.validated_data.get('telefono', ''),
                    rol='medico',
                    especialidad_id=esp_id,
                )
                return Response(UsuarioSerializer(usuario).data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        if request.user.rol != 'admin':
            return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)

        medico_id = request.data.get('id')
        try:
            medico = Usuario.objects.get(id=medico_id, rol='medico')
        except Usuario.DoesNotExist:
            return Response({'error': 'Médico no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        for field in ['first_name', 'last_name', 'email', 'telefono']:
            if field in request.data:
                setattr(medico, field, request.data[field])
        if 'especialidad_id' in request.data:
            esp_val = request.data['especialidad_id']
            medico.especialidad_id = int(esp_val) if esp_val else None
        if 'is_active' in request.data:
            val = request.data['is_active']
            medico.is_active = val if isinstance(val, bool) else val.lower() == 'true'
        if 'password' in request.data:
            medico.set_password(request.data['password'])

        medico.save()
        return Response(UsuarioSerializer(medico).data)

    def delete(self, request):
        if request.user.rol != 'admin':
            return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)

        medico_id = request.query_params.get('id')
        try:
            medico = Usuario.objects.get(id=medico_id, rol='medico')
            medico.delete()
            return Response({'message': 'Médico eliminado'})
        except Usuario.DoesNotExist:
            return Response({'error': 'Médico no encontrado'}, status=status.HTTP_404_NOT_FOUND)


class DisponibilidadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            medico_id = int(request.query_params.get('medico_id'))
            fecha_str = request.query_params.get('fecha')
        except (TypeError, ValueError):
            return Response({'error': 'Parámetros inválidos'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            fecha = date.fromisoformat(fecha_str)
        except Exception:
            return Response({'error': 'Fecha inválida (formato: YYYY-MM-DD)'}, status=status.HTTP_400_BAD_REQUEST)

        if fecha < date.today():
            return Response({'error': 'No puedes reservar en fecha pasada'}, status=status.HTTP_400_BAD_REQUEST)

        if fecha.weekday() >= 5:
            return Response({'error': 'Solo días laborales'}, status=status.HTTP_400_BAD_REQUEST)

        citas_existentes = Cita.objects.filter(
            medico_id=medico_id,
            fecha=fecha,
            estado__in=['programada', 'completada']
        ).values_list('hora', flat=True)

        horarios = []
        hora_actual = HORA_INICIO
        while hora_actual < HORA_FIN:
            if hora_actual not in citas_existentes:
                horarios.append(hora_actual.strftime('%H:%M'))
            hora_actual = (timezone.datetime.combine(date.today(), hora_actual) + DURACION_CITA).time()

        return Response({
            'medico_id': medico_id,
            'fecha': fecha_str,
            'horarios_disponibles': horarios,
        })


class CitaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rol = request.user.rol
        qs = Cita.objects.select_related(
            'paciente__eps', 'medico__especialidad', 'orden_medica', 'autorizacion__eps'
        )
        tipo_cita = request.query_params.get('tipo_cita')

        if rol == 'paciente':
            citas = qs.filter(paciente=request.user).order_by('fecha', 'hora')
        elif rol == 'medico':
            fecha = request.query_params.get('fecha')
            citas = qs.filter(medico=request.user)
            if fecha:
                citas = citas.filter(fecha=fecha)
            citas = citas.order_by('fecha', 'hora')
        else:
            citas = qs.all().order_by('fecha', 'hora')
            eps_id = request.query_params.get('eps_id')
            regimen = request.query_params.get('regimen')
            if eps_id:
                citas = citas.filter(paciente__eps_id=eps_id)
            if regimen:
                citas = citas.filter(paciente__regimen=regimen)

        if tipo_cita:
            citas = citas.filter(tipo_cita=tipo_cita)

        return Response(CitaSerializer(citas, many=True).data)


class CitaCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if 'paciente_id' not in data and request.user.rol == 'paciente':
            data['paciente_id'] = request.user.id

        serializer = CitaCreateSerializer(data=data)
        if serializer.is_valid():
            from datetime import datetime
            try:
                hora_dt = datetime.strptime(str(serializer.validated_data['hora']), '%H:%M:%S').time()
            except Exception:
                hora_dt = serializer.validated_data['hora']

            fecha = serializer.validated_data['fecha']

            if fecha < date.today():
                return Response({'error': 'No puedes agendar en fecha pasada'}, status=status.HTTP_400_BAD_REQUEST)

            if fecha.weekday() >= 5:
                return Response({'error': 'Solo días laborales'}, status=status.HTTP_400_BAD_REQUEST)

            if hora_dt < HORA_INICIO or hora_dt >= HORA_FIN:
                return Response({'error': 'Horario fuera de atención (08:00–18:00)'}, status=status.HTTP_400_BAD_REQUEST)

            use_case = ScheduleAppointmentUseCase(CitaRepository())
            try:
                cita = use_case.execute(
                    paciente_id=serializer.validated_data['paciente_id'],
                    medico_id=serializer.validated_data['medico_id'],
                    fecha=fecha,
                    hora=hora_dt,
                    motivo=serializer.validated_data['motivo'],
                    tipo_cita=serializer.validated_data.get('tipo_cita', 'general'),
                    canal_solicitud=serializer.validated_data.get('canal_solicitud', 'web'),
                    orden_medica_id=serializer.validated_data.get('orden_medica_id'),
                    autorizacion_id=serializer.validated_data.get('autorizacion_id'),
                )
                return Response(CitaSerializer(cita).data, status=status.HTTP_201_CREATED)
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_409_CONFLICT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CitaDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            cita = Cita.objects.select_related(
                'paciente__eps', 'medico__especialidad', 'orden_medica', 'autorizacion__eps'
            ).get(pk=pk)
            if not self._puede_acceder(request.user, cita):
                return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)
            return Response(CitaSerializer(cita).data)
        except Cita.DoesNotExist:
            return Response({'error': 'Cita no encontrada'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            cita = Cita.objects.get(pk=pk)
            if not self._puede_acceder(request.user, cita):
                return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)
        except Cita.DoesNotExist:
            return Response({'error': 'Cita no encontrada'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CitaUpdateSerializer(data=request.data)
        if serializer.is_valid():
            if 'estado' in serializer.validated_data:
                cita.estado = serializer.validated_data['estado']
            if 'observaciones' in serializer.validated_data:
                cita.observaciones = serializer.validated_data['observaciones']
            if 'fecha' in serializer.validated_data:
                cita.fecha = serializer.validated_data['fecha']
            if 'hora' in serializer.validated_data:
                cita.hora = serializer.validated_data['hora']
            cita.save()
            return Response(CitaSerializer(cita).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            cita = Cita.objects.get(pk=pk)
            if not self._puede_acceder(request.user, cita):
                return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)
        except Cita.DoesNotExist:
            return Response({'error': 'Cita no encontrada'}, status=status.HTTP_404_NOT_FOUND)

        use_case = CancelAppointmentUseCase(CitaRepository())
        if use_case.execute(pk):
            return Response({'message': 'Cita cancelada'})
        return Response({'error': 'No se pudo cancelar'}, status=status.HTTP_400_BAD_REQUEST)

    def _puede_acceder(self, usuario, cita):
        if usuario.rol == 'admin':
            return True
        if usuario.rol == 'medico':
            return cita.medico_id == usuario.id
        if usuario.rol == 'paciente':
            return cita.paciente_id == usuario.id
        return False


class EspecialidadView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(EspecialidadSerializer(Especialidad.objects.all(), many=True).data)

    def post(self, request):
        if request.user.rol != 'admin':
            return Response({'error': 'Solo administradores'}, status=status.HTTP_403_FORBIDDEN)
        serializer = EspecialidadSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EspecialidadDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            return Response(EspecialidadSerializer(Especialidad.objects.get(pk=pk)).data)
        except Especialidad.DoesNotExist:
            return Response({'error': 'Especialidad no encontrada'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        if request.user.rol != 'admin':
            return Response({'error': 'Solo administradores'}, status=status.HTTP_403_FORBIDDEN)
        try:
            especialidad = Especialidad.objects.get(pk=pk)
        except Especialidad.DoesNotExist:
            return Response({'error': 'Especialidad no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        serializer = EspecialidadSerializer(especialidad, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if request.user.rol != 'admin':
            return Response({'error': 'Solo administradores'}, status=status.HTTP_403_FORBIDDEN)
        try:
            Especialidad.objects.get(pk=pk).delete()
            return Response({'message': 'Especialidad eliminada'})
        except Especialidad.DoesNotExist:
            return Response({'error': 'Especialidad no encontrada'}, status=status.HTTP_404_NOT_FOUND)


class EPSView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        solo_activas = request.query_params.get('activas', 'true').lower() == 'true'
        qs = EPS.objects.filter(activa=True) if solo_activas else EPS.objects.all()
        return Response(EPSSerializer(qs.order_by('nombre'), many=True).data)

    def post(self, request):
        if not hasattr(request.user, 'rol') or request.user.rol != 'admin':
            return Response({'error': 'Solo administradores'}, status=status.HTTP_403_FORBIDDEN)
        serializer = EPSSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EPSDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            return Response(EPSSerializer(EPS.objects.get(pk=pk)).data)
        except EPS.DoesNotExist:
            return Response({'error': 'EPS no encontrada'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        if request.user.rol != 'admin':
            return Response({'error': 'Solo administradores'}, status=status.HTTP_403_FORBIDDEN)
        try:
            eps = EPS.objects.get(pk=pk)
        except EPS.DoesNotExist:
            return Response({'error': 'EPS no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        serializer = EPSSerializer(eps, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if request.user.rol != 'admin':
            return Response({'error': 'Solo administradores'}, status=status.HTTP_403_FORBIDDEN)
        try:
            EPS.objects.get(pk=pk).delete()
            return Response({'message': 'EPS eliminada'})
        except EPS.DoesNotExist:
            return Response({'error': 'EPS no encontrada'}, status=status.HTTP_404_NOT_FOUND)


class OrdenMedicaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        repo = OrdenMedicaRepository()
        if request.user.rol == 'paciente':
            ordenes = repo.get_by_paciente(request.user.id)
        elif request.user.rol == 'medico':
            ordenes = OrdenMedica.objects.filter(
                medico_solicitante=request.user
            ).select_related('paciente', 'especialidad_solicitada').order_by('-creado_en')
        else:
            solo_pendientes = request.query_params.get('pendientes', 'false').lower() == 'true'
            ordenes = repo.get_pendientes() if solo_pendientes else repo.get_all()
        return Response(OrdenMedicaSerializer(ordenes, many=True).data)

    def post(self, request):
        if request.user.rol not in ('medico', 'admin'):
            return Response({'error': 'Solo médicos o administradores'}, status=status.HTTP_403_FORBIDDEN)

        serializer = OrdenMedicaCreateSerializer(data=request.data)
        if serializer.is_valid():
            use_case = CreateOrdenMedicaUseCase()
            try:
                orden = use_case.execute(
                    paciente_id=serializer.validated_data['paciente_id'],
                    medico_solicitante_id=request.user.id,
                    especialidad_solicitada_id=serializer.validated_data['especialidad_solicitada_id'],
                    cita_origen_id=serializer.validated_data.get('cita_origen_id'),
                    vigencia_dias=serializer.validated_data.get('vigencia_dias', 30),
                    observaciones=serializer.validated_data.get('observaciones', ''),
                )
                return Response(OrdenMedicaSerializer(orden).data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrdenMedicaDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            orden = OrdenMedica.objects.select_related(
                'paciente', 'medico_solicitante', 'especialidad_solicitada'
            ).get(pk=pk)
            return Response(OrdenMedicaSerializer(orden).data)
        except OrdenMedica.DoesNotExist:
            return Response({'error': 'Orden no encontrada'}, status=status.HTTP_404_NOT_FOUND)


class AutorizarOrdenView(APIView):
    """Admin registra la autorización EPS para una orden médica pendiente."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.rol != 'admin':
            return Response({'error': 'Solo administradores'}, status=status.HTTP_403_FORBIDDEN)

        serializer = AutorizacionEPSCreateSerializer(data={**request.data, 'orden_id': pk})
        if serializer.is_valid():
            use_case = RegisterAutorizacionEPSUseCase()
            try:
                autorizacion = use_case.execute(
                    orden_id=pk,
                    eps_id=serializer.validated_data['eps_id'],
                    numero_autorizacion=serializer.validated_data['numero_autorizacion'],
                    fecha_autorizacion=serializer.validated_data['fecha_autorizacion'],
                    fecha_vigencia=serializer.validated_data['fecha_vigencia'],
                    servicios_autorizados=serializer.validated_data.get('servicios_autorizados', ''),
                )
                return Response(AutorizacionEPSSerializer(autorizacion).data, status=status.HTTP_201_CREATED)
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class HistoriaClinicaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rol = request.user.rol
        if rol == 'medico':
            qs = HistoriaClinica.objects.filter(medico=request.user).select_related('paciente','cita').prefetch_related('receta','laboratorios').order_by('-creado_en')
        elif rol == 'paciente':
            qs = HistoriaClinica.objects.filter(paciente=request.user).select_related('medico','cita').prefetch_related('receta','laboratorios').order_by('-creado_en')
        elif rol == 'admin':
            qs = HistoriaClinica.objects.all().select_related('medico','paciente','cita').prefetch_related('receta','laboratorios').order_by('-creado_en')
            pid = request.query_params.get('paciente_id')
            if pid:
                qs = qs.filter(paciente_id=pid)
        else:
            return Response([], status=status.HTTP_200_OK)
        return Response(HistoriaClinicaSerializer(qs, many=True).data)

    def post(self, request):
        if request.user.rol != 'medico':
            return Response({'error': 'Solo médicos'}, status=status.HTTP_403_FORBIDDEN)
        ser = HistoriaClinicaCreateSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        data = ser.validated_data
        try:
            cita = Cita.objects.get(pk=data['cita_id'], medico=request.user)
        except Cita.DoesNotExist:
            return Response({'error': 'Cita no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        if hasattr(cita, 'historia_clinica'):
            return Response({'error': 'Esta cita ya tiene historia clínica'}, status=status.HTTP_400_BAD_REQUEST)
        hc = HistoriaClinica.objects.create(
            cita=cita, medico=request.user, paciente=cita.paciente,
            motivo_consulta=data['motivo_consulta'],
            enfermedad_actual=data.get('enfermedad_actual',''),
            antecedentes_personales=data.get('antecedentes_personales',''),
            revision_sistemas=data.get('revision_sistemas',''),
            tension_arterial=data.get('tension_arterial',''),
            frecuencia_cardiaca=data.get('frecuencia_cardiaca'),
            frecuencia_respiratoria=data.get('frecuencia_respiratoria'),
            temperatura=data.get('temperatura'),
            peso_kg=data.get('peso_kg'),
            talla_cm=data.get('talla_cm'),
            saturacion_o2=data.get('saturacion_o2'),
            examen_fisico=data.get('examen_fisico',''),
            diagnostico_principal=data['diagnostico_principal'],
            codigo_cie10=data.get('codigo_cie10',''),
            tipo_diagnostico=data.get('tipo_diagnostico','presuntivo'),
            conducta=data.get('conducta',''),
            indicaciones=data.get('indicaciones',''),
            proximo_control=data.get('proximo_control'),
        )
        for item in data.get('receta', []):
            ItemReceta.objects.create(historia_clinica=hc, **item)
        for lab in data.get('laboratorios', []):
            OrdenLaboratorio.objects.create(historia_clinica=hc, **lab)
        cita.estado = 'completada'
        cita.save(update_fields=['estado'])
        return Response(HistoriaClinicaSerializer(hc).data, status=status.HTTP_201_CREATED)


class HistoriaClinicaDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            hc = HistoriaClinica.objects.prefetch_related('receta','laboratorios').select_related('medico','paciente','cita').get(pk=pk)
        except HistoriaClinica.DoesNotExist:
            return Response({'error': 'No encontrada'}, status=status.HTTP_404_NOT_FOUND)
        if request.user.rol == 'paciente' and hc.paciente != request.user:
            return Response({'error': 'Sin acceso'}, status=status.HTTP_403_FORBIDDEN)
        if request.user.rol == 'medico' and hc.medico != request.user:
            return Response({'error': 'Sin acceso'}, status=status.HTTP_403_FORBIDDEN)
        return Response(HistoriaClinicaSerializer(hc).data)


class HistoriaClinicaByCitaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            cita = Cita.objects.get(pk=pk)
        except Cita.DoesNotExist:
            return Response({'error': 'Cita no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        if request.user.rol == 'paciente' and cita.paciente != request.user:
            return Response({'error': 'Sin acceso'}, status=status.HTTP_403_FORBIDDEN)
        if request.user.rol == 'medico' and cita.medico != request.user:
            return Response({'error': 'Sin acceso'}, status=status.HTTP_403_FORBIDDEN)
        try:
            hc = HistoriaClinica.objects.prefetch_related('receta','laboratorios').get(cita=cita)
            return Response(HistoriaClinicaSerializer(hc).data)
        except HistoriaClinica.DoesNotExist:
            return Response(None, status=status.HTTP_200_OK)
