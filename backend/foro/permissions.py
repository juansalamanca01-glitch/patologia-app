from rest_framework import permissions


class EsAutorOAdminOSoloLectura(permissions.BasePermission):
    """
    Cualquier usuario autenticado puede leer el foro.
    Crear publicaciones/comentarios requiere rol patólogo o admin (auditor: solo lectura).
    Editar o eliminar solo lo puede hacer el autor del contenido o un admin (moderación).
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        # Crear (POST) requiere patólogo o admin.
        if request.method == 'POST':
            return request.user.rol in ('admin', 'patologo')
        return True  # object-level check decides PUT/PATCH/DELETE

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.rol == 'admin':
            return True
        return getattr(obj, 'autor_id', None) == request.user.id
