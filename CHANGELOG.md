# Registro de cambios

Todos los cambios de código del proyecto se documentan aquí, del más reciente al más antiguo.
Cada entrada indica la fecha, qué se cambió y por qué. Los códigos como "C-1" remiten a `docs/auditoria-inicial.md`.

## 2026-10-03

### Seguridad: un usuario ya no puede cambiarse el rol, el estado ni el username (C-1)

**Qué se cambió**
- `backend/accounts/serializers.py`: en `UsuarioSerializer`, los campos `username`, `rol` y `activo` pasan a ser de solo lectura (`read_only_fields`). Se siguen mostrando en las respuestas, pero se ignoran si llegan en un `PATCH` o `PUT` a `/api/auth/perfil/`.
- `backend/accounts/tests.py` (nuevo): primeras pruebas automáticas del proyecto (`PerfilCamposProtegidosTests`). Comprueban que un usuario no puede cambiar su `rol`, `activo` ni `username`, y que sí puede editar sus datos personales.

**Por qué**
- Cualquier usuario autenticado, incluso un auditor, podía enviar `{"rol": "admin"}` a `/api/auth/perfil/` y convertirse en administrador. Eso anulaba todo el control de acceso por roles.
- El registro de usuarios (`RegistroSerializer`, solo para admin) y el panel `/admin/` de Django no usan este serializer, así que siguen pudiendo asignar roles.
