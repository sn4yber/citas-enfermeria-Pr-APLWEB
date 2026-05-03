from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model

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


class AuthRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UsuarioCreateSerializer(data=request.data)
        if serializer.is_valid():
            usuario_repo = UsuarioRepository()
            use_case = RegisterUserUseCase(usuario_repo)
            try:
                usuario = use_case.execute(
                    first_name=serializer.validated_data['first_name'],
                    email=serializer.validated_data['email'],
                    password=serializer.validated_data['password'],
                    rol=serializer.validated_data.get('rol', 'paciente'),
                    telefono=serializer.validated_data.get('telefono', '')
                )
                return Response(UsuarioSerializer(usuario).data, status=status.HTTP_201_CREATED)
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UsuarioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuarios = Usuario.objects.all()
        return Response(UsuarioSerializer(usuarios, many=True).data)


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
        serializer = CitaCreateSerializer(data=request.data)
        if serializer.is_valid():
            from datetime import datetime
            try:
                hora_dt = datetime.strptime(str(serializer.validated_data['hora']), '%H:%M:%S').time()
            except:
                hora_dt = serializer.validated_data['hora']

            use_case = ScheduleAppointmentUseCase(CitaRepository())
            try:
                cita = use_case.execute(
                    paciente_id=serializer.validated_data['paciente_id'],
                    medico_id=serializer.validated_data['medico_id'],
                    fecha=serializer.validated_data['fecha'],
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
            return Response(CitaSerializer(cita).data)
        except Cita.DoesNotExist:
            return Response({'error': 'Cita no encontrada'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            cita = Cita.objects.get(pk=pk)
        except Cita.DoesNotExist:
            return Response({'error': 'Cita no encontrada'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CitaUpdateSerializer(data=request.data)
        if serializer.is_valid():
            estado = serializer.validated_data.get('estado')
            observaciones = serializer.validated_data.get('observaciones', '')
            
            if estado:
                cita.estado = estado
            if observaciones:
                cita.observaciones = observaciones
            cita.save()
            return Response(CitaSerializer(cita).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        use_case = CancelAppointmentUseCase(CitaRepository())
        if use_case.execute(pk):
            return Response({'message': 'Cita cancelada'})
        return Response({'error': 'No se pudo cancelar'}, status=status.HTTP_400_BAD_REQUEST)


class EspecialidadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        especialidades = Especialidad.objects.all()
        return Response(EspecialidadSerializer(especialidades, many=True).data)

    def post(self, request):
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
        try:
            especialidad = Especialidad.objects.get(pk=pk)
            especialidad.delete()
            return Response({'message': 'Especialidad eliminada'})
        except Especialidad.DoesNotExist:
            return Response({'error': 'Especialidad no encontrada'}, status=status.HTTP_404_NOT_FOUND)