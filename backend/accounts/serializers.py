from rest_framework import serializers
from django.contrib.auth import get_user_model

Usuario = get_user_model()


class UsuarioSerializer(serializers.ModelSerializer):
    """Read-only user profile serializer."""

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'nombre_completo',
            'rol', 'telefono', 'especialidad', 'activo', 'fecha_creacion',
        ]
        read_only_fields = ['id', 'fecha_creacion']


class RegistroSerializer(serializers.ModelSerializer):
    """User registration serializer."""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'nombre_completo', 'rol', 'telefono', 'especialidad',
        ]

    def validate(self, data):
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError({'password_confirm': 'Las contraseñas no coinciden.'})
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Usuario(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Login request serializer (for docs / validation only; JWT handled by SimpleJWT)."""
    username = serializers.CharField()
    password = serializers.CharField()


class CambiarPasswordSerializer(serializers.Serializer):
    """Change password serializer."""
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('La contraseña actual es incorrecta.')
        return value

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
