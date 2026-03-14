from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

from .serializers import RegistroSerializer, UsuarioSerializer, CambiarPasswordSerializer
from .permissions import EsAdmin

Usuario = get_user_model()


# ── Custom JWT token that includes user role ──────────────────────
class CustomTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['rol'] = user.rol
        token['nombre'] = user.nombre_completo or user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UsuarioSerializer(self.user).data
        return data


class CustomTokenView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer


# ── Registration (admin-only) ────────────────────────────────────
class RegistroView(generics.CreateAPIView):
    serializer_class = RegistroSerializer
    permission_classes = [EsAdmin]


# ── Profile ──────────────────────────────────────────────────────
class PerfilView(generics.RetrieveUpdateAPIView):
    serializer_class = UsuarioSerializer

    def get_object(self):
        return self.request.user


# ── Change password ──────────────────────────────────────────────
class CambiarPasswordView(APIView):
    def post(self, request):
        serializer = CambiarPasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Contraseña actualizada correctamente.'})


# ── List users (admin-only) ─────────────────────────────────────
class ListaUsuariosView(generics.ListAPIView):
    serializer_class = UsuarioSerializer
    permission_classes = [EsAdmin]
    queryset = Usuario.objects.all()
