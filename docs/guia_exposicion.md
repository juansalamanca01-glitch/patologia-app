# 🎓 Guía Completa de Exposición Académica — PathoLab (`patologia-app`)

**Proyecto**: PathoLab — Sistema de Gestión y Automatización de Informes de Patología Clínica  
**Estudiante**: Juan Salamanca  
**Institución**: Unicatólica  
**Repositorio GitHub**: [https://github.com/juansalamanca01-glitch/patologia-app](https://github.com/juansalamanca01-glitch/patologia-app)  

---

## 📌 Índice del Documento

1. [Diapositiva 1: Portada y Presentación](#1-portada-y-presentación)
2. [Diapositiva 2: Problemática Real](#2-problemática-real)
3. [Diapositiva 3: Qué Quiero Resolver (La Solución)](#3-qué-quiero-resolver-la-solución)
4. [Diapositiva 4: Cuántos Endpoints Necesita mi App](#4-cuántos-endpoints-necesita-mi-app)
5. [Diapositiva 5: Endpoint #1 en Funcionamiento (Login JWT)](#5-endpoint-1-en-funcionamiento-login-jwt)
6. [Diapositiva 6: Endpoint #2 en Funcionamiento (Creación de Informe)](#6-endpoint-2-en-funcionamiento-creación-de-informe)
7. [Diapositiva 7: Guía Paso a Paso para la Demostración en Postman](#7-guía-paso-a-paso-para-la-demostración-en-postman)
8. [Diapositiva 8: Conclusiones y Roadmap](#8-conclusiones-y-roadmap)
9. [Preguntas Frecuentes del Profesor y Cómo Responderlas](#9-preguntas-frecuentes-del-profesor-y-cómo-responderlas)

---

## 1. Portada y Presentación

### Contenido de la Diapositiva
- **Título**: **PathoLab** — Sistema Clínico de Informes de Patología
- **Subtítulo**: API REST en Django + Frontend en React para la automatización del flujo histopatológico
- **Expositor**: Juan Salamanca
- **Carrera / Materia**: Ingeniería de Sistemas / Desarrollo de Software

### 🎙️ Guión sugerido para iniciar:
> *"Buenos días profesor y compañeros. Hoy les presento **PathoLab**, una solución de software diseñada para resolver un problema recurrente en el sector salud: la ineficiencia y el riesgo de error humano en la transcripción y elaboración de informes de patología clínica. A continuación veremos la problemática que ataca, la solución construida, la arquitectura de nuestra API REST y una demostración en vivo con Postman."*

---

## 2. Problemática Real

### Contenido de la Diapositiva
- **Redacción manual repetitiva**: Los médicos patólogos dedican hasta un 60% de su jornada laboral a redactar informes descriptivos extensos en procesadores de texto planos (Word) o notas físicas.
- **Riesgo de omisión de variables críticas**: Al no existir un formulario estructurado que valide campos según el tipo de órgano, con frecuencia se omiten datos esenciales para el diagnóstico oncológico (dimensiones del tumor, estado de márgenes quirúrgicos, afección ganglionar).
- **Falta de estandarización en la redacción**: Diferentes profesionales emplean términos dispares para la misma muestra, lo cual entorpece la interpretación del cirujano u oncólogo.
- **Inseguridad y falta de trazabilidad**: En archivos Word o papeles no hay control de versiones, firma digital ni segregación de funciones entre quien redacta, quien revisa y quien audita.

### 🎙️ Guión sugerido:
> *"En los laboratorios clínicos, cuando llega una biopsia, el patólogo realiza una descripción macroscópica: mide, pesa y observa la muestra. Actualmente, esto suele transcribirse a mano o en procesadores de texto sin validaciones. Si el médico olvida registrar si los márgenes estaban libres o comprometidos, el informe queda incompleto y se pone en riesgo el tratamiento del paciente. Además, la redacción consume horas valiosas que el patólogo debería dedicar al análisis microscópico."*

---

## 3. Qué Quiero Resolver (La Solución)

### Contenido de la Diapositiva
- 🩺 **14 Plantillas Médicas Específicas**: Formularios dinámicos adaptados a cada tipo de muestra (Piel, Mama, Tiroides, Próstata, Vesícula, Colon, etc.).
- 🤖 **Generador Automático en Lenguaje Natural**: El backend procesa los datos ingresados en el formulario y redacta en milisegundos un párrafo descriptivo formal con vocabulario médico exacto.
- 🔐 **Seguridad Basada en Roles (RBAC)**:
  - **Administrador**: Gestión del sistema y configuración de catálogos.
  - **Patólogo**: Elaboración, edición y cierre formal de informes.
  - **Auditor**: Búsqueda, trazabilidad y lectura de informes históricos.
- 📄 **Exportación a PDF Clínico**: Generación inmediata de informes oficiales listos para firma e impresión con ReportLab.

### 🎙️ Guión sugerido:
> *"PathoLab resuelve este problema transformando la recolección de datos en un proceso estructurado e inteligente. El patólogo simplemente selecciona el tipo de patología y el sistema despliega dinámicamente los campos requeridos. Al guardar, el backend analiza las respuestas y redacta automáticamente la descripción macroscópica en lenguaje natural, garantizando que no falte ningún dato obligatorio y produciendo un PDF oficial listo para el historial clínico del paciente."*

---

## 4. Cuántos Endpoints Necesita mi App

### Contenido de la Diapositiva
Nuestra API REST modular expone **25 operaciones / métodos HTTP**, agrupados en **4 módulos funcionales** y **9 rutas base de recursos**:

| Módulo | Métodos | Rutas URL | Descripción Funcional |
|---|---|---|---|
| **1. Autenticación y Cuentas** | 6 endpoints | `/api/auth/` | Login con JWT (`/login/`), renovación de token (`/refresh/`), consulta de perfil (`/perfil/`), cambio de contraseña (`/cambiar-password/`), registro y lista de usuarios (solo admin). |
| **2. Catálogo de Patologías** | 6 operaciones | `/api/patologias/` | CRUD completo para administrar los tipos de patología médica activas en el laboratorio. |
| **3. Plantillas de Formularios** | 6 operaciones | `/api/plantillas/` | CRUD para los campos dinámicos asociados a cada patología (tipos de campo: texto, lista, número, etc.). |
| **4. Informes Clínicos** | 7 operaciones | `/api/informes/` | CRUD de informes, motor de búsqueda con filtros (`q`, fecha, estado), acción para **finalizar informe** (`/finalizar/`) y **exportación a PDF** (`/pdf/`). |
| **Total Global** | **25 métodos** | **9 rutas URI** | **Cobertura integral del ciclo clínico del laboratorio.** |

### 🎙️ Guión sugerido:
> *"Para cubrir todo el flujo de trabajo, la aplicación necesita 25 operaciones REST organizadas en 4 módulos. El módulo de autenticación protege la aplicación mediante JSON Web Tokens; los módulos de patologías y plantillas manejan el esquema dinámico de los formularios; y el módulo de informes gestiona el ciclo de vida del reporte, su búsqueda con filtros multicriterio y la exportación a formato PDF."*

---

## 5. Endpoint #1 en Funcionamiento (Login JWT)

### Especificación Técnica
- **Finalidad**: Autenticación segura y obtención de credenciales JWT con rol de usuario.
- **Método HTTP**: `POST`
- **Ruta URL**: `http://127.0.0.1:8000/api/auth/login/`
- **Cabeceras (Headers)**:
  ```http
  Content-Type: application/json
  ```

### Petición (Request Body)
```json
{
  "username": "patologo1",
  "password": "patologo1234"
}
```

### Respuesta Exitosa (Response 200 OK)
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 2,
    "username": "patologo1",
    "email": "patologo@patologia.local",
    "nombre_completo": "Dr. Carlos Méndez",
    "rol": "patologo",
    "especialidad": "Patología Quirúrgica",
    "activo": true,
    "fecha_creacion": "2026-03-13T23:53:31.046495-05:00"
  }
}
```

### 🎙️ Qué explicar al mostrarlo:
> *"Este primer endpoint valida las credenciales contra la base de datos y genera dos tokens: el `access` (que autorizará las peticiones subsiguientes) y el `refresh`. Lo especial de nuestra implementación en Django es que customizamos el token para incluir el rol del usuario (`patologo`), de manera que el frontend y el backend saben de inmediato qué permisos tiene sin realizar consultas adicionales."*

---

## 6. Endpoint #2 en Funcionamiento (Creación de Informe)

### Especificación Técnica
- **Finalidad**: Registrar un nuevo informe histopatológico y ejecutar el motor de redacción macroscópica en lenguaje natural.
- **Método HTTP**: `POST`
- **Ruta URL**: `http://127.0.0.1:8000/api/informes/`
- **Cabeceras (Headers)**:
  ```http
  Authorization: Bearer <access_token>
  Content-Type: application/json
  ```

### Petición (Request Body)
```json
{
  "numero_caso": "PAT-2026-EXP-01",
  "patologia": 1,
  "tipo_muestra": "Biopsia escisional",
  "datos_ingresados": {
    "localizacion": "Espalda región escapular derecha",
    "tipo_muestra": "Escisional",
    "dimensiones": "2.5 x 1.8 x 0.6 cm",
    "color": "Pigmentado",
    "bordes": "Irregulares",
    "superficie": "Rugosa con ulceración central",
    "hallazgos_adicionales": "Lesión nodular hiperpigmentada sin sangrado"
  },
  "notas": "Muestra fijada en formol al 10% remitida por Dermatología"
}
```

### Respuesta Exitosa (Response 201 Created)
```json
{
  "id": 1,
  "numero_caso": "PAT-2026-EXP-01",
  "patologia": 1,
  "patologia_nombre": "Biopsia de Piel",
  "autor": 2,
  "autor_nombre": "Dr. Carlos Méndez",
  "fecha": "2026-09-07",
  "tipo_muestra": "Biopsia escisional",
  "datos_ingresados": {
    "localizacion": "Espalda región escapular derecha",
    "tipo_muestra": "Escisional",
    "dimensiones": "2.5 x 1.8 x 0.6 cm",
    "color": "Pigmentado",
    "bordes": "Irregulares",
    "superficie": "Rugosa con ulceración central",
    "hallazgos_adicionales": "Lesión nodular hiperpigmentada sin sangrado"
  },
  "texto_generado": "Se recibe espécimen para estudio de Biopsia de Piel. El tipo de muestra corresponde a Escisional. La localización anatómica es Espalda región escapular derecha. Las dimensiones son 2.5 x 1.8 x 0.6 cm. El color macroscópico observado es Pigmentado. La superficie se describe como Rugosa con ulceración central. Los bordes se observan Irregulares. Hallazgos adicionales: Lesión nodular hiperpigmentada sin sangrado. Se procesa el material y se remite para estudio histopatológico.",
  "estado": "borrador",
  "notas": "Muestra fijada en formol al 10% remitida por Dermatología",
  "fecha_creacion": "2026-09-07T15:30:00.000000-05:00",
  "fecha_actualizacion": "2026-09-07T15:30:00.000000-05:00"
}
```

### 🎙️ Qué explicar al mostrarlo:
> *"Este endpoint representa el valor diferencial de PathoLab. Nosotros no enviamos el texto de la descripción redactado; enviamos los datos en un diccionario JSON estructurado. El servidor valida que los campos requeridos estén presentes y ejecuta el algoritmo generador que construye el campo `texto_generado` en lenguaje natural. Además, asocia automáticamente al patólogo autenticado como autor del caso y lo guarda en estado borrador para su posterior revisión."*

---

## 7. Guía Paso a Paso para la Demostración en Postman

Para que la demostración en la clase salga perfecta:

```
PASO 1: Iniciar el servidor local
   └─ Terminal: cd backend && python manage.py runserver
   
PASO 2: Petición en Postman 1 (Login)
   ├─ Método: POST
   ├─ URL: http://127.0.0.1:8000/api/auth/login/
   ├─ Body (raw JSON): {"username": "patologo1", "password": "patologo1234"}
   ├─ Clic en "Send" -> Recibir 200 OK
   └─ Copiar el valor del string "access"

PASO 3: Petición en Postman 2 (Crear Informe)
   ├─ Nueva pestaña en Postman
   ├─ Método: POST
   ├─ URL: http://127.0.0.1:8000/api/informes/
   ├─ Headers:
   │    Key: Authorization
   │    Value: Bearer <pegar_access_token>
   ├─ Body (raw JSON): pegar el JSON de la Diapositiva 6
   ├─ Clic en "Send" -> Recibir 201 Created
   └─ Resaltar ante el profesor el campo "texto_generado"
```

> [!TIP]
> **Punto Extra / Sorpresa**:
> En una tercera pestaña de Postman, haz una petición **GET** a:  
> `http://127.0.0.1:8000/api/informes/1/pdf/`  
> con el Header `Authorization: Bearer <token>`.  
> Postman descargará el archivo PDF clínico generado con ReportLab directamente en la respuesta.

---

## 8. Conclusiones y Roadmap

### Conclusiones
- **Impacto directo en la productividad médica**: Se reduce drásticamente el tiempo de transcripción y se mitigan los riesgos de omisión en biopsias.
- **Arquitectura escalable**: Separación limpia entre lógica de negocio (Django REST Framework) y experiencia de usuario (React + Vite).
- **Seguridad y buenas prácticas**: Control de acceso por roles, autenticación JWT, código versionado en GitHub con documentación y control de entornos.

### Roadmap (Próximos Pasos en el Semestre)
- [ ] Integración de fotos microscópicas y macroscópicas directas en el PDF.
- [ ] Módulo de diagnóstico microscópico e inmunohistoquímica (IHQ).
- [ ] Firma electrónica del patólogo.
- [ ] Contenedorización con Docker y despliegue en la nube.

---

## 9. Preguntas Frecuentes del Profesor y Cómo Responderlas

1. **¿Qué pasa si el patólogo no llena un campo obligatorio?**
   - *Respuesta*: *"El serializador de Django valida el campo `datos_ingresados` contrastándolo contra los campos marcados como obligatorios en la plantilla de esa patología. Si falta alguno, la API rechaza la petición con un error HTTP `400 Bad Request` indicando exactamente cuáles campos faltan."*

2. **¿Por qué usaron JWT en lugar de sesiones de Django?**
   - *Respuesta*: *"Porque JWT es un estándar sin estado (stateless) ideal para APIs REST. Nos permite desacoplar completamente el backend del frontend en React y abre la puerta para que en el futuro una app móvil consuma la misma API sin requerir cookies de sesión."*

3. **¿Cómo se genera el texto macroscópico?**
   - *Respuesta*: *"En el archivo `informes/utils.py` desarrollamos una función que mapea las variables clínicas a patrones de redacción médica en lenguaje natural. Concatena las oraciones con coherencia gramatical y agrega las cláusulas de procesamiento técnico."*

4. **¿Dónde está alojado el código?**
   - *Respuesta*: *"El código está completamente documentado y publicado en GitHub bajo la rama `main` en: `https://github.com/juansalamanca01-glitch/patologia-app`."*
