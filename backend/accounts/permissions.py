from rest_framework import permissions


class EsAdmin(permissions.BasePermission):
    """Solo los administradores tienen acceso."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol == 'admin'


class EsPatologoOAdmin(permissions.BasePermission):
    """Todos leen; solo patólogos y administradores escriben (el auditor solo lee)."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.rol in ('admin', 'patologo')


class EsPatologoOAdminYSoloAdminBorra(EsPatologoOAdmin):
    """Como EsPatologoOAdmin, pero borrar (DELETE) es solo del admin. Pacientes (decisión D-11)."""

    def has_permission(self, request, view):
        if request.method == 'DELETE':
            return request.user.is_authenticated and request.user.rol == 'admin'
        return super().has_permission(request, view)


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
