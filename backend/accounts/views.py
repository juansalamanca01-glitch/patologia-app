from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .permissions import EsAdmin
from .serializers import CambiarPasswordSerializer, RegistroSerializer, UsuarioSerializer
from .throttles import LoginRateThrottle, RegistroRateThrottle

Usuario = get_user_model()


# ── Token JWT que incluye el rol del usuario ──────────────────────
class CustomTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['rol'] = user.rol
        token['nombre'] = user.nombre_visible
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UsuarioSerializer(self.user).data
        return data


class CustomTokenView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer
    throttle_classes = [LoginRateThrottle]


# ── Registro de usuarios (solo admin) ────────────────────────────────────
class RegistroView(generics.CreateAPIView):
    serializer_class = RegistroSerializer
    permission_classes = [EsAdmin]
    throttle_classes = [RegistroRateThrottle]


# ── Perfil ──────────────────────────────────────────────────────
class PerfilView(generics.RetrieveUpdateAPIView):
    serializer_class = UsuarioSerializer

    def get_object(self):
        return self.request.user


# ── Cambio de contraseña ──────────────────────────────────────────────
class CambiarPasswordView(APIView):
    def post(self, request):
        serializer = CambiarPasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()
        # Cierra todas las sesiones anteriores (decisión D-6): ningún token de renovación
        # emitido antes del cambio vuelve a servir, en este ni en otros dispositivos.
        for token in OutstandingToken.objects.filter(user=usuario):
            BlacklistedToken.objects.get_or_create(token=token)
        # La sesión desde la que se cambió la contraseña sigue abierta con tokens nuevos.
        nuevo = RefreshToken.for_user(usuario)
        return Response(
            {
                'detail': 'Contraseña actualizada correctamente.',
                'access': str(nuevo.access_token),
                'refresh': str(nuevo),
            }
        )


# ── Cerrar sesión ──────────────────────────────────────────────────
class LogoutView(APIView):
    """
    Invalida el token de renovación recibido (decisión D-6). No exige el token de
    acceso: quien tiene el token de renovación puede anularlo, aunque el de acceso
    ya haya vencido.
    """

    permission_classes = [permissions.AllowAny]
    # Sin autenticación: un token de acceso vencido en la cabecera haría que DRF
    # respondiera 401 antes de llegar aquí, y la sesión no se cerraría.
    authentication_classes = []

    def post(self, request):
        try:
            RefreshToken(request.data.get('refresh', '')).blacklist()
        except TokenError:
            return Response({'detail': 'Token inválido o ya invalidado.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': 'Sesión cerrada.'})


# ── Lista de usuarios (solo admin) ─────────────────────────────────────
class ListaUsuariosView(generics.ListAPIView):
    serializer_class = UsuarioSerializer
    permission_classes = [EsAdmin]
    queryset = Usuario.objects.all()
