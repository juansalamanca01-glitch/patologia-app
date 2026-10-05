# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

PathoLab: app web para crear, gestionar y exportar a PDF informes histopatológicos. Backend Django 4.2 + DRF + SimpleJWT en `backend/`, frontend React 18 + Vite 6 en `frontend/`. Todo el dominio (modelos, campos, mensajes, UI) está en español; mantener esa convención.

## Reglas de trabajo (obligatorias)

1. **Confirmar antes de tocar código.** Antes de borrar o modificar código, explicar al usuario qué se va a cambiar y por qué, y esperar su confirmación explícita antes de editar.
2. **CHANGELOG.md.** Todo cambio en el código se registra en `CHANGELOG.md` (raíz del repo; crearlo si no existe) con la fecha (AAAA-MM-DD), qué se cambió (archivos y comportamiento) y por qué.
3. **Documentación al día.** Si un cambio afecta la arquitectura, el backend, el frontend o la base de datos (modelos o migraciones), actualizar también la documentación correspondiente: `docs/`, `README.md` (estructura, endpoints de la API, usuarios de prueba, roadmap) y, si aplica, este `CLAUDE.md`.
4. **Idioma.** Los comentarios del código, los docstrings, la documentación y las entradas del CHANGELOG se escriben en español.
5. **Respetar `docs/decisiones.md`.** Las decisiones registradas ahí son definitivas: el código y la documentación deben cumplirlas aunque contradigan una recomendación de `docs/auditoria-inicial.md` u otro documento. Si un cambio pedido entra en conflicto con una decisión, avisar al usuario antes de hacerlo. Las decisiones nuevas se agregan a ese archivo con fecha, decisión y motivo.
6. **Estado del trabajo en `docs/progreso.md`.**
   - **Al empezar cada conversación nueva**, antes de cualquier otra cosa, leer `docs/progreso.md` para saber qué se hizo, qué falta, cuál es la siguiente tarea, en qué rama se trabaja y qué preguntas esperan respuesta del usuario.
   - **Al terminar cada tarea o etapa**, actualizar `docs/progreso.md` **antes de hacer el commit**, para que vaya en el mismo commit.
   - Actualizarlo también cada vez que quede algo pendiente de confirmar, para que el trabajo se pueda retomar aunque la conversación se corte.

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
python manage.py seed_data        # usuarios de prueba, 14 patologías con sus plantillas, temas del foro, servicios, EPS y 2 pacientes ficticios (idempotente)
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

Las pruebas del backend están en `backend/*/tests.py`: `APITestCase` de DRF para la API y `SimpleTestCase` en `config/tests.py` para la configuración. Las del frontend usan Vitest + React Testing Library + jsdom (configuración en `vite.config.js` y `src/test/setup.js`), en archivos `*.test.jsx` junto al componente, y simulan la API con `vi.mock('../api/client')`. No hay linter configurado. Los hallazgos pendientes de corregir están en `docs/auditoria-inicial.md`. `PathoLab_API.postman_collection.json` contiene la colección de la API.

Usuarios de `seed_data`: `admin/admin1234`, `patologo1/patologo1234` (registro médico `RM-PRUEBA-0001`, que se le asigna también si ya existía sin registro), `auditor1/auditor1234`. `seed_data` los crea directamente, sin validadores. La API (registro y cambio de contraseña) sí aplica `AUTH_PASSWORD_VALIDATORS` mediante `validar_contrasena()` de `accounts/serializers.py`, así que esas contraseñas no se aceptarían como contraseña nueva.

## Configuración

`backend/config/settings.py` lee todo con `python-decouple` desde `backend/.env` (ver `.env.example`):
- `SECRET_KEY` es obligatoria: si falta, `settings.py` lanza `ImproperlyConfigured` y nada arranca (ni `runserver` ni las pruebas). `DEBUG` vale `False` si no se define. Las dos cosas las verifica `backend/config/tests.py`.
- Si `DB_NAME` está definido usa PostgreSQL; si no, SQLite (`backend/db.sqlite3`, con `timeout` de 20 s para esperar en vez de fallar con "database is locked"). Con SQLite, las pruebas usan el archivo `backend/test_db.sqlite3` y no la base en memoria, porque la prueba de concurrencia del número de petición escribe desde varios hilos. Las pruebas corren con `config/test_runner.py`, que usa `DummyCache`: así los límites de peticiones (throttles) no se acumulan entre pruebas. Ninguna prueba debe depender de esos límites.
- `DEBUG=True` activa `CORS_ALLOW_ALL_ORIGINS` y sirve `/media/`; con `DEBUG=False` se usan `CORS_ALLOWED_ORIGINS` y los ajustes HTTPS/HSTS.
- `FORO_MAX_TAMANO_IMAGEN` (10 MB) es el límite por imagen del foro. Lo aplica `foro/views.py` (`subir_imagenes`, que además comprueba con Pillow que el archivo sea una imagen real), y `ForoPage.jsx` repite el valor en `MAX_TAMANO_IMAGEN_MB`: si cambia uno, hay que cambiar el otro.
- Idioma `es`, zona horaria `America/Bogota`.

## Arquitectura

**Apps Django** (rutas en `config/urls.py`):
- `accounts` → `/api/auth/`: `AUTH_USER_MODEL = accounts.Usuario` con campo `rol` (`admin` | `patologo` | `auditor`). El login (`CustomTokenView`) devuelve `access`, `refresh` y `user`. En `/admin/`, `Usuario` usa el `UserAdmin` de Django, con formularios adaptados a `Usuario` (`accounts/admin.py`), para que la contraseña se cifre al crear un usuario. No lo cambies por un `ModelAdmin` común: guardaría la contraseña tal cual (lo vigila `AdminUsuariosTests`).
- `informes` → `/api/`: `Categoria` → `Patologia` → `Plantilla` (campos del formulario dinámico), `Servicio` e `Informe`. También `GET /api/opciones/` (`OpcionesView`).
- `pacientes` → `/api/pacientes/`: `Paciente` (en la raíz, `/api/pacientes/{id}/`, con el historial en `/api/pacientes/{id}/informes/`), el catálogo `EPS` (`/api/pacientes/eps/`) y las listas fijas `TipoDocumento` y `Sexo`. En `urls.py`, `eps` se registra antes que los pacientes y `PacienteViewSet.lookup_value_regex` solo acepta números, para que las dos rutas no se confundan.
- `foro` → `/api/foro/`: `TemaForo`, `Publicacion` (con `ImagenPublicacion`, subidas a `media/foro/publicaciones/<id>/`) y `Comentario`.

**Permisos por rol.** DRF exige autenticación por defecto. Las clases están en `accounts/permissions.py`, y comparan `request.user.rol` como string:
- `EsPatologoOAdmin`: todos leen; escriben solo admin y patólogo.
- `EsPatologoOAdminYSoloAdminBorra` (pacientes, decisión D-11): igual que el anterior, pero `DELETE` es solo del admin.
- En el foro, `fijado` solo lo puede cambiar un admin y la `publicacion` de un comentario no se puede cambiar después de crearlo. Se controla en `get_fields()` de `foro/serializers.py` (auditoría I-8).
- `EsAutorOAdminOSoloLectura` (informes y foro): todos leen; crear requiere admin o patólogo; editar, borrar o finalizar requiere ser el autor o admin (decisión D-2).
- Un `Informe` finalizado no se puede editar ni borrar, ni siquiera por un admin: `InformeViewSet.update` y `destroy` responden 400 (decisión D-3).

En el frontend, `AuthContext` expone `isAdmin`, `isPatologo`, `isAuditor` y `canWrite` para ocultar acciones en la UI; la autorización real la hace el backend.

**Formularios dinámicos e informes.**
- Cada `Patologia` tiene filas `Plantilla` con `campo_nombre`, `tipo_campo` (`texto`, `numero`, `lista`, `textarea`, `boolean`), `opciones` y `orden`. `InformePage.jsx` renderiza el formulario con ellas.
- Los valores se guardan como JSON en `Informe.datos_ingresados`.
- **Número de petición (decisión D-7).** `Informe.save()` asigna `numero_peticion` (`P-AÑO-NNNNN`) al crear el informe, también desde el ORM, `/admin/` o `seed_data`. Usa `siguiente_numero_peticion()` de `informes/models.py`, que incrementa el contador del año (`ConsecutivoPeticion`) con un `UPDATE` atómico dentro de la misma transacción que guarda el informe. No lo cambies por "el mayor número + 1": con dos usuarios a la vez se repite o falla. Lo comprueba `NumeroPeticionConcurrenciaTests`. El número es de solo lectura en la API, no se reutiliza y es el que identifica al informe en listados, búsqueda y PDF. `numero_orden_externa` es opcional y no es único. Ya no existe `numero_caso`.
- En cada create/update, `InformeViewSet` regenera `texto_generado` con `informes/utils.generar_descripcion_macroscopica`. Esa función usa un diccionario `mapeo` de `campo_nombre` → frase: los campos cuyo nombre coincide con una clave (`localizacion`, `dimensiones`, `peso`, `margenes`…) producen una frase redactada; los demás se agregan como `Etiqueta: valor`. Por eso, al añadir plantillas o patologías conviene reutilizar esos nombres de campo.
- `generar_pdf_informe` (ReportLab) arma el PDF con la estructura de la sección 5 de `docs/propuesta-informe-v2.md` (informe v2, etapa 7), en funciones pequeñas: `_encabezado`, `_tabla_datos`, `_titulo`, `_seccion`, `_firma` (que usa `_lineas_firma`), `_aviso_adendas` y `_adendas`.
  - El encabezado es fijo (`ENCABEZADO_LABORATORIO`, `ENCABEZADO_CIUDAD`, de demostración: P-9). Hacerlo configurable por `.env` quedó como propuesta futura por decisión del usuario.
  - Paciente, EPS, servicio y firma salen de `datos_impresos()` (D-10), y la edad de `Informe.edad_paciente()`, que comparte con `InformeSerializer`. Todo texto del usuario pasa por `texto_seguro()` (I-3); un dato vacío se imprime "—".
  - Un borrador no lleva firma y dice "BORRADOR — SIN VALIDEZ" en la fecha de informe y en el pie. Además, `CanvasNumerado` (con `marca_agua='BORRADOR'`) le dibuja una marca de agua en diagonal en cada página.
  - **Decisión D-12:** el PDF de un borrador es una vista previa solo para su autor o un admin. `exportar_pdf` responde 403 a los demás, y el archivo se llama `informe_P-AAAA-NNNNN_borrador.pdf`. En `InformePage`, el botón dice "Vista previa (borrador)" y solo lo ve quien puede editar el informe (`puedeVerPdf`).
  - El pie ("N.º de petición … · Página X de Y · Generado el …", hora de Bogotá) lo dibuja `CanvasNumerado`, el `canvasmaker`, al final, cuando ya se sabe el total de páginas. Las pruebas (`PdfInformeTests`) leen el pie espiando `Canvas.drawCentredString`, y el contenido espiando `Paragraph` y `Table`.
  - Ya no hay sección "DATOS CLÍNICOS": los datos del formulario están redactados en la macroscópica.
  - Si hay adendas, bajo el título va el aviso "Este informe tiene N adenda(s); ver al final." y, después de la firma, la sección "ADENDAS". Cada adenda (con el título de la sección en la primera) va en un `KeepTogether` con sus líneas de firma (`_lineas_firma`, no `_firma`: un `KeepTogether` dentro de otro reparte mal las páginas).
- El PDF se descarga solo por `GET /api/informes/{id}/pdf/` (acción `exportar_pdf`), con el token en la cabecera `Authorization`. `InformePage.jsx` lo pide con `client.get(..., { responseType: 'blob' })` y lo guarda con un enlace temporal `blob:`. Nunca se debe pasar el token por la URL: la antigua ruta `/api/descargar-pdf/...?token=` se eliminó (auditoría I-5).
- `POST /api/informes/{id}/finalizar/` cambia el estado `borrador` → `finalizado` (ver "Firma y finalización").
- `GET /api/informes/estadisticas/` devuelve los totales por estado calculados en el backend. El listado está paginado de 20 en 20 (`PAGE_SIZE`): el frontend usa `count`, `next` y `previous` y nunca debe contar los resultados de una sola página. Los menús desplegables y las listas que deben mostrarlo todo piden `params: LISTA_COMPLETA` (`?page_size=1000`, que permite `config/paginacion.py`). `BuscarPage.jsx` tiene `TAMANO_PAGINA = 20`, que debe coincidir con `PAGE_SIZE`.

**Listas de opciones (informe v2).**
- Las listas fijas son `TextChoices` en el código: `Sexo` y `TipoDocumento` en `pacientes/models.py`, `Informe.TipoEstudio` en `informes/models.py`. `GET /api/opciones/` las devuelve como `{sexos, tipos_documento, tipos_estudio}`, cada elemento con `valor` y `etiqueta`. El frontend debe pedirlas ahí y no copiarlas en `constants.js`. Si agregas una lista fija, agrégala también a `OpcionesView`.
- EPS y servicios son catálogos editables (`EsPatologoOAdmin`, decisión D-11). Se desactivan en lugar de borrarse (D-4), con el filtro `?activa=` (EPS) o `?activo=` (servicios): cada filtro se llama como su campo. Comparten `config/catalogos.py`: `NombreCatalogoMixin` rechaza nombres repetidos sin importar mayúsculas ni espacios, y `filtrar_por_activo()` aplica el filtro. Úsalos en cualquier catálogo nuevo.
- Una EPS o un servicio en uso (`Paciente.eps`, `Informe.eps` e `Informe.servicio` son `PROTECT`) no se borran: `EPSViewSet.destroy` y `ServicioViewSet.destroy` responden 400 y piden desactivarlos. Se administran en `CatalogosPage.jsx` (`/catalogos`).

**Pacientes (informe v2, etapa 3).**
- **Solo datos ficticios** en pruebas, `seed_data`, Postman y ejemplos: nombres como "Paciente Ficticio Uno" y documentos con el prefijo `PRUEBA`. Nunca datos de personas reales. No agregues campos que no salen en el informe (dirección, teléfono, correo): son datos sensibles (Ley 1581 de 2012).
- **La edad no se guarda.** `Paciente.edad_en(fecha)` la devuelve como texto ("45 años", "8 meses", "28 días") y `Paciente.edad` la calcula a hoy (`timezone.localdate()`). El informe usa `edad_en(fecha_ingreso)` (`paciente_datos` en `InformeSerializer`), para que no cambie al reimprimirlo. `Paciente.nombre_completo` y `Paciente.documento` ("CC PRUEBA0001") son las formas de mostrarlo.
- `PacienteSerializer` normaliza el documento (sin espacios ni puntos, en mayúsculas) y comprueba en `validate()` que el tipo y el número no se repitan. Por eso tiene `validators = []`: el validador automático de DRF daría un mensaje en inglés. No se asigna una EPS desactivada, pero el paciente que ya la tenía la conserva.

**Datos de la solicitud (informe v2, etapa 4).**
- `Informe.paciente` es `PROTECT` y admite `null` solo por los informes antiguos. `InformeSerializer._validar_paciente_y_fecha_ingreso` lo exige al crear y no deja quitarlo; un paciente con informes no se borra (400).
- `Informe.eps` es la EPS **del momento del estudio**, no la actual del paciente. Si un informe nuevo no envía `eps`, se copia la del paciente si sigue activa. Una EPS o un servicio desactivados no se asignan, pero el informe que ya los tenía los conserva (como en `PacienteSerializer`).
- `fecha_ingreso` es hoy si no se envía, y no puede estar en el futuro ni ser anterior al nacimiento.
- El listado lleva `paciente_nombre`, `paciente_documento` y `tipo_estudio`, con `select_related('paciente', 'eps', 'servicio')`. Lo vigila `ConsultasListadoInformesTests`: si agregas campos relacionados al listado, agrégalos al `select_related`.
- En el frontend, `InformePage.jsx` usa `components/informe/SelectorPaciente.jsx` y `DatosSolicitud.jsx`. El formulario de paciente (`components/FormularioPaciente.jsx`) se comparte con `PacientesPage` y se dibuja con un portal en `document.body`, porque el informe ya es un `<form>`; su `onSubmit` llama a `stopPropagation()` para que los eventos de React no envíen también el informe. `utils/formularios.js` tiene `hoyISO()` y `conOpcionActual()`, que agrega a la lista de activos el elemento desactivado que el registro ya tenía.

**Contenido del informe (informe v2, etapa 5).**
- `Informe.descripcion_microscopica` y `Informe.comentarios` (antes `notas`, renombrado por la migración 0009 sin perder datos; `notas` ya no existe en la API).
- `Diagnostico` (`informe`, `orden`, `descripcion`, `codigo_cie10`; único por `informe` + `orden`) va anidado en `InformeSerializer` como `diagnosticos`. Si la petición lo trae, `_guardar_diagnosticos` **reemplaza** toda la lista en la misma transacción que el informe; si no lo trae, no cambia. El orden es el de la lista enviada. Máximo `MAX_DIAGNOSTICOS` (20).
- `DiagnosticoSerializer.validate_codigo_cie10` normaliza el código (mayúsculas, sin espacios, agrega el punto: `c443` → `C44.3`) y lo valida con `PATRON_CIE10`. No hay catálogo oficial de CIE-10.
- `InformeViewSet.get_queryset` hace `prefetch_related('diagnosticos')` solo en las rutas de detalle (`self.detail`): el listado no los muestra. Lo vigila `test_el_detalle_no_hace_una_consulta_por_diagnostico`.
- El PDF imprime microscópica, diagnósticos (`1. … (CIE-10: C44.3)`) y comentarios con `texto_seguro()`.
- En el frontend, `components/informe/ListaDiagnosticos.jsx` es controlado: `conClaves()` da a cada fila una `clave` para React y `sinClaves()` la quita antes de enviar. Recibe en `error` un texto o el arreglo de errores por fila que devuelve DRF; `InformePage` conserva ese arreglo sin aplanarlo.

**Firma y finalización (informe v2, etapa 6; decisiones D-8 y D-10).**
- `Usuario.registro_medico` solo lo asigna un admin (`RegistroSerializer` o `/admin/`); en `UsuarioSerializer` es de solo lectura, como `rol`.
- `finalizar` bloquea el informe (`select_for_update(of=('self',))`: en PostgreSQL no se puede bloquear el lado nulo de un `LEFT JOIN`), revisa `Informe.requisitos_faltantes()` (paciente, al menos un diagnóstico, microscópica en histología y registro médico **del autor**, aunque finalice un admin) y, si falta algo, responde 400 con `detail` y `requisitos`. Si todo está bien, en la misma transacción fija `fecha_informe` y guarda `datos_finalizacion = datos_para_congelar()`.
- `fecha_informe` y `datos_finalizacion` son `editable=False`: no se escriben por la API ni en `/admin/`.
- `Informe.datos_impresos()` devuelve los datos congelados si el informe está finalizado y los actuales si es borrador. La usan `InformeSerializer` (`paciente_datos`, `eps_nombre`, `servicio_nombre`, `firma`) y el PDF: cualquier dato nuevo del paciente, la EPS, el servicio o la firma que se muestre debe salir de ahí y agregarse a `datos_para_congelar()`. La edad no se congela: se calcula con `pacientes.models.edad_en_texto()` a partir de la fecha de nacimiento congelada y la fecha de ingreso.
- La migración `informes/0010` completa los informes ya finalizados (`fecha_informe` = `fecha_actualizacion`) con una copia propia de la lógica de `datos_para_congelar()`. Las pruebas de migraciones antiguas vuelven también `accounts` a `0001_initial`: con la columna `registro_medico` el modelo histórico no podría crear usuarios.
- En el frontend, `components/informe/SeccionFirma.jsx` es la tarjeta "Firma" (solo lectura, solo en informes guardados) e `InformePage` muestra la lista `requisitos` si no se puede finalizar. `PerfilPage` muestra el registro médico en solo lectura.

**Adendas (informe v2, etapa 8; decisión D-9).**
- Un informe finalizado se corrige con `Adenda` (`informe` y `autor` son `PROTECT`; `numero`, `motivo` de 300, `texto`, `fecha` y `firma` en JSON; única por `informe` + `numero`). La adenda **no modifica** el informe (D-3): ni su contenido, ni `fecha_actualizacion`, ni `datos_finalizacion`.
- `GET` y `POST /api/informes/{id}/adendas/` (acción `adendas` de `InformeViewSet`); no hay PUT, PATCH ni DELETE (405). `get_object()` aplica el permiso: crear es del autor del informe o de un admin (D-2). Responde 400 si el informe es un borrador o si **quien la crea** no tiene registro médico, aunque sea admin, porque la firma es la suya.
- La firma sale de `firma_de(usuario)` en `informes/models.py`, la misma que usa `Informe.firma_actual()`, y se guarda congelada. El número se calcula como el máximo + 1 con el informe bloqueado (`select_for_update`); la restricción única es el respaldo (en SQLite no hay bloqueo), y un choque responde 400 "intente de nuevo".
- `AdendaSerializer` solo escribe `motivo` y `texto`. `InformeSerializer` trae `adendas` (solo lectura); se cargan con `prefetch_related('adendas')` solo en las rutas de detalle, como los diagnósticos, y el listado no las muestra. En `/admin/`, `AdendaInline` es de solo lectura.
- En el frontend, `components/informe/SeccionAdendas.jsx` es la tarjeta "Adendas", solo en informes finalizados. `InformePage` la dibuja **fuera** de su `<form>`, porque tiene su propio formulario y su propia petición. Pide confirmación antes de guardar y, al guardar, `onAgregada` agrega la adenda a `informe.adendas` sin recargar. Reutiliza `LineasFirma` y `formatoFechaHora` de `SeccionFirma.jsx`.

**Cambios sin guardar en el informe (decisión D-13).**
- `InformePage` cuenta los cambios del usuario (`version`; cada `onChange` llama a `marcarCambio()`) y compara con `versionGuardada`. Si se agrega un campo editable al informe, su `onChange` debe llamar a `marcarCambio()`.
- Con cambios sin guardar, `useBlocker` muestra el aviso (Seguir editando, Salir sin guardar, Guardar y salir) y `beforeunload` cubre cerrar o recargar. "Guardar y salir" no sale si falla la validación. No se frena la salida a `/login` (solo ocurre si la sesión ya terminó).
- **Cerrar sesión pasa por `/salir`:** "Salir" del `Navbar` solo navega a `/salir` (`CerrarSesionPage`), que llama a `logout()` y lleva a `/login`. No llames a `logout()` directamente desde un botón: el aviso del informe no aparecería.
- Finalizar y la vista previa del PDF de un borrador llaman a `guardarCambiosPendientes()`: si hay cambios sin guardar, se guardan primero, y si no son válidos no siguen.
- Un borrador existente se autoguarda `ESPERA_AUTOGUARDADO_MS` (5 s) después del último cambio, solo si `calcularErrores()` está vacío. Un informe nuevo nunca se autoguarda (gastaría un número de petición, D-7), y nunca se guarda nada en el navegador.

**Rate limiting.** En `settings.REST_FRAMEWORK` están los throttles globales (`anon`, `user`) y otros por scope (`login`, `registro`, `foro_publicacion`, `foro_comentario`). Los de scope se asignan en `accounts/throttles.py` y en `get_throttles()` de las vistas del foro. Si un endpoint nuevo usa un scope nuevo, hay que agregarlo a `DEFAULT_THROTTLE_RATES`.

**Frontend.**
- `src/api/client.js` es la instancia Axios. Su `baseURL` es `VITE_API_URL + "/api"` (`frontend/.env`). En desarrollo `VITE_API_URL` va vacía: las peticiones a `/api/...` las reenvía el proxy de `vite.config.js` a `localhost:8000`. No escribas direcciones fijas del backend en el código (auditoría I-10). Agrega el `Bearer` desde `localStorage` (`access_token`) y, ante un 401, intenta refrescar con `refresh_token`; si falla, redirige a `/login`. **Los tokens de renovación rotan y están en lista negra** (`token_blacklist`, `BLACKLIST_AFTER_ROTATION`, decisión D-6): cada renovación devuelve un `refresh` nuevo que hay que guardar, porque el anterior deja de servir. `AuthContext.logout()` llama a `POST /api/auth/logout/`, y cambiar la contraseña invalida todos los `refresh` del usuario y devuelve un par nuevo.
- Las rutas están en `App.jsx`, en un router de datos (`createBrowserRouter` + `RouterProvider`, creado al montar `App`), que es lo que exige `useBlocker` (D-13). Las pruebas de una pantalla que use `useBlocker` deben renderizarla con `createMemoryRouter`, no con `<MemoryRouter>`. Hay tres wrappers:
  - `ProtectedRoute`: requiere sesión y añade Navbar y Footer.
  - `PublicRoute`: solo para `/login`.
  - `LegalRoute`: páginas legales, visibles con o sin sesión. Sin sesión muestran el `Footer` y el enlace "← Volver al inicio de sesión". `LoginPage` también dibuja el `Footer`, para que la política de privacidad se pueda leer antes de entrar.
- Los estilos globales están en `src/index.css`; no hay librería de UI.
- `hooks/useOpciones.js` pide `/api/opciones/` una sola vez y la guarda para toda la sesión del navegador; `etiquetaDe(lista, valor)` da la etiqueta de un valor. En las pruebas, llama a `reiniciarOpciones()` en `beforeEach` para que cada prueba vuelva a pedir las opciones a su simulación.
- Código compartido: las etiquetas de rol (`ROL_LABELS`) y de estado del informe están en `src/constants.js`; la etiqueta de estado se dibuja con `<EstadoBadge estado={...} />`, y `resultados(data)` de `api/client.js` saca la lista de un listado paginado. En el backend, el nombre para mostrar de un usuario es `Usuario.nombre_visible`. Úsalos en lugar de repetir esa lógica.
