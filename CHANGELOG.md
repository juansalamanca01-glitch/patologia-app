# Registro de cambios

Todos los cambios de código del proyecto se documentan aquí, del más reciente al más antiguo.
Cada entrada indica la fecha, qué se cambió y por qué. Los códigos como "C-1" remiten a `docs/auditoria-inicial.md`.

## 2026-10-04

### Seguridad: cerrar sesión y cambiar la contraseña invalidan el token de renovación (M-11, decisión D-6)

**Qué se cambió**
- `backend/config/settings.py`:
  - Se instaló `rest_framework_simplejwt.token_blacklist`, que añade 12 migraciones con sus tablas.
  - `BLACKLIST_AFTER_ROTATION = True`: al renovar, el token de renovación anterior queda invalidado.
- `backend/accounts/views.py` y `urls.py`:
  - Nuevo `POST /api/auth/logout/` (`LogoutView`), que invalida el `refresh` recibido. No procesa la autenticación (`authentication_classes = []`), para que funcione aunque el token de acceso haya vencido.
  - `CambiarPasswordView` invalida todos los tokens de renovación del usuario y devuelve un par nuevo (`access`, `refresh`), para que la sesión actual siga abierta.
- `frontend/src/api/client.js`: al renovar el token, el interceptor guarda también el `refresh` nuevo. Sin esto, la lista negra habría cerrado la sesión en la segunda renovación.
- `frontend/src/context/AuthContext.jsx`: `logout()` avisa al backend antes de borrar los tokens del navegador.
- `frontend/src/pages/PerfilPage.jsx`: guarda los tokens nuevos al cambiar la contraseña.
- Pruebas:
  - Backend: `CierreDeSesionTests`, 5 pruebas (logout, token inválido, token de acceso vencido, reutilizar un token renovado y cambio de contraseña con dos sesiones abiertas).
  - Frontend: 3 pruebas (interceptor, `logout` y perfil).
- Documentación: tabla de la API y sección de Seguridad del `README.md`, y el frontend en `CLAUDE.md`.

**Por qué**
- Antes, cerrar sesión solo borraba los tokens del navegador. Un token de renovación robado seguía sirviendo hasta 7 días, incluso después de cambiar la contraseña.
- Verificado de punta a punta a través del proxy de Vite. Login; renovar devuelve un `refresh` nuevo; reutilizar el viejo da 401; `logout` con un token de acceso vencido da 200; usar el `refresh` después del logout da 401.
- **En otros computadores** hay que ejecutar `python manage.py migrate`. En el del autor ya se aplicó, después de guardar una copia de seguridad de `db.sqlite3`.

### La hora del pie del PDF usa la zona horaria configurada (M-10)

**Qué se cambió**
- `backend/informes/utils.py`: el pie *"Generado el …"* usa `timezone.localtime()` de Django en lugar de `datetime.now()`.
- `backend/informes/tests.py`: una prueba fija la hora en 03:30 UTC del 4 de octubre y comprueba que el PDF diga "03/10/2026 22:30" (hora de Bogotá).

**Por qué**
- `datetime.now()` devuelve la hora del sistema operativo, no la de `TIME_ZONE = 'America/Bogota'`. En Linux, Django ajusta la zona horaria de todo el proceso y el resultado coincidía; en Windows no puede hacerlo, y en un servidor con otra zona la hora del PDF salía corrida.

### Los errores se muestran en pantalla, no solo en la consola (M-9)

**Qué se cambió**
- `frontend/src/pages/DashboardPage.jsx`: si falla la carga del panel, se muestra *"No se pudo cargar el panel…"*; si falla el borrado de un borrador, se muestra el motivo que devuelve la API.
- `frontend/src/pages/InformePage.jsx`: avisos si no se pueden cargar las patologías o los campos de la patología elegida. Se quitó el último `console.error`, porque ese error ya se mostraba en pantalla.
- Pruebas: `DashboardPage.test.jsx` (nuevo, 2) y 2 nuevas en `InformePage.test.jsx`.

**Por qué**
- Con el backend apagado o ante un error del servidor, el panel se quedaba vacío y el formulario de informe sin opciones, sin ningún aviso. El error solo aparecía en la consola del navegador, que el usuario no ve.

### Foro: el auditor ya no ve el formulario para comentar (M-7)

**Qué se cambió**
- `frontend/src/pages/PublicacionDetallePage.jsx`: el formulario de comentarios solo se muestra si el usuario puede escribir (`canWrite`).
- `frontend/src/pages/PublicacionDetallePage.test.jsx` (nuevo): 2 pruebas, una para el auditor y otra para el patólogo.

**Por qué**
- El auditor tiene solo lectura y la API le rechaza los comentarios (403). Aun así veía el formulario, y al usarlo recibía un error.

### Foro: temas iniciales y botón para crear temas (M-6, decisión D-5)

**Qué se cambió**
- `backend/informes/management/commands/seed_data.py`: crea 4 temas del foro: *Casos clínicos*, *Técnicas de laboratorio*, *Investigación* y *Dudas y consultas*. Usa `get_or_create`, así que ejecutarlo varias veces no duplica nada.
- `frontend/src/pages/ForoPage.jsx`: botón **"+ Tema"** (solo para patólogos y administradores, según D-1) con un formulario de nombre y descripción.
- Pruebas: `TemasInicialesTests` (2, backend) y una nueva en `ForoPage.test.jsx`.
- `README.md`: `seed_data` y la descripción del foro.

**Por qué**
- El foro empezaba sin temas, y la app no tenía forma de crearlos: solo se podía desde `/admin/`.
- Para tener los temas en una base de datos que ya existe, basta con volver a ejecutar `python manage.py seed_data`.

### Las patologías se pueden desactivar en lugar de borrarse (M-5, decisión D-4)

**Qué se cambió**
- `backend/informes/views.py`: `GET /api/patologias/` acepta `?activa=true` o `?activa=false`.
- `frontend/src/pages/InformePage.jsx`: al **crear** un informe, el selector pide solo las patologías activas. Al **editar** pide todas, para que se vea la patología de un informe viejo aunque esté desactivada.
- `frontend/src/pages/PatologiasPage.jsx`: casilla **"Activa"** en el formulario de patologías; las nuevas se crean activas.
- Pruebas: `PatologiasActivasTests` (3, backend), `PatologiasPage.test.jsx` (2, frontend, nuevo) y 2 en `InformePage.test.jsx`.
- `README.md`: nuevo filtro `?activa=` y una frase en las características.

**Por qué**
- El selector de "Nuevo informe" ofrecía también las patologías desactivadas, y la app no tenía forma de activarlas o desactivarlas (solo desde `/admin/`).
- Una patología con informes no se puede borrar (I-1): desactivarla permite retirarla sin perder el historial.

### Corrección: los menús desplegables muestran todos los elementos, no solo los primeros 20

**Qué se cambió**
- `backend/config/paginacion.py` (nuevo): clase `PaginacionEstandar`, que sigue paginando de 20 en 20 pero admite `?page_size=` hasta 1000. Se configura en `settings.REST_FRAMEWORK['DEFAULT_PAGINATION_CLASS']`.
- `frontend/src/api/client.js`: constante `LISTA_COMPLETA` (`{ page_size: 1000 }`). Se usa en el selector de patologías de "Nuevo informe", en los temas del foro y en las categorías y patologías de la pantalla Patologías.
- Pruebas: `TamanoDePaginaTests` (3, backend) y una nueva en `InformePage.test.jsx`.
- Documentación: `CLAUDE.md` y la nota de paginación de la API en el `README.md`.

**Por qué**
- Fallo encontrado durante la limpieza; no estaba en la auditoría. Los listados vienen de 20 en 20 y esas pantallas solo leían la primera página. Con más de 20 patologías, las demás no se podían elegir al crear un informe, ni se veían en la tabla de Patologías.

### Rendimiento: los listados ya no hacen una consulta por fila (M-4)

**Qué se cambió**
- `backend/informes/views.py` y `backend/foro/views.py`: los listados de categorías, temas y publicaciones cuentan sus totales en la misma consulta, con `annotate(Count(...))`. El de publicaciones ya no precarga los comentarios completos, solo las imágenes, que se usan para la portada.
- `backend/informes/serializers.py` y `backend/foro/serializers.py`:
  - `total_patologias` y `total_publicaciones` usan el valor contado y, si no existe (al crear o editar un solo elemento), cuentan aparte.
  - La portada del listado se toma de las imágenes ya precargadas; antes `.first()` hacía una consulta por publicación.
- Se indica el orden de forma explícita (`order_by`) en esos tres listados. Al usar `annotate(Count)`, Django ignora el `Meta.ordering` del modelo: sin esto, el foro habría dejado de mostrar primero las publicaciones fijadas.
- `backend/informes/tests.py`: nueva clase `ConsultasPorListadoTests` con 4 pruebas:
  - el número de consultas no crece al pasar de 5 a 20 elementos;
  - crear una categoría o un tema devuelve su total;
  - los totales y la portada son correctos;
  - los listados conservan su orden.

**Por qué**
- Medido con 20 elementos, los listados de categorías y temas hacían 22 consultas y el de publicaciones 25. Ahora hacen 2, 2 y 3.

### Limpieza: código duplicado y comentarios en español (M-3, M-13)

**Qué se cambió**
- Backend:
  - Nueva propiedad `Usuario.nombre_visible` (nombre completo o, si está vacío, el nombre de usuario). Reemplaza la expresión `nombre_completo or username`, que estaba repetida en 8 lugares: 5 serializers (que ahora usan `CharField(source='autor.nombre_visible')`), el PDF, el token del login y `Usuario.__str__`. La API responde igual.
  - Se tradujeron al español 52 docstrings, comentarios y el texto de ayuda de `seed_data`, en 11 archivos. También se corrigió el docstring de `Patologia`, que todavía mencionaba el campo borrado en M-1.
- Frontend:
  - `src/constants.js` (nuevo): `ROL_LABELS` (antes copiado en 3 archivos) y `ESTADOS_INFORME`.
  - `src/components/EstadoBadge.jsx` (nuevo): la etiqueta de estado del informe, que se repetía en el Dashboard, el Buscador y la página del informe. Antes, cualquier estado distinto de "borrador" se mostraba como "Finalizado"; ahora un estado desconocido se muestra tal cual.
  - `api/client.js`: nueva función `resultados(data)`, que reemplaza `data.results || data` (7 apariciones en 5 páginas).
  - Se tradujeron 11 comentarios.
- Pruebas: `NombreVisibleAutorTests` (2, backend) y `EstadoBadge.test.jsx` (3, frontend). Los mocks de `InformePage.test.jsx` y `ForoPage.test.jsx` ahora conservan las funciones reales del módulo `api/client`.
- Documentación: `CLAUDE.md` (dónde está el código compartido) y una corrección en la auditoría (ver M-13).

**Por qué**
- Con el código repetido, un cambio (por ejemplo, el nombre de un rol) había que hacerlo en varios sitios, y era fácil olvidar alguno.
- La regla 4 de `CLAUDE.md` pide comentarios y documentación en español.

### Limpieza: código y archivos sin usar (M-1, M-2)

**Qué se cambió**
- Backend:
  - Importaciones sin usar: `status` y `permissions` en `accounts/views.py`, `os` en `config/settings.py`, y `inch` y `TA_LEFT` en `informes/utils.py`.
  - Se borró la clase `LoginSerializer` (`accounts/serializers.py`), que no se usaba.
  - Se quitó el campo **`Patologia.campos_requeridos`** del modelo y del serializer, con la migración `informes/migrations/0003_quitar_campos_requeridos.py`. La API ya no devuelve ese campo.
- Frontend:
  - `LoginPage.jsx`: se quitaron `ROL_LABELS` y la variable `user`, que no se usaban.
  - `AuthContext.jsx`: se quitaron `isPatologo` e `isAuditor`. `canWrite` ahora compara directamente el rol.
  - `InformePage.jsx`: se quitaron dos `console.log` de depuración.
- Archivos borrados: `frontend/public/favicon.svg`, `frontend/public/icons.svg`, `frontend/src/assets/hero.png`, `typescript.svg` y `vite.svg` (restos de la plantilla de Vite que nadie usaba). También se borró la carpeta local `frontend/dist/`, que no está en git.
- `frontend/src/context/AuthContext.test.jsx` (nuevo): 3 pruebas que comprueban qué roles pueden escribir.

**Por qué**
- El código que no se usa confunde a quien lee el proyecto. `campos_requeridos` parecía definir los campos obligatorios, pero nunca se leía ni se llenaba (estaba vacío en las 14 patologías). Los obligatorios se definen en `Plantilla.obligatorio`.
- `frontend/dist/` tenía compilada una versión vieja del frontend, todavía con el token en la URL del PDF (I-5). Se regenera con `npm run build`.
- Al quitar `isPatologo` se detectó que `canWrite` dependía de él. Sin el ajuste, los patólogos habrían perdido el permiso de escritura en la interfaz. La prueba nueva de `AuthContext` cubre ese caso: se comprobó que falla si se reintroduce el error.
- **En otros computadores** hay que ejecutar `python manage.py migrate` para aplicar la migración 0003. En el del autor ya se aplicó, después de guardar una copia de seguridad de `db.sqlite3`.

### Corrección: los campos obligatorios de los informes se validan siempre (I-2)

**Qué se cambió**
- `backend/informes/serializers.py`:
  - `InformeSerializer.validate()` valida los campos obligatorios de la plantilla aunque `datos_ingresados` llegue vacío o no llegue. Si un `PATCH` no trae `datos_ingresados` (por ejemplo, porque solo cambia las notas), valida los datos ya guardados.
  - Nueva función `esta_vacio()`: solo cuenta como vacío `None`, un texto en blanco o una lista o diccionario vacíos. **`0` y `false` son respuestas válidas.**
- `backend/informes/tests.py`: nueva clase `CamposObligatoriosTests` con 7 pruebas.
- `README.md`: vuelve a indicar que los campos obligatorios se validan en el backend; la frase se había quitado en I-12 porque no era cierta.

**Por qué**
- La condición `if patologia and datos:` saltaba toda la validación si `datos_ingresados` venía vacío. Desde la API se podía crear un informe sin ningún campo obligatorio.
- `if not valor` trataba el número `0` como "vacío", así que un informe con "Número de ganglios: 0" (un dato clínico real) se rechazaba si llegaba como número por la API.
- La colección de Postman y `iniciar_y_probar.ps1` siguen funcionando: envían todos los campos obligatorios.

### Documentación: README reescrito y colección de Postman actualizada (I-12)

**Qué se cambió**
- `README.md`, reescrito por completo:
  - Se eliminaron las líneas con caracteres de control dañados y los bloques de código rotos.
  - Nueva sección **Roles y Permisos**, con una tabla según las decisiones D-1, D-2 y D-3. Corrige que el administrador no es el único que gestiona el catálogo.
  - Referencia de la API completa, sacada de las rutas reales: autenticación, catálogo (con categorías), informes (con estadísticas) y foro.
  - Nuevas secciones de **Pruebas Automáticas**, **Seguridad** y **Documentación del Proyecto**.
  - Estructura del proyecto actualizada (foro, pruebas, `docs/`).
  - Se corrigieron afirmaciones que no eran ciertas: el PDF no lleva "firma del patólogo", sino su nombre; la búsqueda no es "en tiempo real"; las pruebas exigen Node 22.12+, no Node 18; y `GET /api/plantillas/` lo puede leer cualquier usuario autenticado.
- `PathoLab_API.postman_collection.json`, rehecha:
  - 14 peticiones en 4 carpetas: autenticación, catálogo, informes y foro.
  - El token se configura a nivel de colección y el login lo guarda automáticamente.
  - "Crear informe" y "Crear publicación" guardan su `id` para las peticiones siguientes.
  - El número de caso usa `{{$timestamp}}` para no repetirse.

**Por qué**
- El README tenía 15 líneas dañadas (por ejemplo, "dmin" en lugar de `admin`), no mencionaba el foro ni las categorías, y su tabla de la API estaba incompleta.
- En la colección de Postman, "Listar patologías" no enviaba el token y siempre respondía 401, "Descargar PDF" usaba el informe 1 escrito a mano y "Crear informe" fallaba la segunda vez por repetir el número de caso.
- La colección nueva se ejecutó completa contra una copia de la base de datos: las 14 peticiones respondieron 200 o 201.

### Corrección: la dirección del backend ya no está fija en el código del frontend (I-10)

**Qué se cambió**
- `frontend/src/api/client.js`: `API_URL` deja de ser `'http://localhost:8000/api'` y pasa a ser `VITE_API_URL + '/api'` (se quita una posible barra final). Con `VITE_API_URL` vacía, el frontend llama a `/api/...` en el mismo sitio que la página; en desarrollo esas peticiones las reenvía el proxy de `vite.config.js` al backend. La renovación del token usa la misma dirección.
- `frontend/.env.example`: `VITE_API_URL` vacía, con comentarios sobre cuándo darle valor.
- El `frontend/.env` local del usuario también se dejó con `VITE_API_URL` vacía, con su permiso. Ese archivo no está en git.
- `frontend/src/api/client.test.js` (nuevo): 3 pruebas (sin variable, con variable y con barra final).
- Documentación: pasos de instalación del frontend en el `README.md` (incluido crear el `.env`, y una nota corregida sobre el proxy) y sección del frontend en `CLAUDE.md`.

**Por qué**
- Con la dirección fija en `localhost:8000`, la app solo funcionaba en el computador del desarrollador. Publicada en un servidor, el navegador de cada visitante buscaría el backend en su propio equipo.
- `VITE_API_URL` y el proxy de Vite ya existían, pero el código no los usaba.
- Verificado con las 11 pruebas del frontend, con `vite build` (el resultado ya no contiene `localhost:8000`) y con un login real a través del proxy (Vite en 5199 → Django en 8000: respuesta 200 con token).

### Seguridad: Vite 5 → 6.4 y Vitest 3 → 5 (I-9, parte b)

**Qué se cambió**
- `frontend/package.json` y `package-lock.json`: `vite` ^5.4.0 → ^6.4.3 y `vitest` ^3.2.7 → ^5.0.3. `@vitejs/plugin-react` 4.7 ya era compatible con Vite 6 y no cambió. `vite.config.js` no necesitó cambios.
- `README.md` (insignia y lista de tecnologías) y `CLAUDE.md`: versión de Vite actualizada.

**Por qué**
- Las vulnerabilidades de las herramientas de desarrollo (Vite, esbuild ≤ 0.24.2 y la de Vitest 3, GHSA-82fw-gwwq-j7x9) solo se corregían con versiones principales nuevas. `npm audit` (todo) pasa de 6 vulnerabilidades (1 alta) a **2 moderadas**, que son las de `react-router` ya analizadas en I-9a.
- Se eligió Vite 6.4 en lugar de 7: es el salto más pequeño que cierra todas las vulnerabilidades de desarrollo. Ninguno de los cambios incompatibles de Vite 6 (Sass, `resolve.conditions`, `json.stringify`, modo librería) afecta a la configuración de PathoLab.
- Verificado con las 8 pruebas del frontend, `vite build` y arrancando el servidor de desarrollo, que sirvió la página y transformó `main.jsx` y `App.jsx` sin errores.

### Seguridad: actualización de dependencias del frontend sin cambiar de versión principal (I-9, parte a)

**Qué se cambió**
- `frontend/package-lock.json`: se ejecutó `npm audit fix` (sin `--force`). `package.json` no cambió. Versiones de producción actualizadas: `axios` 1.13.6 → 1.20.0, `react-router-dom` y `react-router` 6.30.3 → 6.30.6, `@remix-run/router` 1.23.2 → 1.23.4, `follow-redirects` 1.15.11 → 1.16.1 y `form-data` 4.0.5 → 4.0.6, además de dependencias internas de estos paquetes. También se actualizaron versiones menores de herramientas de desarrollo (Babel, PostCSS, nanoid, browserslist).

**Por qué**
- `npm audit --omit=dev`, que solo cuenta lo que llega a la app publicada, pasó de **6 vulnerabilidades (2 altas)** a **2 moderadas**. Las altas estaban en `axios` y `form-data`.
- Las 2 que quedan son de `react-router` y solo se corrigen con React Router 7 (cambio de versión principal). Se revisó que **no afectan a PathoLab**:
  - [GHSA-wrjc-x8rr-h8h6](https://github.com/advisories/GHSA-wrjc-x8rr-h8h6), redirección abierta en `<Link>`/`useNavigate`: la app solo navega a rutas fijas o con ids numéricos que devuelve la API, nunca a rutas escritas por el usuario.
  - [GHSA-337j-9hxr-rhxg](https://github.com/advisories/GHSA-337j-9hxr-rhxg): solo afecta a renderizado en servidor (SSR) con `createBrowserRouter`. PathoLab usa `BrowserRouter` sin SSR.
- Verificado con las 8 pruebas del frontend y con `vite build`.

### Seguridad: el registro y el cambio de contraseña aplican los validadores de Django (I-11)

**Qué se cambió**
- `backend/accounts/serializers.py`:
  - Nueva función `validar_contrasena()`, que llama a `validate_password()` de Django y convierte su error en un 400 de DRF.
  - `CambiarPasswordSerializer` la usa en `validate_new_password()`.
  - `RegistroSerializer` la usa en `validate()`, con un `Usuario` temporal sin guardar para poder detectar contraseñas parecidas al usuario. Los errores salen en el campo `password`.
- `backend/accounts/tests.py`: nueva clase `ValidacionContrasenasTests` con 5 pruebas.
- Documentación: nota en `CLAUDE.md` sobre los usuarios de `seed_data`.

**Por qué**
- `settings.py` define 4 validadores (longitud mínima, contraseñas comunes, solo números y parecido al usuario), pero ningún serializer los aplicaba. Se aceptaban contraseñas como `12345678` o `password123`.
- Los mensajes salen en español (`LANGUAGE_CODE = 'es'`), y la página de perfil ya los muestra sin cambios en el frontend.

### Seguridad: en el foro solo un admin fija publicaciones y los comentarios no se pueden mover (I-8)

**Qué se cambió**
- `backend/foro/serializers.py`:
  - `PublicacionSerializer.get_fields()` vuelve `fijado` de solo lectura si quien hace la petición no es admin.
  - `ComentarioSerializer.get_fields()` vuelve `publicacion` de solo lectura al editar un comentario existente.
  - Como en C-1, los valores no permitidos se ignoran en silencio (comportamiento estándar de DRF).
- `backend/foro/tests.py`: nueva clase `CamposProtegidosForoTests` con 5 pruebas.
- Documentación: sección de permisos de `CLAUDE.md`.

**Por qué**
- El modelo dice que "los administradores pueden fijar publicaciones importantes", pero cualquier patólogo podía crear o editar su publicación con `"fijado": true` y dejarla siempre arriba del foro.
- El autor de un comentario podía cambiar su campo `publicacion` con un `PATCH` y moverlo a otra publicación.
- El frontend no necesitó cambios: no tiene botón para fijar y solo envía `publicacion` al crear un comentario.

### Seguridad: límite real de tamaño y validación de las imágenes del foro (I-6)

**Qué se cambió**
- `backend/config/settings.py`:
  - Nuevo ajuste `FORO_MAX_TAMANO_IMAGEN = 10 MB`.
  - Se corrigió el comentario que decía que `DATA_UPLOAD_MAX_MEMORY_SIZE` y `FILE_UPLOAD_MAX_MEMORY_SIZE` limitaban la subida; no lo hacen.
  - Se quitó `FILE_UPLOAD_MAX_MEMORY_SIZE` para usar el valor por defecto de Django (2,5 MB), así los archivos grandes van a disco y no a RAM.
  - Se añadió una nota: en producción, el servidor web debe limitar el tamaño de las peticiones (por ejemplo, `client_max_body_size` en Nginx).
- `backend/foro/views.py` (`subir_imagenes`): antes de guardar nada revisa todos los archivos. Si alguno supera el límite o **no es una imagen real** (se abre con Pillow mediante `forms.ImageField().to_python()`), responde 400. Las imágenes se guardan dentro de `transaction.atomic()`.
- `frontend/src/pages/ForoPage.jsx`:
  - Revisa el tipo y el tamaño de las imágenes **antes** de crear la publicación.
  - Los errores del formulario se muestran dentro del modal; antes quedaban ocultos detrás.
  - Si la publicación se crea pero el backend rechaza las imágenes, cierra el formulario y lo avisa, para que reintentar no cree una publicación duplicada.
- Pruebas: `backend/foro/tests.py` (nuevo, 5 pruebas; las imágenes se guardan en una carpeta temporal) y `frontend/src/pages/ForoPage.test.jsx` (nuevo, 4 pruebas).
- Documentación: `CLAUDE.md` (ajuste `FORO_MAX_TAMANO_IMAGEN`).

**Por qué**
- El "límite de 10 MB" no existía: los ajustes usados no limitan el tamaño de los archivos subidos, y se podía llenar el disco del servidor.
- Durante el arreglo se descubrió algo más grave: `ImagenPublicacion.objects.create()` no valida el `ImageField`, así que el foro aceptaba cualquier archivo con extensión de imagen. Por ejemplo, un HTML con `<script>` llamado `foto.png`.
- En el frontend, una imagen rechazada dejaba una publicación sin imágenes, y al reintentar se creaba otra duplicada.

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
