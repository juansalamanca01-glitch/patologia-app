# Plan: calidad, seguridad y diseño

**Fecha:** 2026-10-08
**Estado:** aprobado por el usuario el 2026-10-08, con un cambio: las fases 5 y 6 las aprueban el usuario, el equipo y el profesor.
- Ese mismo día se cerraron la fase 1 y la tarea previa 1.
- También se agregaron la tarea previa 2 y los puntos del inventario de pendientes.

Lo que no pertenece a ninguna fase está en "Pendientes" de `docs/progreso.md`: producción, decisiones del usuario e ideas futuras.

**Objetivo:** después del informe v2 y de los ajustes de la prueba manual (Bloque A), el trabajo sigue en 8 fases:
- dejar el PDF sobrio;
- agregar herramientas de calidad;
- auditar la seguridad según OWASP Top 10:2025 y corregir lo que el usuario decida;
- rediseñar la interfaz con una guía aprobada antes;
- cerrar con una revisión completa de la documentación y una prueba manual.

Como en `docs/propuesta-informe-v2.md`, cada fase se aprueba y se cierra antes de empezar la siguiente.

---

## 0. Procedimiento común a todas las fases

Cada fase sigue las reglas de `CLAUDE.md`:

1. **Rama propia desde `main`**, con el nombre `fase-N-descripcion` (por ejemplo, `fase-2-herramientas-calidad`). La fase 1 es la excepción (ver la fase 1).
2. **Prueba que falla primero**, cuando la fase cambia comportamiento que se puede probar.
3. **Explicación del cambio y confirmación del usuario** antes de tocar el código.
4. **Documentación en el mismo commit:**
   - `CHANGELOG.md` siempre;
   - `README.md` si el cambio afecta algo que el README describe;
   - `CLAUDE.md` y `docs/` cuando corresponda;
   - `docs/decisiones.md` si sale una decisión nueva.
5. **`docs/progreso.md` al terminar la fase**, antes del commit, para que vaya en el mismo commit. También se actualiza cuando algo queda esperando respuesta del usuario.
6. **Commit y `git push`** de la rama.
7. **Unión a `main`** (fast-forward, con todas las pruebas en verde), solo después de preguntar al usuario. La siguiente fase sale de ese `main` actualizado.

En este documento, "todas las pruebas" son:
- las de la raíz (`npm test`);
- las del backend (`python manage.py test`);
- las del frontend (`npm test` en `frontend/`).

Desde la fase 2 se suman las comprobaciones de formato y linter.

---

## Tarea previa 1: `patologo2` en `seed_data` (terminada)

**Qué se encontró:**
- `seed_data` crea solo `admin`, `patologo1` y `auditor1` (`backend/informes/management/commands/seed_data.py`). No crea `patologo2`.
- El README ("Usuarios y Cuentas de Prueba") y `CLAUDE.md` mencionan solo esos tres.
- `patologo2` existe en la base local porque se creó a mano con `create_user` para la prueba manual del 2026-10-05 (`CHANGELOG.md`, entrada del 2026-10-05). Quien instale el proyecto desde cero no lo tiene, y no puede probar que un patólogo no modifica los informes de otro (decisión D-2).

**Qué se propone:**
- `seed_data` crea `patologo2` / `patologo2345`, con estos datos:
  - nombre ficticio (por ejemplo, "Dra. Ana Ficticia");
  - especialidad "Patología Quirúrgica";
  - registro médico ficticio `RM-PRUEBA-0002`, para que también pueda finalizar sus propios informes.
- Si `patologo2` ya existe, no se toca: ni su contraseña ni su registro. Ese es el caso de la base local del usuario, que lo creó a mano.
- **Pruebas** (en `accounts/tests.py`, junto a las de `patologo1`):
  - `seed_data` crea `patologo2` con su registro médico;
  - ejecutarlo dos veces no lo duplica;
  - si `patologo2` ya existía, no lo cambia.
- **Documentación:**
  - README: tabla de usuarios, con una nota sobre para qué sirve (probar D-2);
  - `CLAUDE.md`: usuarios de `seed_data`;
  - Postman: mencionarlo en la descripción del login;
  - `CHANGELOG.md` y `docs/progreso.md`.

**Archivos:** `backend/informes/management/commands/seed_data.py`, `backend/accounts/tests.py`, `README.md`, `CLAUDE.md`, `PathoLab_API.postman_collection.json`, `CHANGELOG.md`, `docs/progreso.md`.

**Rama:** `seed-patologo2`, desde `main`, después de la fase 1 y antes de la fase 2. **Aprobada el 2026-10-08** con `patologo2345` y `RM-PRUEBA-0002`. **Terminada el 2026-10-08.**

**Terminada cuando:**
- las 3 pruebas nuevas pasan;
- `python manage.py seed_data` en una base vacía permite entrar como `patologo2`;
- el README lista los 4 usuarios.

---

## Tarea previa 2: encabezado del PDF configurable

**Origen:**
- Observación del usuario del 2026-10-08: el encabezado "PathoLab — Laboratorio de Patología (demostración)" probablemente no se quede así.
- Ya estaba anotado como propuesta futura:
  - `docs/propuesta-informe-v2.md`, sección 5.1 (respuesta P-9);
  - la hoja de ruta del README;
  - `CLAUDE.md`;
  - `docs/progreso.md`.

**Qué se hace:**
- **Configuración:** `backend/config/settings.py` lee con `python-decouple`, desde `backend/.env`:

  | Variable | Valor por defecto |
  |---|---|
  | `LABORATORIO_NOMBRE` | "PathoLab — Laboratorio de Patología (demostración)" |
  | `LABORATORIO_DIRECCION` | "Santiago de Cali, Colombia" (el texto de la segunda línea actual) |
  | `LABORATORIO_TELEFONO` | vacío |

  Sin `.env`, o sin estas variables, el PDF queda exactamente igual que hoy.
- **PDF:** `_encabezado()` (`backend/informes/utils.py`) usa esos valores en lugar de las constantes `ENCABEZADO_LABORATORIO` y `ENCABEZADO_CIUDAD`.
  - Si el teléfono está vacío, no se imprime su línea.
  - Los valores pasan por `texto_seguro()`, como todo texto que no escribe el programa (I-3): ReportLab interpreta etiquetas.
- **`.env.example`:** explica las tres variables, con un ejemplo ficticio. No se usa el nombre ni los datos de ningún laboratorio real.
- **Pruebas** (en `PdfInformeTests`, con `override_settings`):
  - sin configurar, se imprimen los valores por defecto;
  - con valores propios, se imprimen esos;
  - con teléfono, aparece su línea; sin teléfono, no;
  - un valor con `<` o `&` sale escapado;
  - un valor con tildes y raya (—) leído del `.env` se imprime bien (codificación UTF-8).

**Archivos:**
- Código: `backend/config/settings.py`, `backend/.env.example`, `backend/informes/utils.py` y `backend/informes/tests.py`.
- Documentación:
  - README: "Características", la configuración del `.env` y la hoja de ruta, donde el punto se marca como hecho;
  - `CLAUDE.md`: hoy dice que el encabezado es fijo;
  - `docs/propuesta-informe-v2.md`: nota en la sección 5.1;
  - `CHANGELOG.md` y `docs/progreso.md`.

**Rama:** `encabezado-configurable`, desde `main`, después de la tarea previa 1 y antes de la fase 2. Pedida por el usuario el 2026-10-08. **Antes de implementarla, se explica y se espera confirmación.**

**Terminada cuando:**
- las pruebas nuevas pasan;
- cambiar `LABORATORIO_NOMBRE` en `backend/.env` y reiniciar el backend cambia el encabezado del PDF;
- sin las variables, el PDF es idéntico al actual.

**Relación con el cambio de nombre:** el nombre del proyecto no está decidido (ver "Pendientes" en `docs/progreso.md`). Con esta tarea, el encabezado del PDF de una instalación se cambia en `.env`, sin tocar código. El valor por defecto, en cambio, se cambia junto con el resto del nombre.

---

## Fase 1: PDF en negro

**Origen:** Bloque B, punto 4 de `docs/progreso.md` (observación de la prueba manual del 2026-10-05).

**Qué se hace:**
- Todo el texto y las líneas del PDF en negro, sin azul ni gris.
- El rojo queda solo en el aviso de adendas y en la marca de agua BORRADOR, porque son alertas (aprobado el 2026-10-08).
- Los títulos en negrita, con `fontName='Helvetica-Bold'` escrito en el estilo.
- La línea gruesa azul bajo el encabezado pasa a una línea fina negra (0.75 puntos).

**Archivos:** `backend/informes/utils.py`, `backend/informes/tests.py`, `CHANGELOG.md`, `CLAUDE.md`, `docs/progreso.md`.

**Estado: ya implementada el 2026-10-08**, antes de escribir este plan:
- Rama `bloque-b-estetica`, que salió de `main` como pide el procedimiento.
- Commit `8021597`, con 3 pruebas nuevas en `PdfInformeTests`. Fallaron antes del cambio y pasan después.
- Commit `9e56342`, que saca del repositorio la skill que se había colado.
- Las dos ramas están subidas a GitHub.

**Cierre (2026-10-08):**
- El usuario revisó el PDF y confirmó que se ve como lo pidió, en negro.
- Se acordó cerrar la fase con la rama `bloque-b-estetica` en lugar de una rama `fase-1-…`.
- La rama se une a `main`.

**Terminada cuando:**
- todas las pruebas pasan (248 del backend);
- el usuario aprueba el PDF;
- la rama está unida a `main`.

---

## Fase 2: herramientas de calidad

**Qué se hace:**

1. **Prettier (frontend)** se encarga del formato.
   - Se instala como dependencia de desarrollo en `frontend/`.
   - `frontend/.prettierrc` conserva el estilo actual para que el primer formateo cambie lo menos posible: comillas simples, punto y coma, 2 espacios y líneas de hasta 120 caracteres.
   - `frontend/.prettierignore` deja fuera `dist/` y `node_modules/`.
   - Scripts `npm run format` (aplica el formato) y `npm run format:check` (solo revisa).
2. **ESLint (frontend)** se encarga de los errores y las malas prácticas, no del formato.
   - ESLint 9 con configuración plana (`frontend/eslint.config.js`).
   - Reglas recomendadas de JavaScript, `eslint-plugin-react`, `eslint-plugin-react-hooks` (dependencias de `useEffect`, reglas de los hooks) y globales de Vitest en los archivos `*.test.jsx`.
   - **`eslint-config-prettier` al final**, para apagar las reglas de estilo que chocarían con Prettier.
   - Script `npm run lint`.
3. **Ruff (backend)** hace de formateador y de linter.
   - Se instala en un `backend/requirements-dev.txt` nuevo, para que no entre en las dependencias de producción.
   - Configuración en `backend/ruff.toml`:
     - líneas de hasta 120 caracteres y comillas simples, como el código actual;
     - reglas `E`, `W`, `F` (errores), `I` (orden de imports), `B` (errores probables) y `DJ` (buenas prácticas de Django);
     - las migraciones quedan fuera, porque son código generado y ya aplicado.
   - Comandos: `ruff format`, `ruff format --check` y `ruff check`.
4. **Comando único:**
   - `npm run check` en la raíz corre las cuatro comprobaciones (formato y linter de cada lado).
   - `scripts/entorno.mjs` no cambia: las comprobaciones no bloquean `npm run dev`.

**Orden de los commits** (el formateo no se mezcla con nada más):
1. Instalación y configuración de las herramientas, sin tocar el código.
2. **Solo el formateo automático** (`prettier --write` y `ruff format`). No cambia el comportamiento, y las pruebas siguen pasando sin modificarlas. Su hash se agrega a `.git-blame-ignore-revs`, para que `git blame` lo salte.
3. **Arreglos de lo que señalen los linters.**
   - Primero se presenta la lista al usuario, agrupada por tipo: imports sin usar, dependencias de hooks, variables sin usar, etc.
   - Si algún arreglo cambia el comportamiento (por ejemplo, agregar una dependencia a un `useEffect`), se explica aparte, con una prueba cuando aplique.
   - Una regla se puede desactivar solo con su motivo escrito en la configuración.

**Archivos:**
- Configuración nueva: `frontend/package.json` y `package-lock.json`, `frontend/.prettierrc`, `frontend/.prettierignore`, `frontend/eslint.config.js`, `backend/requirements-dev.txt`, `backend/ruff.toml`, `.git-blame-ignore-revs` y `package.json` de la raíz (script `check`).
- Código formateado: todo `frontend/src/` y todo `backend/` salvo las migraciones.
- Documentación:
  - README: "Pruebas", "Comandos" y la estructura de carpetas;
  - `CLAUDE.md`: hoy dice "No hay linter configurado";
  - `CHANGELOG.md` y `docs/progreso.md`.

**Terminada cuando:**
- `npm run check` termina sin errores;
- `npm run format:check` y `npm run lint` (frontend) y `ruff format --check .` y `ruff check .` (backend) dan 0 errores;
- todas las pruebas siguen pasando;
- el README y `CLAUDE.md` explican cómo usar las herramientas.

---

## Fase 3: auditoría OWASP Top 10:2025

**Qué se hace:** un informe de seguridad en `docs/auditoria-owasp.md`. **No se toca código.**

Para cada una de las 10 categorías se escribe:
- **qué aplica a PathoLab;**
- **qué ya está protegido**, con referencia a los hallazgos de `docs/auditoria-inicial.md` (C-x, I-x, M-x) y a las decisiones de `docs/decisiones.md` (D-x);
- **qué falta**, con un identificador (`O-1`, `O-2`…), dónde está (archivo y línea), cómo se reproduce cuando aplique, la corrección propuesta y su **prioridad** (alta, media o baja, con la justificación).

Las categorías de la edición 2025:

| Código | Categoría | Ejemplos de qué se revisa en PathoLab |
|---|---|---|
| A01 | Control de acceso roto | Permisos por rol, D-2, D-3, D-11 y D-12, acceso a `/media/` del foro, el historial del paciente |
| A02 | Configuración de seguridad incorrecta | `DEBUG`, CORS, cabeceras HTTPS y HSTS, `/admin/`, `manage.py check --deploy` |
| A03 | Fallos en la cadena de suministro de software | Dependencias de npm (frontend y raíz) y **de Python**; `requirements.txt` sin versiones fijas (no hay archivo de bloqueo) |
| A04 | Fallos criptográficos | JWT (algoritmo, duración, rotación de D-6), `SECRET_KEY`, HTTPS, contraseñas |
| A05 | Inyección | ORM y consultas, `texto_seguro()` en el PDF (I-3), XSS en React, subida de imágenes (I-6) |
| A06 | Diseño inseguro | Límites de peticiones, datos sensibles (Ley 1581), conflicto de edición entre pestañas |
| A07 | Fallos de autenticación | Login, throttles, validadores de contraseña (I-11), cierre de sesión (D-6), tokens en `localStorage` |
| A08 | Fallos de integridad de software o datos | Datos congelados (D-10), adendas (D-9), número de petición (D-7) |
| A09 | Fallos en el registro y las alertas de seguridad | Registro de accesos (pendiente en `progreso.md`), qué se registra hoy |
| A10 | Mal manejo de condiciones excepcionales | Errores 500, mensajes que revelan detalles internos, comportamiento ante fallos |

**Puntos ya conocidos que el informe debe evaluar** (salen del inventario del 2026-10-08):
- **I-9c:** 2 vulnerabilidades moderadas de `react-router` 6, que solo se cierran con React Router 7 (`docs/auditoria-inicial.md`, I-9; `CHANGELOG.md`, I-9a).
  - El análisis de I-9a dice que GHSA-337j-9hxr-rhxg no afecta porque "PathoLab usa `BrowserRouter` sin SSR".
  - Desde D-13, `App.jsx` usa `createBrowserRouter`, justo la API que nombra el aviso.
  - La conclusión (no hay SSR) probablemente sigue siendo válida, pero hay que volver a comprobarla.
- **Avisos nuevos de `npm audit` (2026-10-08), que no existían en I-9:**
  - **Crítico:** `shell-quote` 1.9.0, que usa `concurrently` 10.0.5 en la raíz (solo para `npm run dev`).
  - **Alto:** `source-map-js` 1.2.1, que usa Vite a través de PostCSS en el frontend (solo en desarrollo).
  - Los dos tienen arreglo sin cambio de versión principal (`npm audit fix`).
- **`requirements.txt` con rangos de versiones** (`Django>=4.2,<5.0`…) y sin archivo de bloqueo (A03).
- **Edición de informes finalizados en `/admin/`** (A01/A08).
  - D-3 permite "una corrección excepcional" desde `/admin/`.
  - `InformeAdmin` deja cambiar el contenido, los diagnósticos y hasta el `estado` de un informe finalizado, sin dejar rastro.
  - Esto choca con D-9 (las correcciones se hacen con adendas) y con el README ("un informe finalizado no se modifica").
  - **Necesita una decisión del usuario.**
- **Conflicto entre pestañas** (D-13): gana el último guardado, sin aviso (A06/A08). Propuesta anotada: comparar `fecha_actualizacion` y responder 409.
- **Registro de accesos:** no se registra quién consulta qué informe o paciente (A09).
- **Clave antigua en el historial de git** (C-3): cualquier servidor que la haya usado debe cambiarla (A04).
- **Datos del paciente en la dirección** (`GET /api/pacientes/?q=`), aprobado en la etapa 3 con la condición de configurar los registros del servidor web (A02).
- **Tokens en `localStorage`** (A07): conviene evaluar el riesgo frente a XSS.

**Dependencias:**
- **npm:** `npm audit` en `frontend/` y en la raíz.
- **Python:**
  - `pip-audit` sobre `backend/requirements.txt` y sobre lo que está instalado en el venv.
  - Se ejecuta de forma temporal (por ejemplo, `pip install pip-audit` en el venv, sin agregarlo a los requisitos), porque esta fase no cambia archivos del proyecto.
  - Si conviene dejarlo como herramienta, se propone como corrección en la fase 4.
- Para cada vulnerabilidad: paquete, versión, gravedad, si afecta a PathoLab y por qué.

**Archivos:** `docs/auditoria-owasp.md` (nuevo), `docs/progreso.md`, `CHANGELOG.md` (solo una entrada que diga que se agregó el informe) y README (enlace al informe en "Seguridad").

**Terminada cuando:**
- el informe cubre las 10 categorías y las dependencias de los dos lados;
- cada hallazgo tiene identificador, prioridad y corrección propuesta;
- el usuario lo leyó y dijo cuáles se corrigen en la fase 4.

---

## Fase 4: correcciones de seguridad

**Abierta.** Se define cuando el usuario revise el informe de la fase 3: qué hallazgos se corrigen, en qué orden y si van en una o en varias ramas.

Cada corrección sigue el procedimiento común:
- una prueba que demuestre el fallo;
- la explicación del arreglo y la confirmación del usuario;
- el arreglo;
- la documentación.

Al cerrar cada corrección, se actualiza en `docs/auditoria-owasp.md` el estado del hallazgo.

**Terminada cuando:** los hallazgos que eligió el usuario están corregidos, probados y marcados en el informe. Los que no se corrigen quedan anotados con su motivo.

---

## Fase 5: guía de diseño

**Qué se hace:** con la skill `frontend-design`, una guía escrita en `docs/guia-diseno.md` para que la interfaz tenga un aspecto sobrio, profesional y clínico. **No se cambian pantallas en esta fase.**

La guía define:
- **Colores:**
  - paleta con nombre y uso de cada color (texto, fondos, bordes, acción principal, peligro, éxito);
  - colores de los estados del informe (borrador, finalizado) y de las alertas;
  - contraste mínimo WCAG AA, comprobado.
- **Tipografía:**
  - familias, tamaños, pesos e interlineado de títulos, texto, etiquetas, tablas y números;
  - cómo se cargan las fuentes. Se propone instalarlas en el proyecto (por ejemplo, con `@fontsource`) en lugar de pedirlas a Google Fonts, para no enviar datos de los usuarios a terceros.
- **Bordes rectos:** `border-radius: 0` en todo; grosor y color de los bordes.
- **Espaciados:** una escala única (por ejemplo, 4, 8, 12, 16, 24, 32 px) y el ancho máximo del contenido.
- **Componentes:** botones (principal, secundario, peligro), campos de formulario, tablas, tarjetas o secciones, etiquetas de estado, avisos, ventanas modales, menú de navegación y pie de página.
- **Estados:** foco visible con el teclado, error, deshabilitado y carga.
- **Pantallas angostas:** comportamiento hasta 480 px.
- **Cómo se implementa:**
  - variables CSS (`--color-…`, `--espacio-…`) en `frontend/src/index.css`;
  - sigue sin librería de UI.
- **Ejemplo visual:** si el usuario lo pide, una página de muestra (HTML estático) con la paleta y los componentes, para verla antes de aprobar.

**Archivos:** `docs/guia-diseno.md` (nuevo), `docs/progreso.md` y `CHANGELOG.md`. Al aprobarse, una decisión nueva en `docs/decisiones.md` (D-14: la guía es la referencia de diseño).

**Terminada cuando:**
- **la aprueban el usuario, el equipo y el profesor** (con los cambios que pidan);
- queda registrada como decisión.

Mientras falte alguna de esas aprobaciones, la fase sigue abierta y `docs/progreso.md` dice de quién falta.

---

## Fase 6: pantalla de muestra (informe)

**Qué se hace:** se aplica la guía **solo** a la pantalla del informe, la más completa del sistema.

Comprende:
- `InformePage`;
- las tarjetas de `components/informe/`: `SelectorPaciente`, `DatosSolicitud`, `ListaDiagnosticos`, `SeccionFirma` y `SeccionAdendas`;
- el formulario de paciente que se abre desde ella (`FormularioPaciente`);
- el aviso de cambios sin guardar (D-13).

**Cómo se evita cambiar las demás pantallas:**
- Las variables de la guía se agregan a `index.css`.
- Los estilos nuevos se aplican dentro de una clase contenedora de la pantalla del informe (por ejemplo, `.diseno-v2`).
- `Navbar`, `Footer` y las demás pantallas se ven como antes hasta la fase 7.

**Pruebas:**
- El comportamiento no cambia, así que las pruebas actuales deben pasar sin modificarlas.
- Si una prueba busca una clase CSS que cambia de nombre, se ajusta y se explica.
- jsdom no calcula colores ni tamaños: el aspecto se comprueba a mano.

**Archivos:** `frontend/src/index.css`, `frontend/src/pages/InformePage.jsx`, `frontend/src/components/informe/*.jsx`, `frontend/src/components/FormularioPaciente.jsx`, `CHANGELOG.md` y `docs/progreso.md`.

**Terminada cuando:**
- **la aprueban el usuario, el equipo y el profesor**, después de revisar la pantalla del informe en el navegador: borrador, finalizado con adendas, informe nuevo y ventana angosta;
- todas las pruebas pasan.

Mientras falte alguna aprobación, la fase sigue abierta y `docs/progreso.md` dice de quién falta. La fase 7 no empieza antes.

---

## Fase 7: resto de pantallas

**Origen:** Bloque B, punto 5 de `docs/progreso.md`.

**Qué se hace:** se aplica la guía a todo lo demás:
- `Navbar`, `Footer`, `LoginPage` y `CerrarSesionPage`;
- `DashboardPage`, `BuscarPage` y `PacientesPage`;
- `PatologiasPage` y `CatalogosPage`;
- `ForoPage`, `PublicacionDetallePage` y `VisorImagenes`;
- `PerfilPage`, `PoliticaPrivacidadPage` y `TerminosCondicionesPage`;
- `EstadoBadge` y `CeldaPaciente`.

Al final se quita la clase contenedora de la fase 6 y se **borran los estilos viejos** de `index.css`. Hoy tiene 21 `border-radius`.

Se hace por grupos de pantallas, con un commit por grupo, para revisar de a poco:
1. navegación y login;
2. listados;
3. administración (Patologías y Catálogos);
4. foro;
5. perfil y páginas legales.

**Archivos:** `frontend/src/index.css`, `frontend/src/pages/*.jsx`, `frontend/src/components/*.jsx`, `CHANGELOG.md`, `docs/progreso.md` y el README si describe el aspecto de la interfaz.

**Terminada cuando:**
- todas las pantallas siguen la guía;
- `index.css` no tiene estilos viejos sin uso ni `border-radius` distintos de 0;
- todas las pruebas pasan;
- el usuario revisó cada grupo en el navegador, también en ventana angosta.

---

## Fase 8: cierre

**Qué se hace:**

1. **Revisión completa del README contra el código actual:**
   - usuarios de prueba (con `patologo2`);
   - funcionalidades;
   - todos los endpoints de la API, comparados con `config/urls.py` y los `urls.py` de cada app;
   - comandos (incluidos los de la fase 2);
   - estructura de carpetas, comparada con el árbol real;
   - pruebas: cantidad por lado y cómo correrlas;
   - seguridad (con lo de las fases 3 y 4) y hoja de ruta.
2. **Revisión del resto de la documentación:**
   - `CLAUDE.md`, `docs/decisiones.md`, `docs/auditoria-inicial.md` y `docs/auditoria-owasp.md` (estado de cada hallazgo);
   - `docs/propuesta-informe-v2.md` y `docs/guia-diseno.md`;
   - la colección de Postman (`PathoLab_API.postman_collection.json`), con las peticiones probadas.
3. **Prueba manual completa**, hecha por el usuario con una lista de comprobación escrita en `docs/progreso.md`:
   - los 4 usuarios de prueba (`admin`, `patologo1`, `patologo2` y `auditor1`);
   - todas las pantallas y el flujo completo: paciente, informe, finalizar, PDF, adenda, foro y catálogos;
   - que `patologo2` no pueda modificar los informes de `patologo1`;
   - el aviso de cambios sin guardar;
   - ventana angosta.
4. Unión a `main` y cierre del plan: en este documento, el estado pasa a "terminado".

**Contradicciones y textos desactualizados ya detectados** (inventario del 2026-10-08), que se corrigen aquí si no se corrigieron antes:
- `CLAUDE.md`:
  - dice "Los hallazgos pendientes de corregir están en `docs/auditoria-inicial.md`", pero de esa auditoría solo queda I-9c;
  - dice "No hay linter configurado" (lo cambia la fase 2).
- `docs/auditoria-inicial.md`:
  - I-13 (no hay pruebas) no tiene línea de estado, aunque hoy hay casi 400 pruebas;
  - el estado de I-7 dice que falta corregir el README, y ya se corrigió en I-12;
  - la tabla de la sección 5 conserva los ❌ de la auditoría, sin decir que ya se corrigieron.
- `docs/propuesta-informe-v2.md`:
  - el "Estado" del encabezado dice que se terminaron las etapas 1 a 7, pero también están hechas la 8 y la 9;
  - la sección 8 nombra solo el registro de prueba de `patologo1`;
  - la sección 8 dice que nunca se ponen datos del paciente en una URL, pero la búsqueda `?q=` de pacientes sí los lleva (aprobado en la etapa 3, con la nota de producción).
- `CHANGELOG.md` (I-9a): el análisis de GHSA-337j menciona `BrowserRouter`. No se reescribe el historial: se agrega una entrada nueva con el análisis revisado (fase 3).
- `README.md`:
  - la tabla "Documentación del Proyecto" no incluye `docs/plan-calidad-y-diseno.md`;
  - "Pruebas Automáticas" (frontend) no menciona el aviso de cambios sin guardar, el autoguardado, `/salir` ni el visor de imágenes.
- `docs/decisiones.md`: según lo que decida el usuario sobre `/admin/` (fase 3), una decisión nueva que precise D-3.

**Archivos:** `README.md`, `CLAUDE.md`, `docs/*.md`, `PathoLab_API.postman_collection.json`, `CHANGELOG.md` y `docs/progreso.md`.

**Terminada cuando:**
- no quedan diferencias entre la documentación y el código;
- la prueba manual sale bien (o sus hallazgos quedan corregidos o anotados);
- todo está en `main`.

---

## Respuestas del usuario (2026-10-08)

1. **Plan:** aprobado. Las fases 5 y 6 quedan terminadas solo cuando las aprueban el usuario, el equipo y el profesor.
2. **Tarea previa:** sí. `patologo2` / `patologo2345`, registro `RM-PRUEBA-0002`, entre la fase 1 y la fase 2.
3. **Fase 1:** se cierra con la rama `bloque-b-estetica`. El usuario confirmó que el PDF se ve bien, en negro.
