from rest_framework import serializers
from django.contrib.auth import get_user_model
from citas.models import Cita, Especialidad, EPS, OrdenMedica, AutorizacionEPS, HistoriaClinica, ItemReceta, OrdenLaboratorio

Usuario = get_user_model()


class EPSSerializer(serializers.ModelSerializer):
    class Meta:
        model = EPS
        fields = ['id', 'nombre', 'codigo_rnos', 'activa']
        read_only_fields = ['id']


class EspecialidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Especialidad
        fields = ['id', 'nombre', 'descripcion', 'creado_en']
        read_only_fields = ['id', 'creado_en']


class UsuarioSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(source='get_full_name', read_only=True)
    especialidad = serializers.SerializerMethodField()
    eps = EPSSerializer(read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'nombre', 'first_name', 'last_name', 'email',
            'rol', 'telefono', 'fecha_nacimiento', 'date_joined', 'especialidad',
            'is_active', 'tipo_documento', 'numero_documento', 'eps', 'regimen',
        ]
        read_only_fields = ['id', 'date_joined']

    def get_especialidad(self, obj):
        if obj.especialidad:
            return {'id': obj.especialidad.id, 'nombre': obj.especialidad.nombre}
        return None


class UsuarioCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    username = serializers.CharField(required=False)
    eps_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Usuario
        fields = [
            'username', 'first_name', 'last_name', 'email', 'password', 'rol',
            'telefono', 'fecha_nacimiento', 'tipo_documento', 'numero_documento',
            'eps_id', 'regimen',
        ]
        extra_kwargs = {
            'telefono': {'required': False},
            'fecha_nacimiento': {'required': False},
            'tipo_documento': {'required': False},
            'numero_documento': {'required': False},
            'regimen': {'required': False},
        }

    def validate(self, attrs):
        if 'username' not in attrs and 'email' in attrs:
            attrs['username'] = attrs['email'].split('@')[0]
            base_username = attrs['username']
            counter = 1
            while Usuario.objects.filter(username=attrs['username']).exists():
                attrs['username'] = f"{base_username}{counter}"
                counter += 1
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        usuario = Usuario(**validated_data)
        usuario.set_password(password)
        usuario.save()
        return usuario


class AutorizacionEPSSerializer(serializers.ModelSerializer):
    eps = EPSSerializer(read_only=True)

    class Meta:
        model = AutorizacionEPS
        fields = [
            'id', 'numero_autorizacion', 'eps', 'fecha_autorizacion',
            'fecha_vigencia', 'estado', 'servicios_autorizados', 'creado_en',
        ]
        read_only_fields = ['id', 'creado_en']


class AutorizacionEPSCreateSerializer(serializers.Serializer):
    orden_id = serializers.IntegerField()
    eps_id = serializers.IntegerField()
    numero_autorizacion = serializers.CharField(max_length=50)
    fecha_autorizacion = serializers.DateField()
    fecha_vigencia = serializers.DateField()
    servicios_autorizados = serializers.CharField(required=False, allow_blank=True, default='')


class OrdenMedicaSerializer(serializers.ModelSerializer):
    paciente = UsuarioSerializer(read_only=True)
    medico_solicitante = UsuarioSerializer(read_only=True)
    especialidad_solicitada = EspecialidadSerializer(read_only=True)
    autorizacion = AutorizacionEPSSerializer(read_only=True)

    class Meta:
        model = OrdenMedica
        fields = [
            'id', 'paciente', 'medico_solicitante', 'especialidad_solicitada',
            'cita_origen_id', 'fecha_emision', 'vigencia_dias', 'estado',
            'observaciones', 'autorizacion', 'creado_en',
        ]
        read_only_fields = ['id', 'fecha_emision', 'creado_en']


class OrdenMedicaCreateSerializer(serializers.Serializer):
    paciente_id = serializers.IntegerField()
    especialidad_solicitada_id = serializers.IntegerField()
    cita_origen_id = serializers.IntegerField(required=False, allow_null=True)
    vigencia_dias = serializers.IntegerField(required=False, default=30)
    observaciones = serializers.CharField(required=False, allow_blank=True, default='')


class CitaSerializer(serializers.ModelSerializer):
    paciente = UsuarioSerializer(read_only=True)
    medico = UsuarioSerializer(read_only=True)
    orden_medica = OrdenMedicaSerializer(read_only=True)
    autorizacion = AutorizacionEPSSerializer(read_only=True)

    class Meta:
        model = Cita
        fields = [
            'id', 'paciente', 'medico', 'fecha', 'hora', 'estado', 'tipo_cita',
            'motivo', 'observaciones', 'orden_medica', 'autorizacion',
            'cuota_moderadora', 'exento_cuota', 'canal_solicitud', 'creado_en',
        ]
        read_only_fields = ['id', 'creado_en', 'cuota_moderadora', 'exento_cuota']


class CitaCreateSerializer(serializers.Serializer):
    paciente_id = serializers.IntegerField()
    medico_id = serializers.IntegerField()
    fecha = serializers.DateField()
    hora = serializers.TimeField()
    motivo = serializers.CharField(max_length=500)
    tipo_cita = serializers.ChoiceField(
        choices=['general', 'especializada', 'prioritaria'],
        default='general',
    )
    canal_solicitud = serializers.ChoiceField(
        choices=['web', 'whatsapp', 'telefonica', 'presencial'],
        default='web',
    )
    orden_medica_id = serializers.IntegerField(required=False, allow_null=True)
    autorizacion_id = serializers.IntegerField(required=False, allow_null=True)


class ItemRecetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemReceta
        fields = ['id', 'medicamento', 'concentracion', 'forma_farmaceutica',
                  'dosis', 'frecuencia', 'duracion', 'cantidad', 'indicaciones']


class OrdenLaboratorioSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdenLaboratorio
        fields = ['id', 'examen', 'indicacion', 'urgente']


class HistoriaClinicaSerializer(serializers.ModelSerializer):
    receta = ItemRecetaSerializer(many=True, read_only=True)
    laboratorios = OrdenLaboratorioSerializer(many=True, read_only=True)
    medico_nombre = serializers.CharField(source='medico.get_full_name', read_only=True)
    paciente_nombre = serializers.CharField(source='paciente.get_full_name', read_only=True)

    class Meta:
        model = HistoriaClinica
        fields = [
            'id', 'cita', 'medico', 'medico_nombre', 'paciente', 'paciente_nombre',
            'motivo_consulta', 'enfermedad_actual', 'antecedentes_personales', 'revision_sistemas',
            'tension_arterial', 'frecuencia_cardiaca', 'frecuencia_respiratoria',
            'temperatura', 'peso_kg', 'talla_cm', 'saturacion_o2',
            'examen_fisico',
            'diagnostico_principal', 'codigo_cie10', 'tipo_diagnostico',
            'conducta', 'indicaciones', 'proximo_control',
            'receta', 'laboratorios',
            'creado_en', 'actualizado_en',
        ]
        read_only_fields = ['id', 'medico', 'paciente', 'creado_en', 'actualizado_en']


class HistoriaClinicaCreateSerializer(serializers.Serializer):
    cita_id = serializers.IntegerField()
    motivo_consulta = serializers.CharField()
    enfermedad_actual = serializers.CharField(required=False, allow_blank=True, default='')
    antecedentes_personales = serializers.CharField(required=False, allow_blank=True, default='')
    revision_sistemas = serializers.CharField(required=False, allow_blank=True, default='')
    tension_arterial = serializers.CharField(required=False, allow_blank=True, default='')
    frecuencia_cardiaca = serializers.IntegerField(required=False, allow_null=True)
    frecuencia_respiratoria = serializers.IntegerField(required=False, allow_null=True)
    temperatura = serializers.DecimalField(max_digits=4, decimal_places=1, required=False, allow_null=True)
    peso_kg = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    talla_cm = serializers.DecimalField(max_digits=5, decimal_places=1, required=False, allow_null=True)
    saturacion_o2 = serializers.IntegerField(required=False, allow_null=True)
    examen_fisico = serializers.CharField(required=False, allow_blank=True, default='')
    diagnostico_principal = serializers.CharField()
    codigo_cie10 = serializers.CharField(required=False, allow_blank=True, default='')
    tipo_diagnostico = serializers.ChoiceField(
        choices=['confirmado', 'presuntivo', 'descartado'], default='presuntivo'
    )
    conducta = serializers.CharField(required=False, allow_blank=True, default='')
    indicaciones = serializers.CharField(required=False, allow_blank=True, default='')
    proximo_control = serializers.DateField(required=False, allow_null=True)
    receta = ItemRecetaSerializer(many=True, required=False, default=[])
    laboratorios = OrdenLaboratorioSerializer(many=True, required=False, default=[])


class CitaUpdateSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(
        choices=['programada', 'pendiente_autorizacion', 'completada', 'cancelada', 'no_asistio'],
        required=False,
    )
    observaciones = serializers.CharField(required=False, allow_blank=True)
    fecha = serializers.DateField(required=False)
    hora = serializers.TimeField(required=False)
