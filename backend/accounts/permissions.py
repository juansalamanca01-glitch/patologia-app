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
