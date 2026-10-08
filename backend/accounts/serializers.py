from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

Usuario = get_user_model()


def validar_contrasena(clave, usuario):
    """
    Aplica los validadores de AUTH_PASSWORD_VALIDATORS (settings.py): longitud
    mínima, contraseñas comunes, solo números y parecido con los datos del usuario
    (auditoría I-11). Convierte el error de Django en un error de DRF (400).
    """
    try:
        validate_password(clave, user=usuario)
    except DjangoValidationError as error:
        raise serializers.ValidationError(list(error.messages))


class UsuarioSerializer(serializers.ModelSerializer):
    """Perfil de usuario. Se usa en el login, la lista de usuarios y /api/auth/perfil/."""

    class Meta:
        model = Usuario
        fields = [
            'id',
            'username',
            'email',
            'nombre_completo',
            'rol',
            'telefono',
            'especialidad',
            'registro_medico',
            'activo',
            'fecha_creacion',
        ]
        # username, rol y activo son de solo lectura para que nadie pueda
        # cambiárselos a sí mismo desde /api/auth/perfil/ (auditoría C-1). El registro
        # médico tampoco: con uno falso se firmarían informes (decisión D-8).
        read_only_fields = ['id', 'username', 'rol', 'registro_medico', 'activo', 'fecha_creacion']


class RegistroSerializer(serializers.ModelSerializer):
    """User registration serializer."""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = [
            'username',
            'email',
            'password',
            'password_confirm',
            'nombre_completo',
            'rol',
            'telefono',
            'especialidad',
            'registro_medico',
        ]

    def validate(self, data):
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError({'password_confirm': 'Las contraseñas no coinciden.'})
        # Usuario temporal SIN guardar: el validador de "parecida al usuario"
        # necesita sus datos, y el usuario todavía no existe.
        usuario_temporal = Usuario(
            username=data.get('username', ''),
            email=data.get('email', ''),
            nombre_completo=data.get('nombre_completo', ''),
        )
        try:
            validar_contrasena(data['password'], usuario_temporal)
        except serializers.ValidationError as error:
            raise serializers.ValidationError({'password': error.detail})
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Usuario(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CambiarPasswordSerializer(serializers.Serializer):
    """Change password serializer."""

    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('La contraseña actual es incorrecta.')
        return value

    def validate_new_password(self, value):
        validar_contrasena(value, self.context['request'].user)
        return value

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
