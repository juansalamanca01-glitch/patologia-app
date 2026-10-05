# Propuesta: informe de anatomía patológica v2

**Fecha:** 2026-10-04
**Estado:** aprobada el 2026-10-04 con las respuestas del usuario (sección 10). Las decisiones D-7 a D-11 están en `docs/decisiones.md`. Se implementa por etapas (sección 9); las etapas 1 (número de petición), 2 (catálogos y opciones), 3 (pacientes), 4 (datos de la solicitud), 5 (contenido del informe) y 6 (firma y finalización) se terminaron el 2026-10-04.

**Objetivo:** que el informe tenga los datos y el orden de un informe real de laboratorio:

1. Encabezado con nombre del paciente, número de identificación, edad, médico tratante, fecha de ingreso, número de petición, sexo, EPS, servicio, fecha de informe y estudios solicitados.
2. Título "Informe de anatomía patológica" y tipo de estudio.
3. Descripción macroscópica, descripción microscópica, diagnósticos, comentarios y firma.

El formato real se usa como **referencia de estructura**. El PDF no copia el nombre, el logo ni los datos de ningún laboratorio real: el encabezado sale de la configuración (sección 5.1).

---

## 1. Qué hay hoy (revisión del código)

| Pieza | Archivo | Situación actual |
|---|---|---|
| Modelo | `backend/informes/models.py` | `Informe` tiene `numero_caso` (texto libre escrito por el usuario, único), `patologia`, `autor`, `fecha` (fecha de creación), `tipo_muestra`, `datos_ingresados` (JSON del formulario dinámico), `texto_generado` (macroscópica automática), `estado` y `notas`. No hay datos del paciente, descripción microscópica, diagnósticos ni firma. |
| Serializers | `backend/informes/serializers.py` | `InformeSerializer` valida los campos obligatorios de la plantilla (I-2). `InformeListSerializer` es la versión resumida. |
| Vistas | `backend/informes/views.py` | `perform_create` y `perform_update` regeneran `texto_generado`. `finalizar` cambia el estado. `exportar_pdf` usa `numero_caso` en el nombre del archivo. La búsqueda `q` filtra por `numero_caso`, patología y tipo de muestra. Se cumplen D-2 y D-3. |
| Usuario | `backend/accounts/models.py` | Tiene `nombre_completo` y `especialidad`, pero no registro médico. Solo un admin crea usuarios (`RegistroView`). `/perfil/` protege `rol`, `activo` y `username` (C-1). No hay endpoint para que un admin edite a otro usuario: se hace desde `/admin/`. |
| PDF | `backend/informes/utils.py` | Tiene el título "INFORME DE PATOLOGÍA CLÍNICA" y una tabla con caso, fecha, patología, muestra, patólogo y estado. Luego vienen "DATOS CLÍNICOS" (imprime `datos_ingresados` en bruto), "DESCRIPCIÓN MACROSCÓPICA" (`texto_generado`), "NOTAS ADICIONALES" y el pie con la fecha de generación. Todo el texto del usuario pasa por `texto_seguro()` (I-3). |
| Frontend | `frontend/src/pages/InformePage.jsx` | Tiene tres tarjetas: Datos generales (número de caso escrito a mano, patología, tipo de muestra), campos dinámicos ("Descripción macroscópica") y notas. Muestra el texto generado y ofrece finalizar y exportar el PDF. |
| Listados | `BuscarPage.jsx`, `DashboardPage.jsx` | Tienen columnas de número de caso, patología, tipo de muestra, autor y estado. |

**Problemas que la propuesta corrige de paso:**

- El número de caso a mano permite errores de digitación y obliga al usuario a inventar un consecutivo.
- La sección "Datos clínicos" del PDF repite lo que ya dice la macroscópica.
- Nada impide que un informe finalizado cambie si se corrigen los datos del usuario (su nombre, por ejemplo). Con la firma esto pasa a ser importante (sección 3.7).

---

## 2. Cada dato del informe real y dónde se guarda

| Dato del informe real | Dónde se guarda | Cómo se llena |
|---|---|---|
| Nombre del paciente | `Paciente.nombres` + `Paciente.apellidos` | Se escoge o se crea el paciente |
| Número de identificación | `Paciente.tipo_documento` + `Paciente.numero_documento` | Ídem |
| Edad | **No se guarda** | Se calcula de `Paciente.fecha_nacimiento` a la **fecha de ingreso** del informe |
| Sexo | `Paciente.sexo` (lista: Femenino, Masculino, Indeterminado) | Ídem |
| EPS | `Informe.eps` (catálogo), precargada con `Paciente.eps` | Lista |
| Médico tratante | `Informe.medico_tratante` (texto) | Texto libre |
| Fecha de ingreso | `Informe.fecha_ingreso` | Fecha; por defecto, hoy |
| Número de petición | `Informe.numero_peticion` | **Lo genera el sistema** al crear el informe |
| N.º de orden externo (nuevo) | `Informe.numero_orden_externa` | Opcional |
| Servicio | `Informe.servicio` (catálogo) | Lista |
| Fecha de informe | `Informe.fecha_informe` | **Automática** al finalizar |
| Estudios solicitados | `Informe.estudios_solicitados` (texto) | Lo que pidió el médico remitente |
| Tipo de estudio | `Informe.tipo_estudio` (lista) | Histología, citología, etc. |
| Descripción macroscópica | `Informe.texto_generado` (sin cambios) | Se genera con los campos dinámicos, como hoy |
| Descripción microscópica | `Informe.descripcion_microscopica` (nuevo) | Texto libre |
| Diagnósticos | Modelo `Diagnostico` (varios por informe) | Filas con descripción y CIE-10 opcional |
| Comentarios | `Informe.comentarios` (es el actual `notas`, renombrado) | Texto libre |
| Firma | `Usuario.registro_medico` + datos congelados al finalizar | Datos del autor |
| Adendas (nuevo) | Modelo `Adenda` | Solo en informes finalizados |

Se conservan `patologia` (de ella sale el formulario dinámico) y `tipo_muestra`.

---

## 3. Modelo de datos propuesto

### 3.1 Nueva app `pacientes`: modelos `Paciente` y `EPS`

El paciente va en una app propia (`backend/pacientes/`, rutas en `/api/pacientes/`). Así la app `informes` sigue dedicada a informes y catálogo de patologías. La EPS vive aquí porque es un dato del paciente.

```python
class EPS(models.Model):
    nombre = models.CharField(max_length=150, unique=True)
    activa = models.BooleanField(default=True)   # mismo criterio que D-4: se desactiva, no se borra

class Paciente(models.Model):
    class TipoDocumento(models.TextChoices):
        CC = 'CC', 'Cédula de ciudadanía'
        TI = 'TI', 'Tarjeta de identidad'
        RC = 'RC', 'Registro civil'
        CE = 'CE', 'Cédula de extranjería'
        PA = 'PA', 'Pasaporte'
        PPT = 'PPT', 'Permiso por protección temporal'
        MS = 'MS', 'Menor sin identificación'
        AS = 'AS', 'Adulto sin identificación'

    class Sexo(models.TextChoices):              # etiqueta "Sexo", como el formato real (P-3)
        FEMENINO = 'femenino', 'Femenino'
        MASCULINO = 'masculino', 'Masculino'
        INDETERMINADO = 'indeterminado', 'Indeterminado'

    tipo_documento = models.CharField(max_length=3, choices=TipoDocumento.choices)
    numero_documento = models.CharField(max_length=20)   # alfanumérico: los pasaportes llevan letras
    nombres = models.CharField(max_length=150)
    apellidos = models.CharField(max_length=150)
    fecha_nacimiento = models.DateField()
    sexo = models.CharField(max_length=13, choices=Sexo.choices)
    eps = models.ForeignKey(EPS, on_delete=models.PROTECT, null=True, blank=True)  # EPS actual
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [UniqueConstraint(fields=['tipo_documento', 'numero_documento'], name='paciente_documento_unico')]
```

- **Edad:** el método `edad_en(fecha)` devuelve la edad en años cumplidos. Para menores de 1 año la da en meses y para menores de 1 mes en días, como en patología pediátrica y placentaria. El informe muestra la edad **a la fecha de ingreso**, no la de hoy: si se reimprime un informe de hace tres años, la edad no debe cambiar. Nada de esto se guarda en la base de datos.
- **Validaciones:** la fecha de nacimiento no puede estar en el futuro ni ser de hace más de 130 años. `numero_documento` se guarda sin espacios ni puntos.
- **Datos mínimos:** solo se guarda lo que aparece en el informe. No se piden dirección, teléfono ni correo del paciente, porque son datos de salud, que son datos sensibles (Ley 1581 de 2012).
- **EPS del informe (confirmado en la etapa 4):** si un informe nuevo no envía `eps`, toma la EPS actual del paciente si sigue activa. La pantalla de EPS y servicios es `/catalogos`.
- **EPS desactivada (confirmado en la etapa 3):** no se puede asignar a un paciente, pero el paciente que ya la tenía la conserva, para poder corregir sus otros datos.
- **Un paciente puede tener varios informes:** `Informe.paciente` es una `ForeignKey` con `PROTECT`. Un paciente con informes no se puede borrar; la API responde 400, como en I-1.

### 3.2 Catálogo `Servicio` (app `informes`)

```python
class Servicio(models.Model):
    nombre = models.CharField(max_length=150, unique=True)
    activo = models.BooleanField(default=True)
```

`seed_data` carga: Consulta externa, Urgencias, Hospitalización, Cirugía, Unidad de cuidados intensivos, Ginecología y Dermatología.

### 3.3 Listas de opciones: cuáles son fijas y cuáles son catálogo

| Lista | Tipo | Motivo |
|---|---|---|
| Sexo, tipo de documento, tipo de estudio | `TextChoices` en el código | Son estables y la lógica puede depender de ellas |
| EPS, servicio | Tabla editable (catálogo) | Cambian según la institución y con el tiempo (las EPS se fusionan o se liquidan) |

**Tipo de estudio** (`Informe.TipoEstudio`): Histología (por defecto), Citología no ginecológica, Citología cérvico-vaginal, Inmunohistoquímica, Estudio intraoperatorio por congelación y Revisión de láminas (segunda opinión).

**Una sola fuente para las opciones fijas.** El endpoint nuevo `GET /api/opciones/` devuelve `{sexos, tipos_documento, tipos_estudio}` con `valor` y `etiqueta`, sacados de los `TextChoices`. El frontend no los copia en `constants.js`. Así se evita tener el mismo valor en dos sitios, como pasa con `FORO_MAX_TAMANO_IMAGEN`. Las EPS y los servicios se piden a sus endpoints (`/api/pacientes/eps/?activa=true` y `/api/servicios/?activo=true`) con `LISTA_COMPLETA`. Cada filtro se llama como su campo (ajuste de la etapa 2).

**Quién administra los catálogos de EPS y servicios:** patólogo o admin (`EsPatologoOAdmin`), lo mismo que D-1 establece para el catálogo de patologías. El auditor solo lee. Es una extensión de D-1, confirmada por el usuario (P-4, decisión D-11).

### 3.4 Cambios en `Informe`

| Campo | Tipo | Notas |
|---|---|---|
| `numero_peticion` | `CharField(20, unique=True)` | Lo genera el sistema (sección 3.5). Es de solo lectura en la API. |
| `numero_orden_externa` | `CharField(50, blank=True)` | Opcional. **No** es único: dos instituciones distintas pueden repetir números. |
| `paciente` | `FK(Paciente, PROTECT, null=True)` | `null` solo por los informes que ya existen. El serializer lo exige al crear. |
| `medico_tratante` | `CharField(200, blank=True)` | |
| `fecha_ingreso` | `DateField(null=True)` | Por defecto, la fecha local de hoy. No puede estar en el futuro ni ser anterior a la fecha de nacimiento. |
| `eps` | `FK(EPS, PROTECT, null=True, blank=True)` | La del momento del estudio. Se precarga con la del paciente. |
| `servicio` | `FK(Servicio, PROTECT, null=True, blank=True)` | |
| `estudios_solicitados` | `TextField(blank=True)` | |
| `tipo_estudio` | `CharField(choices=TipoEstudio, default='histologia')` | |
| `descripcion_microscopica` | `TextField(blank=True)` | |
| `comentarios` | renombrado desde `notas` (`RenameField`) | Conserva los datos. Confirmado en P-5. |
| `fecha_informe` | `DateTimeField(null=True)` | Se llena **solo** en `finalizar`, con `timezone.now()`. |
| `datos_finalizacion` | `JSONField(null=True)` | Datos congelados al finalizar (sección 3.7). |
| `numero_caso` | **se elimina** | Lo reemplaza `numero_peticion` (P-1, decisión D-7). |

**Por qué la EPS está en el paciente y también en el informe:** el paciente puede cambiar de EPS. El informe debe mostrar la EPS que tenía cuando se hizo el estudio, no la actual.

### 3.5 Número de petición `P-AÑO-consecutivo`

**Formato:** `P-2026-00045`. El año es el de la fecha local de creación (`timezone.localdate()`, America/Bogota). El consecutivo vuelve a empezar en 1 cada año y se rellena con ceros hasta 5 cifras. Si un año pasara de 99 999 informes, sigue creciendo (`P-2026-100000`) en lugar de cortarse.

**El problema que hay que evitar:** si se calcula como "el mayor número existente + 1", dos usuarios que guardan a la vez leen el mismo máximo y obtienen el mismo número.

**Solución: una tabla de contadores con una actualización atómica.**

```python
class ConsecutivoPeticion(models.Model):
    anio = models.PositiveIntegerField(primary_key=True)
    ultimo = models.PositiveIntegerField(default=0)


def siguiente_numero_peticion():
    """Se llama dentro de la misma transacción en la que se guarda el informe."""
    anio = timezone.localdate().year
    # UPDATE ... SET ultimo = ultimo + 1: la base de datos bloquea la fila (PostgreSQL)
    # o la base entera (SQLite) hasta el COMMIT, así que otro usuario espera su turno.
    if not ConsecutivoPeticion.objects.filter(anio=anio).update(ultimo=F('ultimo') + 1):
        try:
            with transaction.atomic():  # punto de guardado: el primer informe del año
                ConsecutivoPeticion.objects.create(anio=anio, ultimo=1)
        except IntegrityError:          # otro usuario creó la fila del año al mismo tiempo
            ConsecutivoPeticion.objects.filter(anio=anio).update(ultimo=F('ultimo') + 1)
    ultimo = ConsecutivoPeticion.objects.get(anio=anio).ultimo
    return f'P-{anio}-{ultimo:05d}'
```

- El número se asigna en `Informe.save()` cuando el informe es nuevo, dentro de `transaction.atomic()`. Así también se numeran los informes creados desde `/admin/`, `seed_data` o las pruebas (`Informe.objects.create(...)`).
- **Se empieza con UPDATE y no con SELECT.** En SQLite, una transacción que primero lee y después escribe puede fallar con "database is locked" en lugar de esperar. Con UPDATE, la transacción pide el bloqueo de escritura desde el principio y la otra espera (hasta `OPTIONS: {'timeout': 20}`, que se propone añadir a la configuración de SQLite). En PostgreSQL, el segundo UPDATE espera al COMMIT del primero y luego lee el valor ya incrementado.
- **Última barrera:** `unique=True` en `numero_peticion`. Aunque hubiera un error de lógica, la base de datos rechaza un número repetido.
- **Huecos:** si se borra un borrador, su número no se reutiliza. Es lo correcto en un documento clínico: un número de petición nunca debe apuntar a dos informes distintos. Se documenta en el README.
- **No se puede modificar:** el serializer marca el campo como de solo lectura y `/admin/` lo muestra como `readonly_fields`.

**Pruebas automáticas** (nueva clase `NumeroPeticionTests`):
1. El formato es `P-AAAA-NNNNN` y los números son consecutivos.
2. El consecutivo vuelve a empezar al cambiar de año (con `mock` de `timezone.localdate`).
3. Si el cliente envía `numero_peticion` en un POST o un PUT, se ignora.
4. **Concurrencia** (`TransactionTestCase`): 10 hilos esperan en un `threading.Barrier` y crean un informe por la API al mismo tiempo, cada uno con su propio `APIClient`. Al terminar, cada hilo cierra su conexión (`connection.close()`). La prueba comprueba que hay 10 números **distintos** y que son exactamente del `00001` al `00010`.
5. La restricción `unique` existe: crear dos informes con el mismo número a mano lanza `IntegrityError`.

**Ajuste necesario para la prueba 4:** la base de pruebas de SQLite es en memoria con caché compartida. Con varios hilos escribiendo, falla de inmediato con "database table is locked" en lugar de esperar. Por eso se propone que la base de pruebas de SQLite sea un archivo (`DATABASES['default']['TEST']['NAME']`), agregado a `.gitignore`. Si `DB_NAME` está definido, la misma prueba corre contra PostgreSQL. Lo recomendable es correrla también así antes de publicar la app.

### 3.6 Diagnósticos (modelo nuevo `Diagnostico`)

```python
class Diagnostico(models.Model):
    informe = models.ForeignKey(Informe, on_delete=models.CASCADE, related_name='diagnosticos')
    orden = models.PositiveSmallIntegerField()
    descripcion = models.TextField()
    codigo_cie10 = models.CharField(max_length=7, blank=True)

    class Meta:
        ordering = ['informe', 'orden']
        constraints = [UniqueConstraint(fields=['informe', 'orden'], name='diagnostico_orden_unico')]
```

- **En la API:** `diagnosticos` es una lista anidada dentro del informe: `[{"descripcion": "...", "codigo_cie10": "C44.3"}]`. El orden de la lista es el orden del informe. En un PUT, o en un PATCH que incluya `diagnosticos`, la lista enviada **reemplaza** a la anterior, dentro de la misma transacción.
- **CIE-10:** es opcional. Se pasa a mayúsculas, se valida con `^[A-Z][0-9]{2}(\.[0-9A-Z]{1,2})?$` y `C443` se normaliza a `C44.3`. No se carga el catálogo oficial de CIE-10, que tiene más de 12 000 códigos. Queda como mejora futura con autocompletado, junto con la CIE-O para morfología tumoral.
- **Límite:** 20 diagnósticos por informe y descripción no vacía.
- **Confirmado en la etapa 5:** si un PUT o un PATCH no trae `diagnosticos`, la lista guardada no cambia; una lista vacía los quita todos. Un borrador se puede guardar sin diagnósticos (la regla de "al menos uno" es para finalizar, etapa 6). La búsqueda `?q=` no incluye los diagnósticos por ahora.

### 3.7 Firma del patólogo

- Se agrega `Usuario.registro_medico` (`CharField(30, blank=True)`).
- **Quién lo escribe:** solo un administrador, al crear el usuario (`RegistroSerializer`) o desde `/admin/`. En `/perfil/` es de **solo lectura**, igual que `rol` (C-1): un registro médico falso firmaría informes clínicos (P-6, decisión D-8).
- **Quién firma:** siempre el **autor** del informe, que es el patólogo responsable según D-2. Aunque un admin finalice el informe de otro, la firma es la del autor.
- **Requisito para finalizar:** el autor debe tener `registro_medico`. Si no lo tiene, `finalizar` responde 400 con "El patólogo autor no tiene registro médico; un administrador debe registrarlo".
- **Datos congelados (`datos_finalizacion`):** al finalizar se guarda en JSON lo que imprime el encabezado y la firma:
  - del paciente: nombre, documento, fecha de nacimiento y sexo;
  - los nombres de la EPS y del servicio;
  - del autor: nombre, especialidad y registro médico.

  Si un informe está finalizado, la API y el PDF usan estos datos y no los actuales. Corregir el nombre de un paciente o de un usuario después **no cambia** un informe ya cerrado. Es la idea de D-3 aplicada también a los datos relacionados.
- **Imagen de la firma (opcional, fase posterior):** `Usuario.firma_imagen` (ImageField, PNG/JPG de máximo 1 MB, validada con Pillow como en el foro). Solo la sube un admin. No es una firma digital criptográfica; la "firma digital" de la hoja de ruta del README sigue pendiente.

### 3.8 Adendas (modelo nuevo `Adenda`)

```python
class Adenda(models.Model):
    informe = models.ForeignKey(Informe, on_delete=models.PROTECT, related_name='adendas')
    numero = models.PositiveSmallIntegerField()          # 1, 2, 3... dentro del informe
    motivo = models.CharField(max_length=300)
    texto = models.TextField()
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    firma = models.JSONField()                           # nombre, especialidad y registro médico congelados

    class Meta:
        constraints = [UniqueConstraint(fields=['informe', 'numero'], name='adenda_numero_unico')]
```

- **Endpoints:** `GET /api/informes/{id}/adendas/` y `POST /api/informes/{id}/adendas/` (acción del `InformeViewSet`). **No hay** PUT, PATCH ni DELETE: una adenda tampoco se modifica.
- **Reglas:**
  - Solo se puede crear en un informe **finalizado**. Si es un borrador responde 400, porque un borrador se corrige editándolo.
  - La crea el autor del informe o un admin, lo mismo que D-2 exige para finalizar. El auditor no puede.
  - Quien crea la adenda la firma y debe tener registro médico.
  - El número se asigna bloqueando el informe (`select_for_update`) y la restricción `unique` sirve de respaldo.
- **No contradice D-3:** el contenido original del informe no cambia. La adenda es un texto nuevo, fechado y firmado, que se agrega al final. Se propone registrarlo como una decisión nueva que complementa D-3 (D-9 en la sección 7).
- **En `/admin/`:** las adendas se ven en solo lectura.
- **En el PDF:** van después de la firma, en la sección "ADENDAS", con número, fecha, motivo, texto y firma. Además, al principio del informe aparece el aviso "Este informe tiene N adenda(s); ver al final", para que nadie lea el diagnóstico original sin saber que se corrigió.

### 3.9 Reglas para finalizar (ampliación de `finalizar`)

Para finalizar, además de lo que se exige hoy (autor o admin, y que no esté ya finalizado):

1. Tiene paciente.
2. Tiene al menos un diagnóstico.
3. El autor tiene registro médico.
4. Si el tipo de estudio es **histología**, la descripción microscópica no puede estar vacía. En los demás tipos de estudio es opcional (P-7, decisión D-8).

Al finalizar se fija `fecha_informe`, se guarda `datos_finalizacion` y se cambia el estado, todo en una sola transacción.

**Hecho en la etapa 6:** si faltan requisitos, `finalizar` responde 400 con todos a la vez: `{"detail": "No se puede finalizar el informe. …", "requisitos": [...]}`, y el formulario los muestra en una lista. La edad no se congela: se calcula con la fecha de nacimiento congelada y la fecha de ingreso, que tampoco cambia. Decisiones del usuario del 2026-10-04: `seed_data` da a `patologo1` el registro ficticio `RM-PRUEBA-0001` (también si ya existía sin registro), y el PDF actual ya usa la firma congelada y muestra el registro médico y la fecha de informe, sin esperar a la etapa 7.

Para **guardar un borrador** solo se exigen la patología, el paciente (en informes nuevos) y los campos obligatorios de la plantilla (I-2), como hoy. Así el patólogo puede guardar el trabajo a medias.

---

## 4. API: resumen de cambios

| Endpoint | Cambio |
|---|---|
| `GET/POST /api/pacientes/`, `GET/PUT/PATCH/DELETE /api/pacientes/{id}/` | **Nuevo.** Todos leen; crean y editan patólogo y admin; **borra solo admin** y solo si el paciente no tiene informes (P-4, decisión D-11). Búsqueda `?q=` por documento, nombres o apellidos. |
| `GET /api/pacientes/{id}/informes/` | **Nuevo.** Historial de informes del paciente. También se puede usar `?paciente=` en `/api/informes/`. |
| `/api/pacientes/eps/`, `/api/servicios/` | **Nuevos** catálogos con filtro `?activa=` (EPS) o `?activo=` (servicios). El nombre no se repite sin importar mayúsculas ni espacios. Hechos en la etapa 2. |
| `GET /api/opciones/` | **Nuevo.** Opciones de las listas fijas. |
| `POST/PUT /api/informes/` | Se dejan de aceptar `numero_caso` y `notas`. Se aceptan los campos de 3.4, `paciente` (id) y `diagnosticos` (lista). |
| `GET /api/informes/{id}/` | Devuelve además `numero_peticion`, `paciente` (objeto resumido con la `edad` calculada), `eps_nombre`, `servicio_nombre`, `diagnosticos`, `adendas`, `fecha_informe` y `firma`. En un informe finalizado, estos datos salen de `datos_finalizacion`. |
| `GET /api/informes/` | El listado cambia `numero_caso` por `numero_peticion` y agrega `paciente_nombre`, `paciente_documento` y `tipo_estudio`. `q` busca también por número de petición, orden externa, nombre y documento del paciente. Se agrega `select_related('paciente')` para no volver a tener consultas de más (M-4). |
| `POST /api/informes/{id}/finalizar/` | Reglas de 3.9. |
| `GET/POST /api/informes/{id}/adendas/` | **Nuevo** (3.8). |
| `GET /api/informes/{id}/pdf/` | El archivo pasa a llamarse `informe_P-2026-00045.pdf`. **Nunca** lleva el nombre ni el documento del paciente. |
| `/api/auth/registro/`, `/api/auth/perfil/` | `registro_medico`: un admin lo escribe al registrar al usuario; en el perfil es de solo lectura. |

**Reglas de privacidad en la API:**

- Los datos del paciente solo los ven usuarios autenticados, igual que los informes hoy.
- Los datos del paciente no se escriben en los registros (logs) ni en las URL.

---

## 5. PDF con la estructura del informe real

### 5.1 Orden

1. **Encabezado del laboratorio:** sale de `settings` y `.env` (`LABORATORIO_NOMBRE`, `LABORATORIO_DIRECCION` y `LABORATORIO_TELEFONO`, opcional). Valores por defecto (P-9): "PathoLab — Laboratorio de Patología (demostración)", "Santiago de Cali, Colombia" y sin teléfono. Si el teléfono está vacío, no se imprime.
2. **Tabla de datos en dos columnas**, como el formato real:

   | | |
   |---|---|
   | **Paciente:** Nombres Apellidos | **Identificación:** CC 0000000 |
   | **Edad:** 45 años | **Sexo:** Femenino |
   | **Médico tratante:** … | **EPS:** … |
   | **Servicio:** … | **N.º de petición:** P-2026-00045 |
   | **Fecha de ingreso:** 03/10/2026 | **Fecha de informe:** 04/10/2026 |
   | **Orden externa:** (solo si existe) | |
   | **Estudios solicitados:** (ocupa todo el ancho) | |

3. Título **"INFORME DE ANATOMÍA PATOLÓGICA"**.
4. **Tipo de estudio:** Histología. Debajo, en letra más pequeña, la patología y el tipo de muestra.
5. Aviso de adendas, si las hay (3.8).
6. **DESCRIPCIÓN MACROSCÓPICA** (`texto_generado`).
7. **DESCRIPCIÓN MICROSCÓPICA.**
8. **DIAGNÓSTICOS**, numerados: "1. Carcinoma basocelular nodular, márgenes libres. (CIE-10: C44.3)".
9. **COMENTARIOS.**
10. **Firma:** línea de firma (o la imagen, si existe), nombre, especialidad y "Registro médico N.º …".
11. **ADENDAS**, si las hay.
12. **Pie de cada página:** "N.º de petición P-2026-00045 · Página X de Y · Generado el dd/mm/aaaa hh:mm" (hora de Bogotá, M-10). Se repite en cada página para que una hoja suelta se pueda identificar. El "Página X de Y" usa un `canvasmaker` de ReportLab que numera las páginas al final.

### 5.2 Otros cambios del PDF

- **Se elimina la sección "DATOS CLÍNICOS"**, que imprimía `datos_ingresados` en bruto. Esos datos ya están redactados en la descripción macroscópica, y el formato real no tiene esa sección.
- **Borrador:** donde iría la fecha de informe se imprime "BORRADOR — SIN VALIDEZ" y no hay firma. Así no circula un borrador que parezca definitivo.
- **Seguridad:** todo texto nuevo del usuario pasa por `texto_seguro()` (I-3): nombre del paciente, médico tratante, estudios solicitados, microscópica, diagnósticos, comentarios y adendas.
- **Organización del código:** `generar_pdf_informe` se divide en funciones pequeñas (`_encabezado`, `_tabla_datos`, `_seccion`, `_firma`, `_adendas`), porque el PDF pasa de 6 a unas 12 partes.

---

## 6. Impacto de cada cambio

### 6.1 Base de datos (migraciones)

| Migración | Contenido | Datos que ya existen |
|---|---|---|
| `pacientes/0001_initial` (etapa 2) | `EPS` | — |
| `pacientes/0002_paciente` (etapa 3) | `Paciente` | — |
| `accounts/0002_registro_medico` | `Usuario.registro_medico` (y luego `firma_imagen`) | Queda vacío. Un admin lo llena. |
| `informes/0004_numero_peticion` (etapa 1) | `ConsecutivoPeticion`; agrega `numero_peticion` (nulo de forma temporal) y `numero_orden_externa` | — |
| `informes/0005_numerar_informes_existentes` (etapa 1) | **Migración de datos:** recorre los informes por `fecha_creacion`, les asigna `P-<año de creación>-NNNNN` y deja `ConsecutivoPeticion` en el último número de cada año | Todos los informes quedan numerados |
| `informes/0006_quitar_numero_caso` (etapa 1) | `numero_peticion` pasa a obligatorio y único; se elimina `numero_caso` (P-1) | Se pierde el número de caso anterior (P-1) |
| `informes/0007_servicio` (etapa 2) | `Servicio` | — |
| `informes/0008_datos_solicitud` | `paciente`, `medico_tratante`, `fecha_ingreso`, `eps`, `servicio`, `estudios_solicitados`, `tipo_estudio` | Los informes antiguos quedan sin paciente (`null`). Se ven y se imprimen con "No registrado". Para finalizar un borrador antiguo, primero hay que asignarle paciente. |
| `informes/0009_contenido` | `descripcion_microscopica`; `RenameField notas → comentarios`; modelo `Diagnostico` | Las notas se conservan como comentarios |
| `informes/0010_finalizacion` | `fecha_informe`, `datos_finalizacion` | **Migración de datos:** en los informes ya finalizados, `fecha_informe` toma el valor de `fecha_actualizacion`, que es la mejor aproximación disponible (se documenta). `datos_finalizacion` se llena con los datos actuales. |
| `informes/0011_adenda` | Modelo `Adenda` | — |

- Todas las migraciones tienen función de reversa cuando es posible. La 0006 no puede recuperar `numero_caso`: se eliminó por decisión del usuario (P-1).
- Después de cada etapa, `npm run dev` avisará de las migraciones pendientes (`migrate --check`). Esto ya funciona.

### 6.2 API

Ver la sección 4. **Cambio incompatible:** `numero_caso` y `notas` desaparecen de la API. El único cliente es el frontend de este repositorio, más la colección de Postman, así que se actualizan en la misma etapa.

### 6.3 Frontend

| Archivo | Cambio |
|---|---|
| `InformePage.jsx` | Se reorganiza en tarjetas con el orden del informe real: **Paciente** → **Datos de la solicitud** → **Estudio** (tipo de estudio, patología, tipo de muestra) → **Descripción macroscópica** (campos dinámicos y texto generado) → **Descripción microscópica** → **Diagnósticos** → **Comentarios** → **Firma** (solo lectura) → **Adendas**. Se quita el campo "Número de caso". El número de petición se muestra en el título después de guardar ("Informe P-2026-00045"). |
| Componentes nuevos en `components/informe/` | `SelectorPaciente.jsx`: busca por documento o nombre, con un botón "Nuevo paciente" que abre un formulario corto y muestra edad, sexo y EPS. También `ListaDiagnosticos.jsx` (filas para agregar, quitar y reordenar), `SeccionFirma.jsx` y `SeccionAdendas.jsx`. `InformePage.jsx` ya tiene unas 400 líneas; separar estas partes evita que se duplique. |
| `PacientesPage.jsx` (nueva, ruta `/pacientes`) | Lista con búsqueda, formulario para crear y editar, e historial de informes de cada paciente. Enlace nuevo en el Navbar. |
| `BuscarPage.jsx`, `DashboardPage.jsx` | Las columnas pasan a ser N.º de petición, Paciente, Tipo de estudio, Patología, Autor y Estado. Cambia el texto de ayuda de la búsqueda. |
| `PerfilPage.jsx` | Muestra el registro médico en solo lectura. Si un patólogo no lo tiene, avisa que no podrá finalizar informes. |
| `hooks/useOpciones.js` (nuevo) | Pide `/api/opciones/` una vez. No se agregan copias de las opciones a `constants.js`. |
| `PatologiasPage.jsx` u otra pantalla | Gestión de los catálogos de EPS y servicios (activar o desactivar, como D-4). Los administran patólogos y admin (P-4, D-11). |
| `PoliticaPrivacidadPage.jsx` | Se actualiza: ahora la aplicación guarda datos de salud de pacientes. |

### 6.4 PDF

Ver la sección 5. `texto_seguro()` y la hora de Bogotá se mantienen.

### 6.5 Pruebas que ya existen

**Backend** (`backend/informes/tests.py`, 77 pruebas en total en el proyecto):

| Clase | Qué cambia |
|---|---|
| `PermisosInformeTests` | El ayudante que crea informes deja de pasar `numero_caso` (ahora es automático) y los cuerpos de PUT ya no lo envían. Hay que añadir paciente y diagnóstico a las pruebas que finalizan, y registro médico al patólogo de prueba. **Las reglas probadas (D-2, D-3) no cambian.** |
| `BorrarPatologiaTests` | Se quita `numero_caso` del `create`. |
| `PdfConTextoDelUsuarioTests` | `notas` → `comentarios`. El texto con marcado que hoy está en `datos_ingresados` pasa a la microscópica, un diagnóstico y el nombre del paciente, porque "DATOS CLÍNICOS" desaparece del PDF. **El objetivo de I-3 se mantiene y cubre los campos nuevos.** La prueba de la hora de Bogotá (M-10) sigue igual. |
| `EstadisticasYPaginacionTests`, `NombreVisibleAutorTests` | Se quita `numero_caso`. `NombreVisibleAutorTests` usaba `numero_caso` como clave del diccionario y pasa a usar `numero_peticion`. |
| `DescargaPdfTests` | `test_nombre_de_archivo_sin_caracteres_peligrosos` pierde su sentido original, porque el número ya no lo escribe el usuario. Se cambia por "el archivo se llama `informe_P-AAAA-NNNNN.pdf` y no contiene datos del paciente". El saneamiento del nombre se mantiene, porque cuesta poco. |
| `CamposObligatoriosTests` | El cuerpo de la petición cambia `numero_caso` por `paciente`. |
| `ConsultasPorListadoTests` | Se le agrega el listado de informes, para comprobar que las consultas no crecen con `paciente`, `diagnosticos` y `adendas`. |
| `config/tests.py` | Puede necesitar ajustes por la base de pruebas en archivo (3.5). |

**Frontend:** en `InformePage.test.jsx` y `DashboardPage.test.jsx` hay que cambiar `numero_caso` por `numero_peticion` y `notas` por `comentarios` en los datos simulados, y simular `/opciones/`. La prueba de I-5 (PDF con Axios) sigue igual, pero el nombre esperado del archivo cambia.

**Raíz (`npm test`):** no cambia.

**Pruebas nuevas** (resumen): número de petición y concurrencia (3.5), edad calculada (años, meses, días y edad a la fecha de ingreso), paciente (documento único, borrado protegido, permisos), opciones, diagnósticos (reemplazo, orden, CIE-10 válido, inválido y normalizado), reglas para finalizar, datos congelados (cambiar el paciente o el usuario después no altera el informe finalizado), adendas (solo en finalizados, sin edición, permisos, numeración), PDF (orden de secciones, borrador, adendas) y los componentes nuevos del frontend.

### 6.6 Documentación

Se actualiza en cada etapa, según las reglas 2, 3 y 6 de `CLAUDE.md`:

- `CHANGELOG.md` y `docs/progreso.md`.
- `README.md`: características, estructura (app `pacientes`), referencia de la API, flujo del informe, usuarios de prueba (registro médico ficticio) y hoja de ruta. Se quita "descripción microscópica" y se aclara que la firma digital criptográfica sigue pendiente.
- `CLAUDE.md`: arquitectura (pacientes, número de petición, datos congelados, adendas, `/api/opciones/`).
- `docs/decisiones.md`: decisiones nuevas de la sección 7.
- Colección de Postman: cuerpo de "Crear informe" y carpetas nuevas de Pacientes, Opciones y Adendas. Se aprovecha para añadir "Cerrar sesión", que estaba pendiente.

---

## 7. Relación con `docs/decisiones.md`

| Decisión | Cómo se respeta |
|---|---|
| D-1 (los patólogos administran el catálogo) | El catálogo de patologías no cambia. Los catálogos nuevos (EPS, servicios) siguen el mismo criterio (P-4, D-11). |
| D-2 (solo el autor o un admin edita, borra o finaliza) | No cambia. Las adendas siguen la misma regla. La firma es siempre la del autor. |
| D-3 (un informe finalizado no se modifica) | No cambia. Las adendas **no modifican** el informe: se agregan aparte. Los datos congelados refuerzan D-3. La excepción de `/admin/` sigue igual, pero en `/admin/` las adendas son de solo lectura. |
| D-4 (se desactiva en lugar de borrar) | Se aplica igual a EPS y servicios. |
| D-5, D-6 | No se ven afectadas. |

**Decisiones nuevas, registradas en `docs/decisiones.md` el 2026-10-04:**

- **D-7.** El número de petición lo genera el sistema (`P-AÑO-NNNNN`, 5 cifras, reinicio cada año), nunca se reutiliza y reemplaza al número de caso, que se elimina.
- **D-8.** El registro médico solo lo asigna un administrador y la firma es siempre la del autor. Para finalizar: el autor tiene registro médico, el informe tiene al menos un diagnóstico y, si es de histología, descripción microscópica.
- **D-9.** Un informe finalizado se corrige con adendas. Las adendas no se editan ni se borran desde la aplicación.
- **D-10.** Al finalizar se congelan los datos del paciente, la EPS, el servicio y la firma.
- **D-11.** Pacientes y catálogos nuevos: patólogos y admin crean y editan pacientes y administran EPS y servicios; solo un admin borra pacientes, y solo si no tienen informes.

---

## 8. Datos de prueba y privacidad

- **Nunca se usan datos de pacientes reales**, ni en las pruebas, ni en `seed_data`, ni en Postman, ni en los ejemplos del README.
- **Nombres:** se usan nombres claramente ficticios, como "Paciente Ficticio Uno" o "Prueba Apellido Dos".
- **Documentos:** llevan el prefijo `PRUEBA` (por ejemplo `PRUEBA0001`). El campo es alfanumérico, así que un número ficticio no puede coincidir con el de una persona real.
- **Médicos tratantes:** "Médico Ficticio".
- **Registro médico de prueba:** `RM-PRUEBA-0001` para `patologo1` en `seed_data`.
- **Fechas de nacimiento:** fijas e inventadas.
- **Pacientes en `seed_data`:** crea 2 pacientes ficticios para poder probar en el navegador. No crea informes, como hoy.
- **Catálogo de EPS en `seed_data`:** incluye "Particular" y "Otra", más una lista corta de EPS colombianas reales. Son nombres de entidades públicas, no datos de personas, y el catálogo se puede editar (confirmado en P-8).
- **Ley:** los datos de salud son datos sensibles (Ley 1581 de 2012) y forman parte de la historia clínica (Resolución 1995 de 1999). La propuesta guarda solo los datos mínimos, nunca pone datos del paciente en URL, nombres de archivo ni logs, y actualiza la política de privacidad. Antes de un uso real haría falta una revisión legal, que este proyecto no reemplaza.

---

## 9. Orden de implementación por etapas

**Rama:** `informe-v2`, creada desde `main` el 2026-10-04.

**En cada etapa** se sigue el procedimiento de `docs/progreso.md`: prueba que falla → explicación y confirmación → arreglo → prueba que pasa → `CHANGELOG.md`, documentación, `progreso.md`, commit y push. Cada etapa deja la aplicación funcionando y con todas las pruebas en verde.

| Etapa | Contenido | Toca |
|---|---|---|
| **1. Número de petición** (hecha, 2026-10-04) | `ConsecutivoPeticion`, `numero_peticion` automático, migración de datos, se elimina `numero_caso`, `numero_orden_externa`, prueba de concurrencia y base de pruebas en archivo. Nombre del PDF, listados, formulario y Postman. | backend, frontend, PDF (solo el número), pruebas |
| **2. Catálogos y opciones** (hecha, 2026-10-04) | `EPS`, `Servicio`, `TipoEstudio`, `GET /api/opciones/` y `seed_data`. Solo backend, con sus pruebas. La app `pacientes` se crea aquí con solo la EPS. | backend |
| **3. Pacientes** (hecha, 2026-10-04) | Modelo `Paciente` en la app `pacientes`, CRUD, búsqueda, edad calculada, permisos, `useOpciones`, `PacientesPage` y enlace en el Navbar. Borrar una EPS que usa un paciente responde 400 ("desactívela"). | backend, frontend |
| **4. Datos de la solicitud** (hecha, 2026-10-04) | Paciente y campos de 3.4 en el informe, historial `GET /api/pacientes/{id}/informes/` (y en `PacientesPage`), 400 al borrar un paciente con informes (se pasaron de la etapa 3 porque necesitan `Informe.paciente`), `SelectorPaciente`, tarjeta "Datos de la solicitud", búsqueda ampliada, columnas de los listados y pantalla para administrar EPS y servicios (6.3). Borrar un servicio o una EPS que usa un informe responde 400. | backend, frontend |
| **5. Contenido del informe** (hecha, 2026-10-04) | Descripción microscópica, `notas` → `comentarios` y diagnósticos con CIE-10 (`ListaDiagnosticos`, que se reordena con botones de subir y bajar). El PDF actual ya imprime las tres secciones (decisión del usuario en la etapa 5); su estructura completa sigue en la etapa 7. | backend, frontend, PDF (secciones nuevas) |
| **6. Firma y finalización** (hecha, 2026-10-04) | `registro_medico`, reglas para finalizar, `fecha_informe`, `datos_finalizacion`, perfil y `SeccionFirma`. El PDF actual ya usa la firma congelada y muestra el registro médico y la fecha de informe (decisión del usuario en la etapa 6). | backend, frontend, PDF (firma y fecha de informe) |
| **7. PDF nuevo** | Estructura de la sección 5, encabezado configurable, numeración de páginas y borrador. | PDF |
| **8. Adendas** | Modelo, endpoints, sección en el frontend y en el PDF. | backend, frontend, PDF |
| **9. Cierre** | Política de privacidad, revisión completa del README y de Postman, comprobar que el código cumple D-7 a D-11 y prueba manual de todo el flujo en el navegador. | documentación |
| *(Opcional)* **10. Imagen de la firma** | `firma_imagen` en el usuario y en el PDF. | backend, PDF |

Las etapas 1 y 2 no dependen entre sí. Las demás van en el orden de la tabla.

---

## 10. Preguntas y respuestas del usuario (2026-10-04)

| Pregunta | Respuesta | Dónde queda |
|---|---|---|
| **P-1.** ¿Se elimina `numero_caso`? | **Sí, se elimina.** | D-7; etapa 1 |
| **P-2.** ¿Formato del consecutivo? | **5 cifras y reinicio cada año** (`P-2026-00045`). | D-7; etapa 1 |
| **P-3.** ¿Género? | Etiqueta **"Sexo"**, con las opciones **Femenino, Masculino e Indeterminado**. | Secciones 2, 3.1 y 5.1; etapas 2 y 3 |
| **P-4.** ¿Permisos de catálogos y pacientes? | **Los patólogos administran EPS y servicios. Borrar pacientes, solo el admin.** | D-11; etapas 2 y 3 |
| **P-5.** ¿Renombrar `notas`? | **Sí: `notas` → `comentarios`.** | Sección 3.4; etapa 5 |
| **P-6.** ¿Quién asigna el registro médico? | **Solo un administrador.** | D-8; etapa 6 |
| **P-7.** ¿Microscópica obligatoria para finalizar? | **Solo en histología; en los demás tipos de estudio es opcional. Siempre se exige al menos un diagnóstico.** | D-8; sección 3.9; etapa 6 |
| **P-8.** ¿EPS de `seed_data`? | **Lista corta de EPS reales, más "Particular" y "Otra".** | Sección 8; etapa 2 |
| **P-9.** ¿Encabezado del PDF? | **"PathoLab — Laboratorio de Patología (demostración)", "Santiago de Cali, Colombia", sin teléfono.** | Sección 5.1; etapa 7 |
