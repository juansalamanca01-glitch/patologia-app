from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('login/', views.CustomTokenView.as_view(), name='token_obtain'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('registro/', views.RegistroView.as_view(), name='registro'),
    path('perfil/', views.PerfilView.as_view(), name='perfil'),
    path('cambiar-password/', views.CambiarPasswordView.as_view(), name='cambiar_password'),
    path('usuarios/', views.ListaUsuariosView.as_view(), name='lista_usuarios'),
]
