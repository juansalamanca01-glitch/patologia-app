# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

PathoLab: app web para crear, gestionar y exportar a PDF informes histopatológicos. Backend Django 4.2 + DRF + SimpleJWT en `backend/`, frontend React 18 + Vite 6 en `frontend/`. Todo el dominio (modelos, campos, mensajes, UI) está en español; mantener esa convención.

## Reglas de trabajo (obligatorias)

1. **Confirmar antes de tocar código.** Antes de borrar o modificar código, explicar al usuario qué se va a cambiar y por qué, y esperar su confirmación explícita antes de editar.
2. **CHANGELOG.md.** Todo cambio en el código se registra en `CHANGELOG.md` (raíz del repo; crearlo si no existe) con la fecha (AAAA-MM-DD), qué se cambió (archivos y comportamiento) y por qué.
3. **Documentación al día.** Si un cambio afecta la arquitectura, el backend, el frontend o la base de datos (modelos o migraciones), actualizar también la documentación correspondiente: `docs/`, `README.md` (estructura, endpoints de la API, usuarios de prueba, roadmap) y, si aplica, este `CLAUDE.md`.
4. **Idioma.** Los comentarios del código, los docstrings, la documentación y las entradas del CHANGELOG se escriben en español.
5. **Respetar `docs/decisiones.md`.** Las decisiones registradas ahí son definitivas: el código y la documentación deben cumplirlas aunque contradigan una recomendación de `docs/auditoria-inicial.md` u otro documento. Si un cambio pedido entra en conflicto con una decisión, avisar al usuario antes de hacerlo. Las decisiones nuevas se agregan a ese archivo con fecha, decisión y motivo.
6. **Estado del trabajo en `docs/progreso.md`.** Al empezar una sesión, leer `docs/progreso.md` para saber en qué rama se trabaja, qué está hecho, qué sigue y qué preguntas esperan respuesta del usuario. Actualizarlo al terminar cada tarea (en el mismo commit) y cada vez que quede algo pendiente de confirmar, para que el trabajo se pueda retomar aunque la conversación se corte.

## Comandos

Desde la raíz (después de `npm install` en la raíz):
```powershell
npm run dev      # arranca backend (8000) y frontend (5173) juntos; Ctrl + C detiene los dos
npm test         # pruebas de scripts/ (comprobaciones previas de npm run dev)
```
`scripts/dev.mjs` revisa el entorno con `scripts/entorno.mjs` (venv, `backend/.env`, `frontend/node_modules`), avisa de migraciones pendientes (`migrate --check`) y lanza los dos servidores con `concurrently`.

Backend (desde `backend/`, con el venv activado: `.\venv\Scripts\Activate.ps1`):
```powershell
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data        # usuarios de prueba + 14 patologías con sus plantillas (idempotente)
python manage.py runserver        # http://127.0.0.1:8000
python manage.py makemigrations <app>
python manage.py test                                  # todas las pruebas
python manage.py test accounts                         # pruebas de una app
python manage.py test accounts.tests.PerfilCamposProtegidosTests.test_no_puede_cambiar_su_rol  # una sola prueba
```

Frontend (desde `frontend/`):
```powershell
npm install
npm run dev      # http://localhost:5173
npm run build
npm test         # pruebas con Vitest (una vez)
npm run test:watch  # pruebas en modo observación
npx vitest run src/pages/PerfilPage.test.jsx  # un solo archivo de pruebas
```

Las pruebas del backend están en `backend/*/tests.py`: `APITestCase` de DRF para la API y `SimpleTestCase` en `config/tests.py` para la configuración. Las del frontend usan Vitest + React Testing Library + jsdom (configuración en `vite.config.js` y `src/test/setup.js`), en archivos `*.test.jsx` junto al componente, y simulan la API con `vi.mock('../api/client')`. No hay linter configurado. Los hallazgos pendientes de corregir están en `docs/auditoria-inicial.md`. `iniciar_y_probar.ps1` (raíz) instala dependencias, migra, siembra datos, levanta el backend y prueba endpoints con el usuario `patologo1`. `PathoLab_API.postman_collection.json` contiene la colección de la API.

Usuarios de `seed_data`: `admin/admin1234`, `patologo1/patologo1234`, `auditor1/auditor1234`. `seed_data` los crea directamente, sin validadores. La API (registro y cambio de contraseña) sí aplica `AUTH_PASSWORD_VALIDATORS` mediante `validar_contrasena()` de `accounts/serializers.py`, así que esas contraseñas no se aceptarían como contraseña nueva.

## Configuración

`backend/config/settings.py` lee todo con `python-decouple` desde `backend/.env` (ver `.env.example`):
- `SECRET_KEY` es obligatoria: si falta, `settings.py` lanza `ImproperlyConfigured` y nada arranca (ni `runserver` ni las pruebas). `DEBUG` vale `False` si no se define. Las dos cosas las verifica `backend/config/tests.py`.
- Si `DB_NAME` está definido usa PostgreSQL; si no, SQLite (`backend/db.sqlite3`).
- `DEBUG=True` activa `CORS_ALLOW_ALL_ORIGINS` y sirve `/media/`; con `DEBUG=False` se usan `CORS_ALLOWED_ORIGINS` y los ajustes HTTPS/HSTS.
- `FORO_MAX_TAMANO_IMAGEN` (10 MB) es el límite por imagen del foro. Lo aplica `foro/views.py` (`subir_imagenes`, que además comprueba con Pillow que el archivo sea una imagen real), y `ForoPage.jsx` repite el valor en `MAX_TAMANO_IMAGEN_MB`: si cambia uno, hay que cambiar el otro.
- Idioma `es`, zona horaria `America/Bogota`.

## Arquitectura

**Apps Django** (rutas en `config/urls.py`):
- `accounts` → `/api/auth/`: `AUTH_USER_MODEL = accounts.Usuario` con campo `rol` (`admin` | `patologo` | `auditor`). El login (`CustomTokenView`) devuelve `access`, `refresh` y `user`.
- `informes` → `/api/`: `Categoria` → `Patologia` → `Plantilla` (campos del formulario dinámico) e `Informe`.
- `foro` → `/api/foro/`: `TemaForo`, `Publicacion` (con `ImagenPublicacion`, subidas a `media/foro/publicaciones/<id>/`) y `Comentario`.

**Permisos por rol.** DRF exige autenticación por defecto. Las clases están en `accounts/permissions.py`, y comparan `request.user.rol` como string:
- `EsPatologoOAdmin`: todos leen; escriben solo admin y patólogo.
- En el foro, `fijado` solo lo puede cambiar un admin y la `publicacion` de un comentario no se puede cambiar después de crearlo. Se controla en `get_fields()` de `foro/serializers.py` (auditoría I-8).
- `EsAutorOAdminOSoloLectura` (informes y foro): todos leen; crear requiere admin o patólogo; editar, borrar o finalizar requiere ser el autor o admin (decisión D-2).
- Un `Informe` finalizado no se puede editar ni borrar, ni siquiera por un admin: `InformeViewSet.update` y `destroy` responden 400 (decisión D-3).

En el frontend, `AuthContext` expone `isAdmin`, `isPatologo`, `isAuditor` y `canWrite` para ocultar acciones en la UI; la autorización real la hace el backend.

**Formularios dinámicos e informes.**
- Cada `Patologia` tiene filas `Plantilla` con `campo_nombre`, `tipo_campo` (`texto`, `numero`, `lista`, `textarea`, `boolean`), `opciones` y `orden`. `InformePage.jsx` renderiza el formulario con ellas.
- Los valores se guardan como JSON en `Informe.datos_ingresados`.
- En cada create/update, `InformeViewSet` regenera `texto_generado` con `informes/utils.generar_descripcion_macroscopica`. Esa función usa un diccionario `mapeo` de `campo_nombre` → frase: los campos cuyo nombre coincide con una clave (`localizacion`, `dimensiones`, `peso`, `margenes`…) producen una frase redactada; los demás se agregan como `Etiqueta: valor`. Por eso, al añadir plantillas o patologías conviene reutilizar esos nombres de campo.
- `generar_pdf_informe` (ReportLab) arma el PDF.
- El PDF se descarga solo por `GET /api/informes/{id}/pdf/` (acción `exportar_pdf`), con el token en la cabecera `Authorization`. `InformePage.jsx` lo pide con `client.get(..., { responseType: 'blob' })` y lo guarda con un enlace temporal `blob:`. Nunca se debe pasar el token por la URL: la antigua ruta `/api/descargar-pdf/...?token=` se eliminó (auditoría I-5).
- `POST /api/informes/{id}/finalizar/` cambia el estado `borrador` → `finalizado`.
- `GET /api/informes/estadisticas/` devuelve los totales por estado calculados en el backend. El listado está paginado de 20 en 20 (`PAGE_SIZE`): el frontend usa `count`, `next` y `previous` y nunca debe contar los resultados de una sola página. Los menús desplegables y las listas que deben mostrarlo todo piden `params: LISTA_COMPLETA` (`?page_size=1000`, que permite `config/paginacion.py`). `BuscarPage.jsx` tiene `TAMANO_PAGINA = 20`, que debe coincidir con `PAGE_SIZE`.

**Rate limiting.** En `settings.REST_FRAMEWORK` están los throttles globales (`anon`, `user`) y otros por scope (`login`, `registro`, `foro_publicacion`, `foro_comentario`). Los de scope se asignan en `accounts/throttles.py` y en `get_throttles()` de las vistas del foro. Si un endpoint nuevo usa un scope nuevo, hay que agregarlo a `DEFAULT_THROTTLE_RATES`.

**Frontend.**
- `src/api/client.js` es la instancia Axios. Su `baseURL` es `VITE_API_URL + "/api"` (`frontend/.env`). En desarrollo `VITE_API_URL` va vacía: las peticiones a `/api/...` las reenvía el proxy de `vite.config.js` a `localhost:8000`. No escribas direcciones fijas del backend en el código (auditoría I-10). Agrega el `Bearer` desde `localStorage` (`access_token`) y, ante un 401, intenta refrescar con `refresh_token`; si falla, redirige a `/login`. **Los tokens de renovación rotan y están en lista negra** (`token_blacklist`, `BLACKLIST_AFTER_ROTATION`, decisión D-6): cada renovación devuelve un `refresh` nuevo que hay que guardar, porque el anterior deja de servir. `AuthContext.logout()` llama a `POST /api/auth/logout/`, y cambiar la contraseña invalida todos los `refresh` del usuario y devuelve un par nuevo.
- Las rutas están en `App.jsx` con tres wrappers:
  - `ProtectedRoute`: requiere sesión y añade Navbar y Footer.
  - `PublicRoute`: solo para `/login`.
  - `LegalRoute`: páginas legales, visibles con o sin sesión.
- Los estilos globales están en `src/index.css`; no hay librería de UI.
- Código compartido: las etiquetas de rol (`ROL_LABELS`) y de estado del informe están en `src/constants.js`; la etiqueta de estado se dibuja con `<EstadoBadge estado={...} />`, y `resultados(data)` de `api/client.js` saca la lista de un listado paginado. En el backend, el nombre para mostrar de un usuario es `Usuario.nombre_visible`. Úsalos en lugar de repetir esa lógica.
