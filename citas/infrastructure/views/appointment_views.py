from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, time, timedelta

from citas.models import Cita, Especialidad
from citas.application.use_cases.manage_appointments import (
    ScheduleAppointmentUseCase, CancelAppointmentUseCase,
    UpdateAppointmentStatusUseCase, GetAppointmentsByPatientUseCase,
    GetAppointmentsByDoctorUseCase
)
from citas.application.use_cases.manage_users import RegisterUserUseCase
from citas.infrastructure.adapters.django_repositories import CitaRepository, UsuarioRepository, EspecialidadRepository
from citas.infrastructure.serializers.appointment_serializers import (
    UsuarioSerializer, UsuarioCreateSerializer,
    CitaSerializer, CitaCreateSerializer, CitaUpdateSerializer,
    EspecialidadSerializer
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
                        {'error': f'No se pueden crear más de {self.MAX_ADMINS} administradores. Contacte al soporte.'},
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
                    telefono=serializer.validated_data.get('telefono', '')
                )
                return Response(UsuarioSerializer(usuario).data, status=status.HTTP_201_CREATED)
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UsuarioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Si es admin, devuelve todos los usuarios
        if request.user.rol == 'admin':
            usuarios = Usuario.objects.all()
            return Response(UsuarioSerializer(usuarios, many=True).data)
        
        # Si no es admin, solo devuelve el usuario actual
        return Response(UsuarioSerializer(request.user).data)

    def put(self, request):
        if request.user.rol != 'admin':
            return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)
        
        usuario_id = request.data.get('id')
        try:
            usuario = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
        if 'first_name' in request.data:
            usuario.first_name = request.data['first_name']
        if 'last_name' in request.data:
            usuario.last_name = request.data['last_name']
        if 'email' in request.data:
            usuario.email = request.data['email']
        if 'telefono' in request.data:
            usuario.telefono = request.data['telefono']
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
    permission_classes = [AllowAny]  # GET público sin auth

    def get(self, request):
        if hasattr(request.user, 'rol') and request.user.rol == 'admin':
            medicos = Usuario.objects.filter(rol='medico')
        else:
            medicos = Usuario.objects.filter(rol='medico', is_active=True)
        
        especialidad_id = request.query_params.get('especialidad')
        if especialidad_id:
            medicos = medicos.filter(especialidad_id=especialidad_id)
            
        return Response(UsuarioSerializer(medicos, many=True).data)

    def post(self, request):
        if request.user.rol != 'admin':
            return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = UsuarioCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                esp_id_raw = request.data.get('especialidad_id')
                esp_id = None
                if esp_id_raw and esp_id_raw != '':
                    try:
                        esp_id = int(esp_id_raw)
                    except:
                        esp_id = None
                
                usuario = Usuario.objects.create_user(
                    username=serializer.validated_data['email'],
                    email=serializer.validated_data['email'],
                    password=serializer.validated_data['password'],
                    first_name=serializer.validated_data['first_name'],
                    last_name=serializer.validated_data.get('last_name', ''),
                    telefono=serializer.validated_data.get('telefono', ''),
                    rol='medico',
                    especialidad_id=esp_id
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
        
        if 'first_name' in request.data:
            medico.first_name = request.data['first_name']
        if 'last_name' in request.data:
            medico.last_name = request.data['last_name']
        if 'email' in request.data:
            medico.email = request.data['email']
        if 'telefono' in request.data:
            medico.telefono = request.data['telefono']
        if 'especialidad_id' in request.data:
            esp_val = request.data['especialidad_id']
            if esp_val and esp_val != '':
                try:
                    medico.especialidad_id = int(esp_val)
                except:
                    pass
            else:
                medico.especialidad_id = None
        if 'is_active' in request.data:
            val = request.data['is_active']
            if isinstance(val, str):
                val = val.lower() == 'true'
            medico.is_active = bool(val)
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
        except:
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
            'horarios_disponibles': horarios
        })


class CitaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rol = request.user.rol
        if rol == 'paciente':
            use_case = GetAppointmentsByPatientUseCase(CitaRepository())
            citas = use_case.execute(request.user.id)
        elif rol == 'medico':
            fecha = request.query_params.get('fecha')
            use_case = GetAppointmentsByDoctorUseCase(CitaRepository())
            citas = use_case.execute(request.user.id, fecha)
        else:
            citas = Cita.objects.all()
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
            except:
                hora_dt = serializer.validated_data['hora']
            
            fecha = serializer.validated_data['fecha']
            
            if fecha < date.today():
                return Response({'error': 'No puedes agendar en fecha pasada'}, status=status.HTTP_400_BAD_REQUEST)
            
            if fecha.weekday() >= 5:
                return Response({'error': 'Solo días laborales'}, status=status.HTTP_400_BAD_REQUEST)
            
            if hora_dt < HORA_INICIO or hora_dt >= HORA_FIN:
                return Response({'error': 'Horario fuera de atención'}, status=status.HTTP_400_BAD_REQUEST)
            
            use_case = ScheduleAppointmentUseCase(CitaRepository())
            try:
                cita = use_case.execute(
                    paciente_id=serializer.validated_data['paciente_id'],
                    medico_id=serializer.validated_data['medico_id'],
                    fecha=fecha,
                    hora=hora_dt,
                    motivo=serializer.validated_data['motivo']
                )
                return Response(CitaSerializer(cita).data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_409_CONFLICT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CitaDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            cita = Cita.objects.get(pk=pk)
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
            estado = serializer.validated_data.get('estado')
            observaciones = serializer.validated_data.get('observaciones', '')
            nueva_fecha = serializer.validated_data.get('fecha')
            nueva_hora = serializer.validated_data.get('hora')
            
            if estado:
                cita.estado = estado
            if observaciones:
                cita.observaciones = observaciones
            
            if nueva_fecha or nueva_hora:
                if nueva_fecha:
                    cita.fecha = nueva_fecha
                if nueva_hora:
                    cita.hora = nueva_hora
            
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
    permission_classes = [AllowAny]  # GET público para pacientes

    def get(self, request):
        especialidades = Especialidad.objects.all()
        return Response(EspecialidadSerializer(especialidades, many=True).data)

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
            especialidad = Especialidad.objects.get(pk=pk)
            return Response(EspecialidadSerializer(especialidad).data)
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
            especialidad = Especialidad.objects.get(pk=pk)
            especialidad.delete()
            return Response({'message': 'Especialidad eliminada'})
        except Especialidad.DoesNotExist:
            return Response({'error': 'Especialidad no encontrada'}, status=status.HTTP_404_NOT_FOUND)