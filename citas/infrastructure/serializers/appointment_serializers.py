from rest_framework import serializers
from django.contrib.auth import get_user_model
from citas.models import Cita, Especialidad

Usuario = get_user_model()


class UsuarioSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(source='get_full_name', read_only=True)
    especialidad = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'nombre', 'first_name', 'last_name', 'email', 'rol', 'telefono', 'fecha_nacimiento', 'date_joined', 'especialidad', 'is_active']
        read_only_fields = ['id', 'date_joined']

    def get_especialidad(self, obj):
        if obj.especialidad:
            return {'id': obj.especialidad.id, 'nombre': obj.especialidad.nombre}
        return None


class UsuarioCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    username = serializers.CharField(required=False)

    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'rol', 'telefono', 'fecha_nacimiento']
        extra_kwargs = {
            'telefono': {'required': False},
            'fecha_nacimiento': {'required': False},
        }

    def validate(self, attrs):
        if 'username' not in attrs and 'email' in attrs:
            # Generate a username from the email if not provided
            attrs['username'] = attrs['email'].split('@')[0]
            # Ensure uniqueness (simple approach)
            base_username = attrs['username']
            counter = 1
            while Usuario.objects.filter(username=attrs['username']).exists():
                attrs['username'] = f"{base_username}{counter}"
                counter += 1
        return attrs

    def create(self, validated_data):
        from django.contrib.auth.hashers import make_password
        validated_data['password_hash'] = make_password(validated_data.pop('password'))
        return super().create(validated_data)


class CitaSerializer(serializers.ModelSerializer):
    paciente = UsuarioSerializer(read_only=True)
    medico = UsuarioSerializer(read_only=True)

    class Meta:
        model = Cita
        fields = ['id', 'paciente', 'medico', 'fecha', 'hora', 'estado', 'motivo', 'observaciones', 'creado_en']
        read_only_fields = ['id', 'creado_en', 'estado']


class CitaCreateSerializer(serializers.Serializer):
    paciente_id = serializers.IntegerField()
    medico_id = serializers.IntegerField()
    fecha = serializers.DateField()
    hora = serializers.TimeField()
    motivo = serializers.CharField(max_length=500)


class CitaUpdateSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=['programada', 'completada', 'cancelada', 'no_asistio'], required=False)
    observaciones = serializers.CharField(required=False, allow_blank=True)
    fecha = serializers.DateField(required=False)
    hora = serializers.TimeField(required=False)


class EspecialidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Especialidad
        fields = ['id', 'nombre', 'descripcion', 'creado_en']
        read_only_fields = ['id', 'creado_en']