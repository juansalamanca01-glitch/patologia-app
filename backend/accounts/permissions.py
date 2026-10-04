from rest_framework import permissions


class EsAdmin(permissions.BasePermission):
    """Only admins can access."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol == 'admin'


class EsPatologoOAdmin(permissions.BasePermission):
    """Patólogos and admins can write; auditors read-only."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.rol in ('admin', 'patologo')


class EsSoloLectura(permissions.BasePermission):
    """Read-only access for auditors."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.rol == 'auditor':
            return request.method in permissions.SAFE_METHODS
        return True


class EsAutorOAdminOSoloLectura(permissions.BasePermission):
    """
    Permiso compartido por informes y foro (ver decisión D-2 en docs/decisiones.md).
    - Cualquier usuario autenticado puede leer.
    - Crear (POST) requiere rol patólogo o admin; el auditor solo lee.
    - Editar, eliminar o ejecutar acciones sobre un objeto (por ejemplo, finalizar
      un informe) solo lo puede hacer su autor o un admin.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        # Crear (POST) requiere patólogo o admin.
        if request.method == 'POST':
            return request.user.rol in ('admin', 'patologo')
        return True  # PUT/PATCH/DELETE se deciden en has_object_permission

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.rol == 'admin':
            return True
        return getattr(obj, 'autor_id', None) == request.user.id
