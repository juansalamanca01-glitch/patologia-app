# Registro de cambios

Todos los cambios de código del proyecto se documentan aquí, del más reciente al más antiguo.
Cada entrada indica la fecha, qué se cambió y por qué. Los códigos como "C-1" remiten a `docs/auditoria-inicial.md`.

## 2026-10-03

### Seguridad: SECRET_KEY obligatoria y DEBUG desactivado por defecto (C-3)

**Qué se cambió**
- `backend/config/settings.py`: se eliminó la `SECRET_KEY` de respaldo escrita en el código. Si falta la variable, la app no arranca y lanza `ImproperlyConfigured` con un mensaje en español que dice qué hacer. `DEBUG` vale `False` si no se define (antes era `True`).
- `backend/config/tests.py` (nuevo): 4 pruebas que cargan `settings.py` simulando que no hay `.env`.
- `iniciar_y_probar.ps1`: si no existe `backend/.env`, lo crea desde `.env.example` con una `SECRET_KEY` aleatoria (`secrets.token_urlsafe(50)`). Si el `.env` ya existe, no lo toca.
- `backend/.env.example`: comentario que explica que `SECRET_KEY` es obligatoria y cómo generar una.
- `README.md`: el paso 4 de la instalación (crear el `.env`) pasa a ser obligatorio y explica cómo generar la clave.
- `backend/accounts/permissions.py`: se borró la clase `EsSoloLectura`, que ya no usaba ninguna vista desde el arreglo de C-2.
- Documentación: `CLAUDE.md` (configuración y regla 6), `docs/progreso.md` (nuevo) y C-3 marcado como corregido en la auditoría.

**Por qué**
- La clave de respaldo era pública en GitHub. Si la app se publicaba sin `.env`, cualquiera podía firmar tokens JWT de administrador. Además quedaba con `DEBUG=True`, que muestra detalles internos en los errores y permite CORS desde cualquier origen.
- `docs/progreso.md` registra en qué punto quedó el trabajo, para poder retomarlo aunque la conversación se corte.

### Seguridad: informes finalizados bloqueados y solo el autor o un admin puede modificarlos (C-2)

**Qué se cambió**
- `backend/accounts/permissions.py`: ahora contiene `EsAutorOAdminOSoloLectura`, que se movió desde `backend/foro/permissions.py` (archivo eliminado) para que lo compartan informes y foro. El comportamiento del foro no cambia; solo cambia el `import` en `backend/foro/views.py`.
- `backend/informes/views.py`: `InformeViewSet` usa `EsAutorOAdminOSoloLectura` en lugar de `EsSoloLectura`. Solo el autor o un admin puede editar, borrar o finalizar un informe; los demás reciben 403. Además, `update()` y `destroy()` responden 400 si el informe está finalizado, también para el admin.
- `backend/informes/serializers.py`: `InformeListSerializer` incluye el campo `autor` (id), que el frontend necesita.
- `frontend/src/pages/InformePage.jsx`: los campos y los botones "Actualizar" y "Finalizar" solo se habilitan para el autor o un admin. También se muestran los mensajes de error `detail` de la API, que antes no aparecían.
- `frontend/src/pages/DashboardPage.jsx`: el botón de eliminar borrador solo aparece para el autor o un admin.
- `backend/informes/tests.py` (nuevo): 12 pruebas de permisos y del bloqueo de informes finalizados.
- Documentación: decisión D-3 en `docs/decisiones.md`; tabla de la API del README; sección de permisos de `CLAUDE.md`; C-2 marcado como corregido en la auditoría.

**Por qué**
- Un informe finalizado se podía seguir editando y borrando, aunque el README dice que finalizar "bloquea edición".
- Cualquier patólogo podía editar, borrar o finalizar informes de otro. Esto va contra las decisiones D-2 (solo el autor o un admin) y D-3 (el bloqueo de un informe finalizado también aplica al admin).

### Seguridad: un usuario ya no puede cambiarse el rol, el estado ni el username (C-1)

**Qué se cambió**
- `backend/accounts/serializers.py`: en `UsuarioSerializer`, los campos `username`, `rol` y `activo` pasan a ser de solo lectura (`read_only_fields`). Se siguen mostrando en las respuestas, pero se ignoran si llegan en un `PATCH` o `PUT` a `/api/auth/perfil/`.
- `backend/accounts/tests.py` (nuevo): primeras pruebas automáticas del proyecto (`PerfilCamposProtegidosTests`). Comprueban que un usuario no puede cambiar su `rol`, `activo` ni `username`, y que sí puede editar sus datos personales.

**Por qué**
- Cualquier usuario autenticado, incluso un auditor, podía enviar `{"rol": "admin"}` a `/api/auth/perfil/` y convertirse en administrador. Eso anulaba todo el control de acceso por roles.
- El registro de usuarios (`RegistroSerializer`, solo para admin) y el panel `/admin/` de Django no usan este serializer, así que siguen pudiendo asignar roles.
