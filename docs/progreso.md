# Estado del trabajo

Este archivo dice **en qué quedamos**. Se actualiza al terminar cada tarea para poder retomar el trabajo si la conversación se corta.
- **Qué se cambió y por qué:** `CHANGELOG.md`.
- **Decisiones tomadas:** `docs/decisiones.md`.
- **Lista completa de problemas:** `docs/auditoria-inicial.md`.

**Última actualización:** 2026-10-03

---

## Dónde estamos

- **Rama de trabajo:** `seguridad-critica`. Está subida a GitHub (`origin/seguridad-critica`) pero **no** se ha unido a `main`.
- **Tarea actual:** corregir los hallazgos de la auditoría, empezando por los críticos.
- **Forma de trabajar con cada hallazgo** (ver las reglas en `CLAUDE.md`):
  1. Escribir una prueba que demuestre el fallo y mostrar que falla.
  2. Explicar el arreglo y esperar confirmación.
  3. Aplicar el arreglo y mostrar que la prueba pasa.
  4. Registrar el cambio en `CHANGELOG.md`, actualizar la documentación y hacer commit.
  5. Hacer `git push` a `seguridad-critica` después de cada commit, como respaldo. El usuario lo autorizó el 2026-10-03. Unir la rama a `main` requiere preguntar aparte.
- **Pruebas:** 25 en total (`cd backend` y luego `python manage.py test`). Todas pasan.

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
| I-3 | El PDF escapa el texto del usuario (sin error 500 ni etiquetas inyectadas) y respeta los saltos de línea | ver `git log` |

## Siguiente paso

Seguir con los hallazgos **importantes**, en el orden sugerido en la sección 7 de la auditoría:
- I-4: el dashboard y el buscador solo ven 20 informes.
- M-8: la página de perfil se rompe si falla la carga.

Más adelante hay que decidir cuándo unir `seguridad-critica` a `main` (con un pull request en GitHub o con `git merge`).

## Pendiente de respuesta del usuario

- Nada por ahora.

## Pendiente de hacer (anotado para no olvidarlo)

- **README:** corregir que el administrador no es el único que gestiona el catálogo (decisión D-1). Se hará junto con I-12 (reescribir el README, que tiene 15 líneas con caracteres de control dañados).
- **M-5 (ampliado):** además de filtrar las patologías inactivas en "Nuevo informe", añadir el campo "activa" al formulario de patologías de `PatologiasPage.jsx`. Así se puede desactivar una patología con informes en lugar de borrarla (relacionado con I-1).
- **Navegador:** probar a mano el cambio de C-2 en el frontend. Otro patólogo debe ver en solo lectura los informes ajenos. Para la prueba hay que crear un segundo patólogo desde `/admin/`.
