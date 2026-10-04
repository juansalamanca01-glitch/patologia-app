# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

PathoLab: app web para crear, gestionar y exportar a PDF informes histopatológicos. Backend Django 4.2 + DRF + SimpleJWT en `backend/`, frontend React 18 + Vite en `frontend/`. Todo el dominio (modelos, campos, mensajes, UI) está en español; mantener esa convención.

## Reglas de trabajo (obligatorias)

1. **Confirmar antes de tocar código.** Antes de borrar o modificar código, explicar al usuario qué se va a cambiar y por qué, y esperar su confirmación explícita antes de editar.
2. **CHANGELOG.md.** Todo cambio en el código se registra en `CHANGELOG.md` (raíz del repo; crearlo si no existe) con la fecha (AAAA-MM-DD), qué se cambió (archivos y comportamiento) y por qué.
3. **Documentación al día.** Si un cambio afecta la arquitectura, el backend, el frontend o la base de datos (modelos o migraciones), actualizar también la documentación correspondiente: `docs/`, `README.md` (estructura, endpoints de la API, usuarios de prueba, roadmap) y, si aplica, este `CLAUDE.md`.
4. **Idioma.** Los comentarios del código, los docstrings, la documentación y las entradas del CHANGELOG se escriben en español.
5. **Respetar `docs/decisiones.md`.** Las decisiones registradas ahí son definitivas: el código y la documentación deben cumplirlas aunque contradigan una recomendación de `docs/auditoria-inicial.md` u otro documento. Si un cambio pedido entra en conflicto con una decisión, avisar al usuario antes de hacerlo. Las decisiones nuevas se agregan a ese archivo con fecha, decisión y motivo.
6. **Estado del trabajo en `docs/progreso.md`.** Al empezar una sesión, leer `docs/progreso.md` para saber en qué rama se trabaja, qué está hecho, qué sigue y qué preguntas esperan respuesta del usuario. Actualizarlo al terminar cada tarea (en el mismo commit) y cada vez que quede algo pendiente de confirmar, para que el trabajo se pueda retomar aunque la conversación se corte.

## Comandos

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

Usuarios de `seed_data`: `admin/admin1234`, `patologo1/patologo1234`, `auditor1/auditor1234`.

## Configuración

`backend/config/settings.py` lee todo con `python-decouple` desde `backend/.env` (ver `.env.example`):
- `SECRET_KEY` es obligatoria: si falta, `settings.py` lanza `ImproperlyConfigured` y nada arranca (ni `runserver` ni las pruebas). `DEBUG` vale `False` si no se define. Las dos cosas las verifica `backend/config/tests.py`.
- Si `DB_NAME` está definido usa PostgreSQL; si no, SQLite (`backend/db.sqlite3`).
- `DEBUG=True` activa `CORS_ALLOW_ALL_ORIGINS` y sirve `/media/`; con `DEBUG=False` se usan `CORS_ALLOWED_ORIGINS` y los ajustes HTTPS/HSTS.
- Idioma `es`, zona horaria `America/Bogota`.

## Arquitectura

**Apps Django** (rutas en `config/urls.py`):
- `accounts` → `/api/auth/`: `AUTH_USER_MODEL = accounts.Usuario` con campo `rol` (`admin` | `patologo` | `auditor`). El login (`CustomTokenView`) devuelve `access`, `refresh` y `user`.
- `informes` → `/api/`: `Categoria` → `Patologia` → `Plantilla` (campos del formulario dinámico) e `Informe`.
- `foro` → `/api/foro/`: `TemaForo`, `Publicacion` (con `ImagenPublicacion`, subidas a `media/foro/publicaciones/<id>/`) y `Comentario`.

**Permisos por rol.** DRF exige autenticación por defecto. Las clases están en `accounts/permissions.py`, y comparan `request.user.rol` como string:
- `EsPatologoOAdmin`: todos leen; escriben solo admin y patólogo.
- `EsAutorOAdminOSoloLectura` (informes y foro): todos leen; crear requiere admin o patólogo; editar, borrar o finalizar requiere ser el autor o admin (decisión D-2).
- Un `Informe` finalizado no se puede editar ni borrar, ni siquiera por un admin: `InformeViewSet.update` y `destroy` responden 400 (decisión D-3).

En el frontend, `AuthContext` expone `isAdmin`, `isPatologo`, `isAuditor` y `canWrite` para ocultar acciones en la UI; la autorización real la hace el backend.

**Formularios dinámicos e informes.**
- Cada `Patologia` tiene filas `Plantilla` con `campo_nombre`, `tipo_campo` (`texto`, `numero`, `lista`, `textarea`, `boolean`), `opciones` y `orden`. `InformePage.jsx` renderiza el formulario con ellas.
- Los valores se guardan como JSON en `Informe.datos_ingresados`.
- En cada create/update, `InformeViewSet` regenera `texto_generado` con `informes/utils.generar_descripcion_macroscopica`. Esa función usa un diccionario `mapeo` de `campo_nombre` → frase: los campos cuyo nombre coincide con una clave (`localizacion`, `dimensiones`, `peso`, `margenes`…) producen una frase redactada; los demás se agregan como `Etiqueta: valor`. Por eso, al añadir plantillas o patologías conviene reutilizar esos nombres de campo.
- `generar_pdf_informe` (ReportLab) arma el PDF.
- Hay dos rutas de descarga del PDF:
  - `/api/informes/{id}/pdf/`: acción del ViewSet, autenticada por header JWT.
  - `/api/descargar-pdf/<id>/<filename>?token=<access>`: vista Django `csrf_exempt` que valida el token recibido por query string. Es la que usa el frontend, mediante un formulario o navegación.
- `POST /api/informes/{id}/finalizar/` cambia el estado `borrador` → `finalizado`.
- `GET /api/informes/estadisticas/` devuelve los totales por estado calculados en el backend. El listado está paginado de 20 en 20 (`PAGE_SIZE`): el frontend usa `count`, `next` y `previous` y nunca debe contar los resultados de una sola página. `BuscarPage.jsx` tiene `TAMANO_PAGINA = 20`, que debe coincidir con `PAGE_SIZE`.

**Rate limiting.** En `settings.REST_FRAMEWORK` están los throttles globales (`anon`, `user`) y otros por scope (`login`, `registro`, `foro_publicacion`, `foro_comentario`). Los de scope se asignan en `accounts/throttles.py` y en `get_throttles()` de las vistas del foro. Si un endpoint nuevo usa un scope nuevo, hay que agregarlo a `DEFAULT_THROTTLE_RATES`.

**Frontend.**
- `src/api/client.js` es la instancia Axios con `baseURL` **fija** en `http://localhost:8000/api`. No usa `VITE_API_URL` ni el proxy `/api` de `vite.config.js`. Agrega el `Bearer` desde `localStorage` (`access_token`) y, ante un 401, intenta refrescar con `refresh_token`; si falla, redirige a `/login`.
- Las rutas están en `App.jsx` con tres wrappers:
  - `ProtectedRoute`: requiere sesión y añade Navbar y Footer.
  - `PublicRoute`: solo para `/login`.
  - `LegalRoute`: páginas legales, visibles con o sin sesión.
- Los estilos globales están en `src/index.css`; no hay librería de UI.
