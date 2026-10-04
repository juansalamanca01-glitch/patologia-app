# Estado del trabajo

Este archivo dice **en qué quedamos**. Se actualiza al terminar cada tarea para poder retomar el trabajo si la conversación se corta.
- **Qué se cambió y por qué:** `CHANGELOG.md`.
- **Decisiones tomadas:** `docs/decisiones.md`.
- **Lista completa de problemas:** `docs/auditoria-inicial.md`.

**Última actualización:** 2026-10-03

---

## Dónde estamos

- **Rama de trabajo:** `seguridad-critica`, subida a GitHub. Se unió a `main` el 2026-10-03 en dos ocasiones: hasta `958c2f0` (C-1, C-2, C-3, I-1, I-3, I-4, M-8) y luego hasta `da69796` (I-5, I-6, I-8, I-11, I-9a, I-9b). Se hizo con fast-forward desde la terminal, sin pull request, porque `gh` no está instalado. El 2026-10-03 también se unió hasta `0d94a56` (I-10, I-12, I-2). El trabajo sigue en esta rama y se volverá a unir a `main` cuando el usuario lo pida.
- **Tarea actual:** corregir los hallazgos de la auditoría, empezando por los críticos.
- **Forma de trabajar con cada hallazgo** (ver las reglas en `CLAUDE.md`):
  1. Escribir una prueba que demuestre el fallo y mostrar que falla.
  2. Explicar el arreglo y esperar confirmación.
  3. Aplicar el arreglo y mostrar que la prueba pasa.
  4. Registrar el cambio en `CHANGELOG.md`, actualizar la documentación y hacer commit.
  5. Hacer `git push` a `seguridad-critica` después de cada commit, como respaldo. El usuario lo autorizó el 2026-10-03. Unir la rama a `main` requiere preguntar aparte.
- **Pruebas:** 57 del backend (`cd backend` y luego `python manage.py test`) y 14 del frontend (`cd frontend` y luego `npm test`). Todas pasan.

## Hecho

| Hallazgo | Qué se hizo | Commit |
|---|---|---|
| — | Auditoría inicial (`docs/auditoria-inicial.md`) | `bf42ff9` |
| C-1 | Un usuario ya no puede cambiarse el rol, `activo` ni `username` | `bf42ff9` |
| I-7 | Resuelto por decisión D-1 (los patólogos sí administran el catálogo) | `945affb` |
| C-2 | Informes finalizados bloqueados; solo el autor o un admin los modifica (D-2, D-3) | `e56174d` |
| C-3 | `SECRET_KEY` obligatoria, `DEBUG=False` por defecto; el script crea el `.env` | `455cff0` |
| — | Borrada la clase `EsSoloLectura`, que ya no se usaba | `455cff0` |
| I-1 | Borrar una patología con informes responde 400 en vez de un error 500 | `bd35f2f` |
| I-3 | El PDF escapa el texto del usuario (sin error 500 ni etiquetas inyectadas) y respeta los saltos de línea | `8ebf17b` |
| I-4 | Endpoint `/api/informes/estadisticas/` para el dashboard y paginación en el buscador | `4938f2d` |
| M-8 | El perfil muestra un error con "Reintentar" en lugar de quedar en blanco; se instala Vitest en el frontend | `958c2f0` |
| I-5 | PDF descargado con Axios (token en la cabecera); se eliminó `/api/descargar-pdf/?token=` | `7886e0c` |
| I-6 | Límite real de 10 MB y validación de que el archivo sea una imagen (backend); revisión previa y sin publicaciones duplicadas (frontend) | `2bf50e6` |
| I-8 | Foro: solo un admin fija publicaciones; un comentario no se puede mover a otra publicación | `8c8dac3` |
| I-11 | El registro y el cambio de contraseña aplican los validadores de Django | `3d5e5cf` |
| I-9a | `npm audit fix`: producción pasa de 6 vulnerabilidades (2 altas) a 2 moderadas que no afectan a la app | `ee92a38` |
| I-9b | Vite 5 → 6.4 y Vitest 3 → 5: quedan solo las 2 vulnerabilidades moderadas de react-router | `da69796` |
| I-10 | `client.js` usa `VITE_API_URL` (vacía en desarrollo → proxy de Vite) en lugar de `localhost:8000` fijo | `1a1822e` |
| I-12 | README reescrito (permisos, API completa, pruebas, seguridad) y colección de Postman rehecha y probada | `e3743c2` |
| I-2 | Los campos obligatorios se validan aunque `datos_ingresados` llegue vacío; `0` y `false` cuentan como respuesta | `0d94a56` |
| M-1, M-2 | Limpieza: imports, `LoginSerializer`, campo `campos_requeridos` (migración 0003), `isPatologo`/`isAuditor`, `console.log`, imágenes sobrantes y `dist/` | ver `git log` |

## Siguiente paso

Seguir el orden sugerido en la sección 7 de la auditoría:
1. **Limpieza** (en 3 grupos, cada uno con su lista exacta y confirmación del usuario):
   - Grupo 1, código y archivos sin usar (M-1, M-2): **hecho**.
   - Grupo 2, código duplicado y comentarios (M-3, M-13): siguiente.
   - Grupo 3, comportamiento (M-4 a M-12; M-5 ampliado, ver abajo).
2. **Opcional, al final (I-9c):** React Router 6 → 7 para cerrar las 2 vulnerabilidades moderadas que quedan. Hoy no afectan a la app (ver CHANGELOG, I-9a). Es un cambio de versión principal que obliga a revisar la navegación de todas las páginas.

Para volver a unir la rama a `main`: comprobar que todas las pruebas pasan, ejecutar `git switch main`, luego `git merge --ff-only seguridad-critica` y `git push origin main`, y volver con `git switch seguridad-critica`. Siempre preguntar antes al usuario.

## Pendiente de respuesta del usuario

- Nada por ahora.

## Pendiente de hacer (anotado para no olvidarlo)

- **M-5 (ampliado):** además de filtrar las patologías inactivas en "Nuevo informe", añadir el campo "activa" al formulario de patologías de `PatologiasPage.jsx`. Así se puede desactivar una patología con informes en lugar de borrarla (relacionado con I-1).
- **Producción:** al publicar la app, configurar en el servidor web un límite de tamaño de petición (por ejemplo, `client_max_body_size 60m;` en Nginx). Ver la nota de I-6 en `settings.py`.
- **Navegador:** probar a mano el dashboard y la paginación del buscador (I-4) con más de 20 informes.
- **Navegador:** probar a mano el cambio de C-2 en el frontend. Otro patólogo debe ver en solo lectura los informes ajenos. Para la prueba hay que crear un segundo patólogo desde `/admin/`.
