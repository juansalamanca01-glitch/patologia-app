# Registro de cambios

Todos los cambios de código del proyecto se documentan aquí, del más reciente al más antiguo.
Cada entrada indica la fecha, qué se cambió y por qué. Los códigos como "C-1" remiten a `docs/auditoria-inicial.md`.

## 2026-10-03

### Seguridad: el token de sesión ya no viaja en la URL al descargar el PDF (I-5)

**Qué se cambió**
- `backend/informes/views.py` y `backend/informes/urls.py`: se eliminaron la vista `descargar_pdf` (`/api/descargar-pdf/<id>/<filename>?token=...`), su ruta y el `import csrf_exempt` que solo ella usaba. El PDF se descarga únicamente por `GET /api/informes/{id}/pdf/`, que exige el token en la cabecera `Authorization`.
- `backend/informes/views.py`: en `exportar_pdf`, el nombre del archivo se limpia con `re.sub(r'[^A-Za-z0-9\-]', '_', ...)`. Antes solo se reemplazaban los espacios, y unas comillas en el número de caso rompían la cabecera `Content-Disposition`.
- `frontend/src/pages/InformePage.jsx`: `downloadPDF` pide el PDF con Axios (`responseType: 'blob'`) y lo guarda con un enlace temporal `blob:`. Ya no crea un formulario oculto con el token. Si la descarga falla, muestra *"No se pudo descargar el PDF."* (antes fallaba sin avisar).
- Pruebas: `DescargaPdfTests` (5 pruebas del backend) y `frontend/src/pages/InformePage.test.jsx` (1 prueba del frontend).
- Documentación: sección de PDF de `CLAUDE.md`.

**Por qué**
- Una URL con `?token=` queda guardada en el historial del navegador y en los registros del servidor y de los proxies. Cualquiera que la viera podía usar la cuenta durante las 8 horas de vida del token.
- Había dos endpoints que hacían lo mismo. Ahora queda uno, autenticado igual que el resto de la API.

### Corrección: la página de perfil ya no queda en blanco si falla la carga (M-8) y primeras pruebas del frontend

**Qué se cambió**
- `frontend/src/pages/PerfilPage.jsx`: la carga del perfil pasa a la función `cargarPerfil()` y tiene `.catch`. Si falla, se muestra *"No se pudo cargar tu perfil. Intenta de nuevo."* con un botón **Reintentar**, en lugar de dibujar el formulario con `perfil = null`.
- Herramientas de prueba del frontend, instaladas solo como `devDependencies`: `vitest` 3.2, `@testing-library/react` 16, `@testing-library/dom` 10, `@testing-library/jest-dom` 6 y `jsdom` 26.
- `frontend/package.json`: scripts `npm test` (`vitest run`) y `npm run test:watch`.
- `frontend/vite.config.js`: sección `test` (entorno `jsdom`, archivo de preparación `src/test/setup.js`).
- `frontend/src/test/setup.js` (nuevo): añade las comprobaciones de jest-dom y limpia el DOM entre pruebas.
- `frontend/src/pages/PerfilPage.test.jsx` (nuevo): 3 pruebas que simulan la API con `vi.mock`. Cubren el error de carga, el botón Reintentar y la carga correcta.
- Documentación: comandos de prueba en el `README.md` y en `CLAUDE.md`.

**Por qué**
- Si `GET /auth/perfil/` fallaba (backend caído, error 500), la página leía `perfil.nombre_completo` con `perfil = null`. React lanzaba `TypeError` y, como la app no tiene un Error Boundary, toda la pantalla quedaba en blanco.
- El frontend no tenía forma de probar errores como este. Ahora tiene Vitest, que también servirá para los próximos hallazgos del frontend.
- **Nota de seguridad:** `npm audit` marca una vulnerabilidad moderada en Vitest 3 (GHSA-82fw-gwwq-j7x9). Solo afecta al ejecutar las pruebas en local y no llega a la app publicada. La corrige Vitest 5, que exige Vite 6 o superior, así que se resolverá junto con I-9. Las vulnerabilidades de producción no cambiaron (siguen las 6 de I-9).

### Corrección: estadísticas reales en el dashboard y paginación en el buscador (I-4)

**Qué se cambió**
- `backend/informes/views.py`: nuevo endpoint `GET /api/informes/estadisticas/` (acción `estadisticas` de `InformeViewSet`). Devuelve `{total, borradores, finalizados}` contando todos los informes en una sola consulta (`Count` agrupado por estado) y respeta los mismos filtros que el listado.
- `frontend/src/pages/DashboardPage.jsx`: las tarjetas de totales usan el endpoint nuevo. "Informes recientes" sigue mostrando los 10 más nuevos del listado.
- `frontend/src/pages/BuscarPage.jsx`: paginación con botones "Anterior" y "Siguiente", el texto "Mostrando X–Y de Z" y el total real en el título. Al cambiar de página se conservan los filtros de la última búsqueda.
- `frontend/src/index.css`: estilo `.paginacion`.
- `backend/informes/tests.py`: nueva clase `EstadisticasYPaginacionTests` con 5 pruebas sobre los totales, los permisos, la segunda página y los filtros.
- Documentación: endpoint nuevo en la tabla de la API del README y en `CLAUDE.md`.

**Por qué**
- La API devuelve los informes de 20 en 20, pero el dashboard contaba solo la primera página. Con 25 informes mostraba "Total 20" y "Finalizados 10" en lugar de 25 y 15. El buscador mostraba "Resultados (20)" y no permitía ver el resto.

### Corrección: el PDF muestra literal el texto del usuario y respeta los saltos de línea (I-3)

**Qué se cambió**
- `backend/informes/utils.py`: nueva función `texto_seguro()`. Escapa `<`, `>` y `&` con `xml.sax.saxutils.escape` y convierte los saltos de línea en `<br/>`. Se aplica a todo el texto del usuario que va a un `Paragraph` del PDF: nombres y valores de los datos clínicos, descripción macroscópica y notas.
- `backend/informes/tests.py`: nueva clase `PdfConTextoDelUsuarioTests` con 3 pruebas. Comprueban que el PDF se genera con textos como `<i>H. pylori` o `<b>grande`, que etiquetas como `<font size=40>` no cambian el formato y que las notas conservan sus saltos de línea.

**Por qué**
- ReportLab interpreta el texto de `Paragraph` como marcado. Un texto como `ver <i>H. pylori` hacía fallar la generación del PDF con un error 500. Con etiquetas válidas como `<font size=40>`, un usuario podía cambiar el aspecto del informe oficial.
- Mejora pedida por el usuario: antes, las notas escritas en varias líneas se juntaban en un solo párrafo.

### Corrección: borrar una patología con informes ya no da error 500 (I-1)

**Qué se cambió**
- `backend/informes/views.py`: `PatologiaViewSet.destroy()` captura `ProtectedError` y responde **400** con el mensaje *"No se puede eliminar: esta patología tiene N informe(s) asociado(s)."*. Antes la petición fallaba con un error 500. Los informes siguen protegidos por `on_delete=PROTECT`.
- `backend/informes/tests.py`: nueva clase `BorrarPatologiaTests` con 2 pruebas. Una comprueba que con informes se responde 400 y la patología no se borra; la otra, que sin informes se borra normalmente (204).

**Por qué**
- Al borrar desde la pantalla de Patologías una patología que ya tenía informes, el servidor fallaba con un error interno y el usuario veía un mensaje genérico. `PatologiasPage.jsx` ya mostraba el campo `detail` de la respuesta, así que el frontend no necesitó cambios.

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
