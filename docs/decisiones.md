# Decisiones del proyecto

Aquí se registran las decisiones de diseño y de reglas de negocio ya tomadas. El código y la documentación deben respetarlas. Para cambiar una decisión, se agrega una entrada nueva que la reemplace; no se borra la anterior.

Los códigos como "I-7" o "C-2" remiten a `docs/auditoria-inicial.md`.

---

## D-1. Los patólogos pueden administrar el catálogo

- **Fecha:** 2026-10-03
- **Hallazgo relacionado:** I-7
- **Decisión:** los usuarios con rol **patólogo** pueden crear, editar y borrar **patologías, plantillas, categorías y temas del foro**, igual que el administrador. El auditor sigue teniendo solo lectura. Los permisos del código (`EsPatologoOAdmin`) no cambian. Lo que se corrige es el README, que decía que esa gestión era solo del administrador.
- **Motivo:** criterio del profesor.

## D-2. Solo el autor o un administrador puede editar, borrar o finalizar un informe

- **Fecha:** 2026-10-03
- **Hallazgo relacionado:** C-2 (punto 3)
- **Decisión:** un informe solo lo puede **editar, borrar o finalizar** su **autor** o un **administrador**. Un patólogo **no** puede finalizar, editar ni borrar informes de otro patólogo, aunque sí puede verlos. El auditor sigue teniendo solo lectura.
- **Motivo:** cada informe tiene un patólogo responsable. Si otro patólogo pudiera modificarlo o cerrarlo, se perdería la trazabilidad de quién hizo qué en un documento clínico.

## D-3. Un informe finalizado no se puede modificar, ni siquiera por un administrador

- **Fecha:** 2026-10-03
- **Hallazgo relacionado:** C-2 (punto 1)
- **Decisión:** cuando un informe está **finalizado**, la API rechaza (400) cualquier intento de editarlo o borrarlo, **también si lo hace un administrador**. Si hiciera falta una corrección excepcional, un administrador puede hacerla desde el panel `/admin/` de Django, que queda fuera de esta regla.
- **Motivo:** el README establece que finalizar un informe "bloquea la edición". Un documento clínico cerrado no debe cambiar desde la aplicación.

## D-4. Las patologías se pueden desactivar en lugar de borrarse

- **Fecha:** 2026-10-03
- **Hallazgo relacionado:** M-5 (y la idea que quedó pendiente en I-1)
- **Decisión:** el selector de "Nuevo informe" muestra solo las patologías **activas**. Al editar un informe existente se sigue viendo su patología aunque esté inactiva. El formulario de la pantalla Patologías tiene una casilla **"Activa"** para activarlas o desactivarlas.
- **Motivo:** una patología con informes no se puede borrar (I-1). Desactivarla permite retirarla del uso sin perder el historial.

## D-5. El foro trae temas iniciales y se pueden crear desde la aplicación

- **Fecha:** 2026-10-03
- **Hallazgo relacionado:** M-6
- **Decisión:** `seed_data` crea 4 temas iniciales: *Casos clínicos*, *Técnicas de laboratorio*, *Investigación* y *Dudas y consultas*. El foro tiene un botón **"+ Tema"** para patólogos y administradores, como permite D-1.
- **Motivo:** el foro empezaba sin temas y solo se podían crear desde `/admin/`.

## D-6. Cerrar sesión o cambiar la contraseña invalida el token de renovación

- **Fecha:** 2026-10-03
- **Hallazgo relacionado:** M-11
- **Decisión:** se activa la lista negra de tokens de SimpleJWT (`token_blacklist`). Al cerrar sesión (nuevo endpoint `POST /api/auth/logout/`) y al cambiar la contraseña, el token de renovación queda invalidado. El token de acceso sigue siendo válido hasta que vence (máximo 8 horas), que es una limitación normal de JWT.
- **Motivo:** hasta ahora, cerrar sesión solo borraba los tokens del navegador. Un token robado seguía sirviendo hasta 7 días.
