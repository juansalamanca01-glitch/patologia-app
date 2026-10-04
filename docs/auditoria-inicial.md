# Auditoría inicial de PathoLab

**Fecha:** 2026-10-03
**Alcance:** todo el código de `backend/` y `frontend/src/`, la documentación (`README.md`, `docs/guia_exposicion.md`, `CLAUDE.md`), la colección de Postman y el script `iniciar_y_probar.ps1`.
**Importante:** en esta auditoría no se modificó ningún archivo de código. Las pruebas de comportamiento se hicieron sobre una **copia** de la base de datos, fuera del proyecto.

---

## Cómo leer este informe

Cada hallazgo tiene un nivel de prioridad:

| Nivel | Qué significa |
|---|---|
| 🔴 **Crítico** | Rompe la seguridad o la regla más importante del sistema. Hay que arreglarlo antes de mostrar la app como "lista" o de publicarla. |
| 🟠 **Importante** | Es un error real o un riesgo claro, pero su alcance es más limitado. Conviene arreglarlo pronto. |
| 🟡 **Menor** | Limpieza, orden u optimización. Mejora la calidad del código, pero nada se rompe si se deja para después. |

Cada punto explica **qué pasa**, **dónde está**, **por qué importa** y **cómo se podría arreglar**. Los puntos marcados con ✅ **Comprobado** no se dedujeron solo de leer el código: se ejecutaron y se vio que el fallo ocurre de verdad.

---

## Resumen rápido

- **¿Arranca el proyecto?** Sí. El backend pasa `python manage.py check` sin errores, no tiene migraciones pendientes y el frontend compila con `vite build`.
- **¿Tiene pruebas automáticas?** **No.** `python manage.py test` ejecuta **0 pruebas** y el frontend no tiene ninguna herramienta de pruebas instalada. Tampoco hay linter.
- **Cantidad de hallazgos:** 3 críticos, 13 importantes y 13 menores.
- **Lo más urgente:**
  1. Cualquier usuario puede convertirse en administrador.
  2. Los informes "finalizados" se pueden seguir editando y borrando, y un patólogo puede modificar los informes de otro.
  3. Si se publica la app sin archivo `.env`, queda en modo debug y con una clave secreta pública.

---

## 1. Estado del proyecto: ¿arranca? ¿tiene pruebas?

| Verificación | Resultado |
|---|---|
| `python manage.py check` | ✅ Sin errores (Python 3.11.9, Django 4.2.30) |
| `python manage.py makemigrations --check` | ✅ No faltan migraciones |
| `python manage.py showmigrations` | ✅ Todas aplicadas |
| `python manage.py test` | ⚠️ **0 pruebas.** Los archivos `tests.py` no existen en ninguna app. |
| `vite build` (frontend) | ✅ Compila (98 módulos, JS de 253 kB) |
| Pruebas en frontend | ⚠️ No hay ninguna (ni Vitest ni Jest) |
| Linter (flake8 / ESLint) | ⚠️ No está configurado |
| `npm audit` | ⚠️ 6 vulnerabilidades en dependencias (ver I-9) |
| `manage.py check --deploy` | ⚠️ 6 avisos de seguridad con la configuración local actual (normal en desarrollo, ver C-3) |

**¿Por qué importa no tener pruebas?** Una prueba automática es un pequeño programa que usa tu app y verifica que responde lo esperado. Sin pruebas, cada cambio puede romper algo sin que nadie se entere. Todos los errores críticos de este informe se habrían detectado con pruebas sencillas de permisos.

---

## 2. 🔴 Hallazgos críticos

### C-1. Cualquier usuario puede cambiarse el rol a "admin" ✅ Comprobado

> **Estado: corregido el 2026-10-03** (rama `seguridad-critica`). Ver `CHANGELOG.md` y la prueba `backend/accounts/tests.py`.

- **Dónde:** `backend/accounts/serializers.py` (`UsuarioSerializer`), usado por `PerfilView` en `backend/accounts/views.py`.
- **Qué pasa:** el endpoint `PATCH /api/auth/perfil/` sirve para que cada usuario edite sus propios datos (nombre, teléfono, etc.). El serializer permite modificar **todos** sus campos salvo `id` y `fecha_creacion`. Eso incluye `rol`, `activo` y `username`.
- **Prueba realizada:** con el usuario `auditor1` se envió `{"rol": "admin"}` a `/api/auth/perfil/`. La respuesta fue **200 OK** y el auditor quedó con rol **admin**.
- **Por qué importa:** es una "escalada de privilegios". Todo el control por roles (RBAC), que es una de las características principales del proyecto, se puede saltar con una sola petición desde Postman.
- **Cómo arreglarlo:** en `UsuarioSerializer`, marcar `rol`, `activo` y `username` como solo lectura en `read_only_fields`. Otra opción es crear un serializer aparte para "editar mi perfil" que solo acepte `nombre_completo`, `email`, `telefono` y `especialidad`.

### C-2. Los informes finalizados se pueden editar y borrar, y cualquier patólogo puede tocar informes ajenos ✅ Comprobado

> **Estado: corregido el 2026-10-03** (rama `seguridad-critica`), según las decisiones D-2 y D-3 de `docs/decisiones.md`. Ver `CHANGELOG.md` y las pruebas de `backend/informes/tests.py`.

- **Dónde:** `backend/informes/views.py` (`InformeViewSet`) y `backend/accounts/permissions.py` (`EsSoloLectura`).
- **Qué pasa:** el README dice que finalizar un informe **"bloquea edición"**, pero el código no lo hace. El permiso `EsSoloLectura` solo impide escribir al auditor. Tampoco revisa si el informe pertenece a quien lo modifica.
- **Prueba realizada:**
  - Un informe se marcó como finalizado y luego se cambiaron sus notas con `PATCH`: **200 OK**.
  - Un segundo patólogo editó ese mismo informe, que no era suyo: **200 OK**.
  - El segundo patólogo **borró** el informe finalizado ajeno: **204 (borrado)**.
- **Por qué importa:** en un sistema clínico, un informe finalizado debe quedar fijo para que se pueda confiar en él. Ahora mismo cualquier patólogo puede alterar o eliminar el trabajo de otro. El frontend esconde el botón de borrar para informes finalizados, pero eso no protege nada: la API acepta la petición igual.
- **Cómo arreglarlo:**
  1. En `perform_update` y `perform_destroy` (o con un permiso a nivel de objeto, `has_object_permission`), rechazar con 400 o 403 los cambios cuando `estado == 'finalizado'`.
  2. Permitir editar y borrar solo al autor del informe o a un admin.
  3. Decidir si un patólogo puede finalizar informes de otros (la acción `finalizar` tampoco lo revisa).
     **Decidido (2026-10-03), ver D-2 en `docs/decisiones.md`:** solo el autor o un admin puede editar, borrar o finalizar un informe.

### C-3. Valores por defecto inseguros: DEBUG activado y clave secreta publicada en GitHub

> **Estado: corregido el 2026-10-03** (rama `seguridad-critica`). Ver `CHANGELOG.md` y las pruebas de `backend/config/tests.py`. **Importante:** la clave antigua sigue en el historial de git. Cualquier servidor que la haya usado debe cambiarla.

- **Dónde:** `backend/config/settings.py`, líneas 11 y 13.
- **Qué pasa:** si no existe el archivo `.env`, Django usa `DEBUG=True` y una `SECRET_KEY` de respaldo escrita en el código. Ese código es público en GitHub.
- **Por qué importa:**
  - Los tokens JWT se **firman con la `SECRET_KEY`**. Si alguien conoce la clave, puede fabricar un token de "admin" válido sin tener contraseña.
  - Con `DEBUG=True`, cuando hay un error se muestran páginas con código, rutas y configuración del servidor.
  - Además, `CORS_ALLOW_ALL_ORIGINS` depende de `DEBUG`, así que cualquier página web podría llamar a la API.
  - Hoy esto no afecta a tu computador porque tienes un `.env`. Pero basta con olvidar el `.env` al publicar la app en un servidor para que quede totalmente expuesta.
- **Cómo arreglarlo:**
  - Que `DEBUG` sea `False` por defecto.
  - Que la app **no arranque** si falta la `SECRET_KEY`, es decir, usar `config('SECRET_KEY')` sin valor por defecto. El `.env.example` ya explica qué variable crear.

---

## 3. 🟠 Hallazgos importantes

### I-1. Borrar una patología que ya tiene informes da error 500 ✅ Comprobado

> **Estado: corregido el 2026-10-03** (rama `seguridad-critica`). Ver `CHANGELOG.md` y `BorrarPatologiaTests` en `backend/informes/tests.py`. La alternativa de *desactivar* en lugar de borrar queda para M-5.

- **Dónde:** `PatologiaViewSet` en `backend/informes/views.py`.
- **Qué pasa:** `Informe.patologia` usa `on_delete=PROTECT`, que es correcto porque evita perder informes. Pero la vista no captura el error `ProtectedError` y el servidor responde **500 Internal Server Error**. En el frontend (`PatologiasPage.jsx`) el usuario ve un mensaje genérico.
- **Cómo arreglarlo:** hacer lo mismo que ya hace `CategoriaViewSet.destroy`: comprobar antes si hay informes y responder 400 con un mensaje claro. Otra opción es desactivar la patología (`activa=False`) en lugar de borrarla.

### I-2. La validación de campos obligatorios se puede saltar ✅ Comprobado

> **Estado: corregido el 2026-10-03** (rama `seguridad-critica`). También se corrigió que el valor `0` se trataba como vacío. Ver `CHANGELOG.md` y `CamposObligatoriosTests` en `backend/informes/tests.py`.

- **Dónde:** `InformeSerializer.validate` en `backend/informes/serializers.py`, línea 72.
- **Qué pasa:** la validación solo se ejecuta si `datos_ingresados` trae algo (`if patologia and datos:`). Si se envía `{}` o no se envía el campo, el informe se crea **sin ningún campo obligatorio**.
- **Prueba realizada:** se creó un informe de "Biopsia de Piel" con `datos_ingresados: {}` y la respuesta fue **201 Created**.
- **Contradicción con la documentación:** `docs/guia_exposicion.md` (pregunta 1) afirma que la API responde 400 si falta un campo obligatorio.
- **Cómo arreglarlo:** quitar la condición `and datos` para que la validación se ejecute siempre que haya patología.

### I-3. El PDF se rompe (error 500) con ciertos textos y permite alterar su formato ✅ Comprobado

> **Estado: corregido el 2026-10-03** (rama `seguridad-critica`). Ver `CHANGELOG.md` y `PdfConTextoDelUsuarioTests` en `backend/informes/tests.py`. También se respetan ahora los saltos de línea de las notas.

- **Dónde:** `generar_pdf_informe` en `backend/informes/utils.py`.
- **Qué pasa:** ReportLab interpreta el texto de los párrafos como si fuera HTML sencillo. Los valores que escribe el usuario (datos, notas, texto generado) se insertan sin "escapar".
  - Textos como `lesión <b>grande`, `ver <i>H. pylori` o `tejido <br> pardo` hacen que el PDF **falle con error 500**.
  - Textos como `<font size=40>` **cambian el aspecto del PDF oficial**: se pueden agrandar u ocultar partes del informe.
- **Cómo arreglarlo:** pasar cada valor del usuario por `xml.sax.saxutils.escape()` (o `html.escape`) antes de meterlo en `Paragraph`.

### I-4. El panel de inicio y el buscador solo ven los primeros 20 informes

> **Estado: corregido el 2026-10-03** (rama `seguridad-critica`): endpoint `/api/informes/estadisticas/` y paginación en el buscador. Ver `CHANGELOG.md` y `EstadisticasYPaginacionTests` en `backend/informes/tests.py`.

- **Dónde:** `DashboardPage.jsx` (líneas 12–22) y `BuscarPage.jsx`.
- **Qué pasa:** la API devuelve los resultados por páginas de 20 (`PAGE_SIZE: 20`). El dashboard calcula "Total", "Borradores" y "Finalizados" contando solo esa primera página, y el buscador muestra "Resultados (20)" aunque haya 300.
- **Por qué importa:** cuando haya más de 20 informes, las estadísticas mostrarán **números falsos** y algunos informes no se podrán encontrar desde la interfaz.
- **Cómo arreglarlo:**
  - Para el total, usar `data.count`, que la API ya envía.
  - Para borradores y finalizados, crear un endpoint de estadísticas en el backend (por ejemplo, con `Count` agrupado por estado).
  - En el buscador, agregar paginación ("siguiente" / "anterior").

### I-5. El token de sesión viaja en la URL al descargar el PDF

> **Estado: corregido el 2026-10-03** (rama `seguridad-critica`). Se eliminó `/api/descargar-pdf/`; el frontend descarga con Axios. Ver `CHANGELOG.md`, `DescargaPdfTests` y `InformePage.test.jsx`.

- **Dónde:** `downloadPDF` en `InformePage.jsx` y la vista `descargar_pdf` en `backend/informes/views.py`.
- **Qué pasa:** para descargar el PDF, el frontend arma una URL como `/api/descargar-pdf/5/informe.pdf?token=eyJ...`.
- **Por qué importa:** las URLs quedan guardadas en el historial del navegador, en los registros del servidor y de proxies, y se pueden copiar sin querer. Cualquiera que vea esa URL tiene acceso a la cuenta durante 8 horas, que es lo que dura el token.
- **Detalles adicionales:**
  - La vista usa `@csrf_exempt` sin necesidad, porque es un GET.
  - Existen **dos** endpoints que hacen lo mismo: `/api/informes/{id}/pdf/`, que no usa el frontend pero sí Postman y la guía, y `/api/descargar-pdf/...`.
- **Cómo arreglarlo:** descargar el PDF con Axios (`responseType: 'blob'`), que ya envía el token en la cabecera `Authorization`, y luego crear el archivo con `URL.createObjectURL`. Así se puede eliminar la vista `descargar_pdf` y queda una sola ruta.

### I-6. El límite de 10 MB para subir imágenes no existe en realidad

> **Estado: corregido el 2026-10-03** (rama `seguridad-critica`). Al corregirlo se encontró otro problema: tampoco se validaba que el archivo fuera una imagen (se aceptaba un HTML llamado `foto.png`). También quedó corregido. Ver `CHANGELOG.md`, `backend/foro/tests.py` y `ForoPage.test.jsx`.

- **Dónde:** `backend/config/settings.py`, líneas 158–161.
- **Qué pasa:** el comentario dice "Tamaño máximo de subida (10 MB)", pero esos ajustes no hacen eso:
  - `DATA_UPLOAD_MAX_MEMORY_SIZE` **no cuenta** los archivos subidos.
  - `FILE_UPLOAD_MAX_MEMORY_SIZE` solo decide cuándo Django guarda el archivo en disco en vez de en memoria; no rechaza nada.
- **Por qué importa:** cualquier patólogo podría subir 6 imágenes de cientos de MB cada una y llenar el disco del servidor.
- **Cómo arreglarlo:** validar `archivo.size` en `subir_imagenes` (`foro/views.py`) o crear un validador en `ImagenPublicacion.imagen`, y corregir el comentario.

### I-7. Los patólogos pueden administrar el catálogo, aunque la documentación dice que es tarea del admin

> **Estado: resuelto por decisión (2026-10-03).** Ver la decisión D-1 en `docs/decisiones.md`: por criterio del profesor, los patólogos **sí** pueden administrar el catálogo. El código de permisos no cambia. Solo queda corregir el README para que lo diga, y eso se hará junto con I-12.

- **Dónde:** `CategoriaViewSet`, `PatologiaViewSet` y `PlantillaViewSet` (`informes/views.py`) y `TemaForoViewSet` (`foro/views.py`). Todos usan `EsPatologoOAdmin`.
- **Qué pasa:** el README dice que el **Administrador** se encarga de la "gestión de patologías y plantillas". En el código, cualquier patólogo puede crear, editar y **borrar** patologías, plantillas (los campos de los formularios), categorías y temas del foro.
- **Por qué importa:** un patólogo podría borrar una plantilla o cambiar los campos obligatorios de todos los demás.
- **Cómo arreglarlo:** decidir cuál es la regla correcta. Si es "solo admin", crear un permiso que permita leer a todos y escribir solo al admin, y usarlo en esas vistas. Si es "patólogos también", actualizar la documentación.

### I-8. Un autor puede fijar su propia publicación en el foro ✅ Comprobado

> **Estado: corregido el 2026-10-03** (rama `seguridad-critica`), junto con el problema de mover comentarios. Ver `CHANGELOG.md` y `CamposProtegidosForoTests` en `backend/foro/tests.py`.

- **Dónde:** `PublicacionSerializer` en `backend/foro/serializers.py`.
- **Qué pasa:** el modelo dice que **"Los administradores pueden fijar publicaciones importantes"**, pero `fijado` no es de solo lectura. Al crear una publicación con `"fijado": true`, el patólogo la dejó fijada arriba de todo (**201**, `fijado: True`).
- **Problema parecido:** en `ComentarioSerializer` el autor puede cambiar el campo `publicacion` con un `PATCH` y mover su comentario a otra publicación.
- **Cómo arreglarlo:** poner `fijado` como solo lectura para quien no sea admin, y `publicacion` como no editable después de crear el comentario.

### I-9. Dependencias del frontend con vulnerabilidades conocidas

> **Estado: parte (a) corregida el 2026-10-03** (rama `seguridad-critica`): producción pasa de 6 vulnerabilidades (2 altas) a 2 moderadas de `react-router`, que no afectan a cómo PathoLab usa la librería. Parte (b) corregida el mismo día: Vite 6.4 y Vitest 5, sin vulnerabilidades en las herramientas de desarrollo. Pendiente: (c) opcional, React Router 7. Ver `CHANGELOG.md` y `docs/progreso.md`.

- **Qué pasa:** `npm audit` reporta **6 vulnerabilidades (2 altas y 4 moderadas)** en `axios`, `form-data`, `follow-redirects` y `react-router` / `@remix-run/router`.
- **Cómo arreglarlo:** ejecutar `npm audit fix`. Las versiones corregidas están dentro de las mismas versiones principales (axios 1.20, react-router-dom 6.30.6), así que no debería romper nada. Después hay que probar la app.

### I-10. La URL de la API está fija en el código del frontend

> **Estado: corregido el 2026-10-03** (rama `seguridad-critica`) con la propuesta de este punto: `VITE_API_URL` + proxy de Vite. Ver `CHANGELOG.md` y `frontend/src/api/client.test.js`.

- **Dónde:** `frontend/src/api/client.js`, línea 3.
- **Qué pasa:** `API_URL = 'http://localhost:8000/api'` está escrita directamente en el código. Hay tres consecuencias:
  - La variable `VITE_API_URL` del `.env` **no se usa en ningún lado**.
  - El proxy de `vite.config.js` (que el README presenta como el mecanismo de conexión) **solo lo usa la descarga de PDF**.
  - Si se publica el frontend en un servidor, intentará conectarse al `localhost` del navegador de cada visitante, y no funcionará.
- **Cómo arreglarlo:** `const API_URL = (import.meta.env.VITE_API_URL || '') + '/api';`. Así en desarrollo funciona el proxy y en producción se usa la URL real.

### I-11. Las contraseñas no pasan por los validadores de Django

> **Estado: corregido el 2026-10-03** (rama `seguridad-critica`). Ver `CHANGELOG.md` y `ValidacionContrasenasTests` en `backend/accounts/tests.py`.

- **Dónde:** `RegistroSerializer` y `CambiarPasswordSerializer` en `backend/accounts/serializers.py`.
- **Qué pasa:** `settings.py` configura validadores para rechazar contraseñas comunes, solo numéricas o parecidas al usuario. Pero esos validadores solo se aplican si se llama a `validate_password()`, y ningún serializer lo hace. Por eso `12345678` se acepta como contraseña nueva.
- **Cómo arreglarlo:** llamar a `django.contrib.auth.password_validation.validate_password(value, user)` dentro de la validación de la contraseña nueva.

### I-12. El README tiene partes dañadas y está desactualizado

> **Estado: corregido el 2026-10-03** (rama `seguridad-critica`). README reescrito (incluye la corrección por la decisión D-1 de I-7) y colección de Postman rehecha y probada. Ver `CHANGELOG.md`.

- **Texto dañado:** **15 líneas** del README tienen caracteres invisibles de control. Probablemente se generó desde PowerShell, donde el acento grave (`` ` ``) es un carácter especial: por ejemplo, `` `b `` se convirtió en un "retroceso". Por eso:
  - Los bloques de código salen rotos: se ve `` `ash `` en lugar de ```` ```bash ````.
  - En la tabla de usuarios aparece "dmin" en lugar de `admin`, "uditor1" en lugar de `auditor1`, e "ite.config.js" en lugar de `vite.config.js`.
  - En GitHub, el README se ve mal formateado.
- **Desactualizado:**
  - No menciona el **foro**, las **categorías**, la página de **perfil** ni las páginas legales.
  - La "Estructura del proyecto" no incluye `foro/`, `throttles.py`, `Footer.jsx` ni las páginas nuevas.
  - La tabla de la API no tiene `/api/auth/registro/`, `/api/categorias/`, `/api/foro/...` ni `/api/descargar-pdf/...`.
- **Cómo arreglarlo:** reescribir esas secciones con bloques de código normales (```` ``` ````) y añadir los módulos nuevos (ver la tabla de la sección 5).

### I-13. No existe ninguna prueba automática

Esto ya se explicó en la sección 1, pero se repite aquí porque es un problema importante.

- **Recomendación:** empezar por pruebas de **permisos y reglas de negocio**, que es donde están los errores críticos:
  1. Un auditor no puede cambiar su rol.
  2. Un informe finalizado no se puede editar.
  3. Un patólogo no puede editar el informe de otro.
  4. Faltan campos obligatorios → 400.
  5. El PDF se genera aunque el texto tenga `<`.
- Con `APITestCase` de DRF, cada prueba ocupa unas 10 líneas.

---

## 4. 🟡 Hallazgos menores

### M-1. Código que no se usa

| Qué | Dónde | Comentario |
|---|---|---|
| `LoginSerializer` | `accounts/serializers.py:45` | No se usa en ninguna parte; el login lo hace `CustomTokenSerializer`. |
| Campo `campos_requeridos` del modelo `Patologia` | `informes/models.py:38` | Nunca se lee ni se llena. Los campos obligatorios se definen con `Plantilla.obligatorio`, así que hay dos fuentes para lo mismo. Quitarlo requiere una migración. |
| Importaciones `inch`, `TA_LEFT` | `informes/utils.py` | Se importan pero no se usan. |
| `const user = await login(...)` y `ROL_LABELS` | `LoginPage.jsx` | La variable `user` y la constante `ROL_LABELS` no se usan. |
| `isAdmin`, `isPatologo`, `isAuditor` | `AuthContext.jsx` | Se exportan, pero ninguna página los usa; todas usan `canWrite` o `user.rol`. |
| `console.log` / `console.error` | 5 apariciones (por ejemplo, `InformePage.jsx:138-140`) | Mensajes de depuración que quedaron en el código. |

### M-2. Archivos sobrantes

- `frontend/public/favicon.svg`, `frontend/public/icons.svg`, `frontend/src/assets/hero.png`, `typescript.svg` y `vite.svg`: **ningún archivo los usa**. Son restos de la plantilla inicial de Vite; el ícono real está incrustado en `index.html`. `typescript.svg` sobra además porque el proyecto no usa TypeScript.
- `frontend/.gitignore` repite reglas que ya están en el `.gitignore` de la raíz. No hace daño, pero es redundante.

### M-3. Código duplicado

- **`ROL_LABELS`** (el texto "Administrador / Patólogo / Auditor") está copiado en **4 archivos**: `Navbar`, `LoginPage`, `DashboardPage` y `PerfilPage`.
- **El indicador de estado del informe** (`ESTADO_CLASS` y el texto "Borrador / Finalizado") se repite en `DashboardPage`, `BuscarPage` e `InformePage`.
- **`get_autor_nombre`** (`nombre_completo or username`) está repetido en **5 serializers**. Se podría convertir en una propiedad del modelo `Usuario`, por ejemplo `nombre_visible`, y usar `source='autor.nombre_visible'`.
- **`data.results || data`** se repite en casi todas las páginas. Un pequeño helper en `api/client.js` lo resolvería.
- **Hay dos endpoints de PDF** que hacen lo mismo (ver I-5).

**Cómo arreglarlo:** crear `frontend/src/constants.js` para las etiquetas y un componente `<EstadoBadge>` para el indicador de estado.

### M-4. Consultas repetidas a la base de datos (problema "N+1")

- **Dónde:** `CategoriaSerializer.total_patologias`, `TemaForoSerializer.total_publicaciones` y `PublicacionListSerializer` (`get_portada` usa `imagenes.first()`).
- **Qué pasa:** en cada fila del listado se hace una consulta extra. Con 20 publicaciones son unas 20 consultas más de las necesarias.
- **Cómo arreglarlo:** usar `annotate(total=Count(...))` en el `queryset`. Para la portada, usar las imágenes ya precargadas (`obj.imagenes.all()[0]`), porque `first()` ignora la precarga.

### M-5. `/api/patologias/` también devuelve las patologías inactivas

La guía y el README dicen "listar patologías **activas**", pero el endpoint devuelve todas. Por eso el selector de "Nuevo informe" ofrece patologías desactivadas. Se puede filtrar `activa=True` cuando la petición viene del formulario de informes.

### M-6. El foro empieza sin temas y no hay forma de crearlos desde la app

`seed_data` no crea temas del foro ni categorías, y el frontend no tiene una pantalla para crear temas. Solo se pueden crear desde `/admin/` o con Postman.

### M-7. El auditor ve el formulario de comentarios aunque no puede comentar

En `PublicacionDetallePage.jsx`, el formulario de comentarios aparece para todos los usuarios, pero la API rechaza al auditor (403). Habría que ocultarlo cuando `canWrite` es falso.

### M-8. La página de perfil se rompe si falla la carga

> **Estado: corregido el 2026-10-03** (rama `seguridad-critica`). Ver `CHANGELOG.md` y `frontend/src/pages/PerfilPage.test.jsx`. Con este arreglo el frontend ya tiene pruebas (Vitest), lo que avanza I-13.

En `PerfilPage.jsx`, si `GET /auth/perfil/` falla, `perfil` queda en `null`. Luego el código intenta leer `perfil.nombre_completo` y la página entera falla con un error de JavaScript. Hay que mostrar un mensaje de error cuando `perfil` es `null`.

### M-9. Algunas peticiones no manejan errores

- `InformePage.jsx` no tiene `.catch` al cargar las patologías ni las plantillas.
- `DashboardPage.jsx` solo escribe los errores en la consola.

Si el backend está apagado, el usuario no ve ningún mensaje.

### M-10. La hora del PDF no usa la zona horaria configurada

`generar_pdf_informe` usa `datetime.now()`, que toma la hora del servidor y no la de Bogotá configurada en `TIME_ZONE`. Se corrige con `django.utils.timezone.localtime()`.

### M-11. Cerrar sesión no invalida los tokens

`logout()` solo borra los tokens del navegador. Un token robado sigue sirviendo hasta 8 horas (el token de acceso) o 7 días (el de refresco). Lo mismo pasa después de cambiar la contraseña. Para este proyecto es aceptable, pero se puede mejorar activando `rest_framework_simplejwt.token_blacklist`.

### M-12. Las imágenes del foro solo se ven en modo desarrollo

En `config/urls.py`, los archivos de `/media/` solo se sirven si `DEBUG=True`. En producción hará falta configurarlos aparte, por ejemplo con Nginx o un almacenamiento externo.

### M-13. Comentarios en inglés y un comentario equivocado

- La regla del proyecto es escribir los comentarios en español, pero muchos docstrings están en inglés (por ejemplo, `"""Custom user model with role-based access."""`).
- En `informes/utils.py`, el comentario `# ── Macroscopic description generator ──` está justo antes de la función que **genera el PDF**, así que confunde.

---

## 5. Documentación frente al código real

| Lo que dice la documentación | Lo que hace el código | ¿Coincide? |
|---|---|---|
| Finalizar un informe "bloquea edición" (README) | Se puede editar y borrar (C-2) | ❌ |
| Si falta un campo obligatorio, la API responde 400 (guía, pregunta 1) | Se salta si `datos_ingresados` está vacío (I-2) | ❌ Parcial |
| El Admin gestiona patologías y plantillas (README) | Los patólogos también pueden (I-7) | ✅ El código queda así por decisión D-1; falta corregir el README |
| `GET /api/patologias/` lista patologías **activas** | Lista todas (M-5) | ❌ |
| El proxy de Vite redirige `/api` al backend (README) | `client.js` llama directo a `localhost:8000`; el proxy solo se usa para el PDF (I-10) | ❌ Parcial |
| Usuarios `admin`, `patologo1`, `auditor1` (README) | Correcto en el código, pero el README muestra "dmin" y "uditor1" por el texto dañado (I-12) | ⚠️ |
| La API tiene "25 operaciones, 4 módulos, 9 rutas" (guía, diapositiva 4) | Ahora hay más: categorías, registro, foro (4 recursos), descargar-pdf | ❌ Desactualizado |
| Estructura del proyecto (README) | Faltan `foro/`, `throttles.py`, `Footer.jsx` y 6 páginas nuevas | ❌ Desactualizado |
| Búsqueda "por patología" (README) | La API acepta `?patologia=`, pero `BuscarPage` no tiene ese filtro | ⚠️ Parcial |
| "Tamaño máximo de subida 10 MB" (comentario en `settings.py`) | No hay límite real (I-6) | ❌ |
| Login JWT con el rol dentro del token (guía) | Correcto | ✅ |
| Texto macroscópico generado automáticamente (README y guía) | Correcto; coincide con el ejemplo de la guía | ✅ |
| 14 patologías precargadas con `seed_data` | Correcto | ✅ |
| Exportación a PDF con ReportLab | Correcto (salvo I-3) | ✅ |
| Colección de Postman | Solo 5 peticiones, sin foro ni categorías; usa la ruta `/pdf/` que el frontend no usa | ⚠️ Incompleta |
| `iniciar_y_probar.ps1` | Funciona; supone que la patología con `id=1` es "Biopsia de Piel", lo cual es cierto solo con una base de datos nueva | ✅ |

---

## 6. Cosas que están bien hechas

También conviene saber qué ya está bien hecho, para no cambiarlo por error:

- El `.gitignore` está correcto: los `.env`, la base de datos, `venv` y `node_modules` nunca se subieron a GitHub.
- La configuración se lee de variables de entorno con `python-decouple`, y existe un `.env.example` documentado.
- Hay límites de peticiones por minuto (throttling) en el login, el registro y el foro, lo que ayuda contra ataques de fuerza bruta y spam.
- `on_delete=PROTECT` en informes evita borrar por accidente un historial clínico (solo falta manejar bien el error, I-1).
- Las consultas de informes usan `select_related` para evitar consultas repetidas.
- El frontend renueva el token automáticamente cuando recibe un 401.
- El foro limita a 6 imágenes por publicación y valida que el contenido no esté vacío.
- En producción (`DEBUG=False`) se activan HSTS, cookies seguras y la redirección a HTTPS.

---

## 7. Orden de trabajo sugerido

1. **Seguridad crítica:** C-1, C-2 y C-3. Son cambios pequeños, casi todos en serializers y vistas.
2. **Pruebas:** escribir pruebas para C-1, C-2, I-2 e I-3 (I-13), para que esos errores no vuelvan.
3. **Errores que el usuario ve:** I-1, I-3, I-4 y M-8.
4. **Seguridad restante:** I-5, I-6, I-8, I-9 e I-11. (I-7 ya está resuelto por la decisión D-1.)
5. **Configuración del frontend:** I-10.
6. **Documentación:** arreglar el README (I-12), actualizar la guía y la colección de Postman, y crear `CHANGELOG.md`.
7. **Limpieza:** los puntos menores M-1 a M-13.

> Según las reglas de trabajo de `CLAUDE.md`, cada uno de estos cambios se explicará y se esperará confirmación antes de tocar el código, y quedará registrado en `CHANGELOG.md`.
