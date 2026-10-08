from rest_framework.throttling import ScopedRateThrottle


class LoginRateThrottle(ScopedRateThrottle):
    """Limita intentos de login por IP para frenar ataques de fuerza bruta."""

    scope = 'login'


class RegistroRateThrottle(ScopedRateThrottle):
    """Limita creación de cuentas para evitar registro masivo automatizado."""

    scope = 'registro'
