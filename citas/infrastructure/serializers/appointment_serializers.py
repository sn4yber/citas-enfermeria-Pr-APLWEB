from rest_framework import serializers
from django.contrib.auth import get_user_model
from citas.models import Cita, Especialidad

Usuario = get_user_model()


class UsuarioSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'nombre', 'first_name', 'last_name', 'email', 'rol', 'telefono', 'fecha_nacimiento', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UsuarioCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'rol', 'telefono', 'fecha_nacimiento']

    def create(self, validated_data):
        from django.contrib.auth.hashers import make_password
        validated_data['password_hash'] = make_password(validated_data.pop('password'))
        return super().create(validated_data)


class CitaSerializer(serializers.ModelSerializer):
    paciente_nombre = serializers.CharField(source='paciente.nombre', read_only=True)
    medico_nombre = serializers.CharField(source='medico.nombre', read_only=True)

    class Meta:
        model = Cita
        fields = ['id', 'paciente', 'paciente_nombre', 'medico', 'medico_nombre', 'fecha', 'hora', 'estado', 'motivo', 'observaciones', 'creado_en']
        read_only_fields = ['id', 'creado_en', 'estado']


class CitaCreateSerializer(serializers.Serializer):
    paciente_id = serializers.IntegerField()
    medico_id = serializers.IntegerField()
    fecha = serializers.DateField()
    hora = serializers.TimeField()
    motivo = serializers.CharField(max_length=500)


class CitaUpdateSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=['programada', 'completada', 'cancelada', 'no_asistio'])
    observaciones = serializers.CharField(required=False, allow_blank=True)


class EspecialidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Especialidad
        fields = ['id', 'nombre', 'descripcion', 'creado_en']
        read_only_fields = ['id', 'creado_en']