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

## D-7. El número de petición lo genera el sistema y reemplaza al número de caso

- **Fecha:** 2026-10-04
- **Relacionado con:** `docs/propuesta-informe-v2.md` (secciones 3.5 y 10, respuestas P-1 y P-2)
- **Decisión:** al crear un informe, el sistema le asigna un **número de petición** con el formato `P-AÑO-NNNNN` (por ejemplo `P-2026-00045`): 5 cifras con ceros a la izquierda y el consecutivo vuelve a 1 cada año. El año es el de la fecha de creación en la hora de Bogotá. El número es único aunque dos usuarios creen informes al mismo tiempo, no se puede modificar y **nunca se reutiliza**: si se borra un borrador, su número queda sin usar. El campo `numero_caso`, que escribía el usuario, **se elimina**. Se agrega un campo opcional, `numero_orden_externa`, para el número de orden de la institución remitente; ese campo no es único.
- **Motivo:** el número escrito a mano permitía errores y obligaba a inventar un consecutivo. En un documento clínico, un mismo número no debe apuntar nunca a dos informes distintos.

## D-8. Firma del patólogo y requisitos para finalizar un informe

- **Fecha:** 2026-10-04
- **Relacionado con:** `docs/propuesta-informe-v2.md` (secciones 3.7 y 3.9, respuestas P-6 y P-7)
- **Decisión:**
  - El **registro médico** del usuario solo lo asigna un **administrador**, al crear el usuario o desde `/admin/`. En el perfil es de solo lectura, como el rol (C-1).
  - La firma del informe es siempre la de su **autor**, aunque lo finalice un administrador (D-2).
  - Para finalizar un informe:
    - el autor debe tener registro médico;
    - el informe debe tener **al menos un diagnóstico**;
    - si el tipo de estudio es **histología**, la **descripción microscópica** no puede estar vacía. En los demás tipos de estudio es opcional.
  - Un borrador se puede guardar sin cumplir estos requisitos.
- **Motivo:** si cualquiera pudiera escribir un registro médico, podría firmar informes clínicos con un registro falso. Un informe sin diagnóstico no está completo. En estudios como la citología, la descripción microscópica no siempre va separada.

## D-9. Un informe finalizado se corrige con adendas

- **Fecha:** 2026-10-04
- **Relacionado con:** D-3; `docs/propuesta-informe-v2.md` (sección 3.8)
- **Decisión:**
  - Un informe finalizado se corrige agregando una **adenda**: un texto nuevo con motivo, fecha, número consecutivo dentro del informe y firma de quien la crea.
  - **Contenido original:** la adenda **no modifica** el informe, así que D-3 sigue vigente.
  - **Cuándo y quién:** las adendas solo se crean en informes finalizados (un borrador se corrige editándolo). Las crea el autor del informe o un administrador (D-2), y quien la crea debe tener registro médico.
  - **No se modifican:** no se editan ni se borran desde la aplicación, y en `/admin/` son de solo lectura.
  - **En el PDF:** van al final, y al principio del informe aparece un aviso de que existen.
- **Motivo:** D-3 impide corregir un informe cerrado desde la aplicación. Las adendas permiten corregirlo sin perder lo que se entregó originalmente y dejan constancia de quién corrigió qué y cuándo.

## D-10. Al finalizar un informe se congelan los datos que imprime

- **Fecha:** 2026-10-04
- **Relacionado con:** D-3; `docs/propuesta-informe-v2.md` (sección 3.7)
- **Decisión:** al finalizar, se guardan en el informe (`datos_finalizacion`) los datos del paciente (nombre, documento, fecha de nacimiento y sexo), los nombres de la EPS y del servicio, y la firma del autor (nombre, especialidad y registro médico). Desde ese momento, la API y el PDF de ese informe usan estos datos y no los actuales.
- **Motivo:** si se corrigiera después el nombre de un paciente o de un usuario, un informe ya entregado cambiaría sin dejar rastro. Es la misma idea de D-3 aplicada a los datos relacionados.

## D-11. Permisos sobre pacientes y sobre los catálogos de EPS y servicios

- **Fecha:** 2026-10-04
- **Relacionado con:** D-1, D-4; `docs/propuesta-informe-v2.md` (respuesta P-4)
- **Decisión:**
  - **Pacientes:** todos los usuarios autenticados ven los pacientes. Los crean y editan patólogos y administradores. **Solo un administrador** puede borrar un paciente, y solo si no tiene informes; si los tiene, la API responde 400.
  - **EPS y servicios:** los administran patólogos y administradores, igual que el catálogo de patologías (D-1). Se desactivan en lugar de borrarse (D-4).
  - **Auditor:** solo lee.
- **Motivo:** el patólogo es quien registra a los pacientes y conoce las EPS y los servicios con los que trabaja. Borrar un paciente es más delicado porque se pierde su identificación, por eso queda solo para el administrador.

## D-12. El PDF de un borrador es una vista previa solo para su autor o un administrador

- **Fecha:** 2026-10-05
- **Relacionado con:** D-2, D-3; `docs/propuesta-informe-v2.md` (sección 5.2)
- **Decisión:**
  - **Quién lo descarga:** el PDF de un informe en **borrador** solo lo descargan su **autor** o un **administrador**, como vista previa antes de finalizar. Los demás patólogos y el auditor reciben 403, y en la pantalla no ven el botón.
  - **Cómo se marca:** el borrador lleva en cada página una marca de agua grande en diagonal, "BORRADOR", además de lo que ya tenía desde la etapa 7: sin firma y con "BORRADOR — SIN VALIDEZ" en la fecha de informe y en el pie. El archivo se llama `informe_P-AAAA-NNNNN_borrador.pdf`, y el botón dice "Vista previa (borrador)".
  - **Informes finalizados:** su PDF lo siguen descargando todos los roles, sin marca de agua ni sufijo.
- **Motivo:** el usuario notó en la prueba manual que cualquiera podía descargar un borrador, y un PDF suelto puede imprimirse y circular aunque diga "sin validez" en letra pequeña. La vista previa se conserva porque al patólogo le sirve revisar el PDF antes de finalizar: después solo podría corregirlo con una adenda (D-9).

## D-13. Aviso al salir con cambios sin guardar y autoguardado de los borradores existentes

- **Fecha:** 2026-10-05
- **Relacionado con:** D-2, D-7; `docs/progreso.md` ("Pendientes", punto 3)
- **Decisión:**
  - **Aviso al salir:** en un informe que se puede editar (nuevo, o borrador del que se es autor o admin), si hay cambios sin guardar, salir de la pantalla pide confirmar. Esto vale para el menú, "Cancelar" o cualquier enlace interno. Las opciones son **Seguir editando**, **Salir sin guardar** y **Guardar y salir**. Si "Guardar y salir" falla por validación (por ejemplo, falta el paciente o un campo obligatorio), no se sale: la página se queda mostrando qué falta. Al cerrar la pestaña o recargar, el navegador muestra su propio aviso.
  - **Autoguardado:** solo en un **borrador que ya existe** y que el usuario puede editar. Se guarda en el servidor 5 segundos después del último cambio, y solo si pasa la validación del formulario. Un indicador muestra el estado: guardado y su hora, guardando, o cambios sin guardar y por qué.
  - **Informes nuevos:** no se autoguardan, porque cada informe creado gasta un número de petición (D-7). Solo llevan el aviso al salir.
  - **Navegador:** no se guarda ninguna copia en el navegador (`localStorage`, `sessionStorage` ni similares), porque serían datos de pacientes en el computador.
- **Motivo:** en la prueba manual del 2026-10-05 el usuario notó que al salir del formulario sin guardar se perdía todo lo escrito. Avisar cubre los informes nuevos sin gastar números de petición, y el autoguardado protege el trabajo largo sobre un borrador sin dejar datos sensibles en el equipo.

