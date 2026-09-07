# 🔬 PathoLab — Sistema de Gestión de Informes de Patología Clínica

[![Django](https://img.shields.io/badge/Django-4.2+-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/DRF-3.14+-red?style=for-the-badge&logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![JWT](https://img.shields.io/badge/JWT-Auth-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white)](https://jwt.io/)

**PathoLab** es una plataforma web moderna diseñada para la captura, generación automatizada, gestión y auditoría de informes histopatológicos clínicos. El sistema acelera el flujo de trabajo de los patólogos transformando entradas estructuradas de laboratorio en descripciones macroscópicas en lenguaje natural y generando informes en PDF de calidad médica listos para impresión.

---

## 📋 Tabla de Contenidos

- [Características Principales](#-características-principales)
- [Arquitectura y Tecnologías](#-arquitectura-y-tecnologías)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación y Configuración Local](#-instalación-y-configuración-local)
  - [1. Clonar el Repositorio](#1-clonar-el-repositorio)
  - [2. Configuración del Backend (Django)](#2-configuración-del-backend-django)
  - [3. Configuración del Frontend (React + Vite)](#3-configuración-del-frontend-react--vite)
- [Usuarios y Cuentas de Prueba](#-usuarios-y-cuentas-de-prueba)
- [Catálogo de Patologías Incluidas](#-catálogo-de-patologías-incluidas)
- [Referencia de la API REST](#-referencia-de-la-api-rest)
- [Flujo de Trabajo del Informe](#-flujo-de-trabajo-del-informe)
- [Hoja de Ruta (Roadmap)](#-hoja-de-ruta-roadmap)

---

## ✨ Características Principales

- 🩺 **14 Patologías Clínicas Preconfiguradas**: Formularios especializados por tipo de espécimen con protocolos médicos integrados.
- 📝 **Formularios Dinámicos Basados en Esquemas**: Los campos (textos, números, listas desplegables, áreas de texto) se renderizan dinámicamente según la patología seleccionada.
- 🤖 **Generador Automático de Descripción Macroscópica**: Transforma instantáneamente las mediciones y observaciones estructuradas en párrafos clínicos redactados en lenguaje natural.
- 📄 **Exportación de Informes a PDF**: Generación con **ReportLab** de informes formales con encabezado institucional, número de caso, metadatos, tabla de hallazgos y firma del patólogo.
- 🔐 **Control de Acceso Basado en Roles (RBAC)**:
  - **Administrador**: Gestión completa de usuarios, patologías y plantillas.
  - **Patólogo**: Creación, edición, redacción y finalización de informes histopatológicos.
  - **Auditor**: Búsqueda avanzada, consulta y descarga de informes (modo solo lectura).
- 🔍 **Búsqueda y Filtros Avanzados**: Búsqueda en tiempo real por número de caso, patología, tipo de muestra, rango de fechas y estado del informe.

---

## 🛠️ Arquitectura y Tecnologías

`
┌────────────────────────────────────────────────────────┐
│                   Cliente (Navegador)                  │
│             React 18 + Vite + React Router             │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTP / JSON (Axios)
                           │ JWT Bearer Token
┌──────────────────────────▼─────────────────────────────┐
│                 API REST Backend (Django)               │
│  ┌─────────────────────────┐ ┌───────────────────────┐ │
│  │    App: accounts        │ │     App: informes     │ │
│  │  - Auth JWT             │ │  - Catálogo Patología │ │
│  │  - Roles (RBAC)         │ │  - Plantillas Dinámicas││
│  │  - Gestión de usuarios  │ │  - Informes & Filtros │ │
│  └─────────────────────────┘ └───────────┬───────────┘ │
│                                          │             │
│                     ┌────────────────────▼───────────┐ │
│                     │  Motor de Generación PDF       │ │
│                     │  ReportLab (Letter, Styles)    │ │
│                     └────────────────────────────────┘ │
└──────────────────────────┬─────────────────────────────┘
                           │ ORM
┌──────────────────────────▼─────────────────────────────┐
│                 Base de Datos (SQLite / PostgreSQL)     │
└────────────────────────────────────────────────────────┘
`

- **Backend**:
  - Python 3.10+
  - Django 4.2 LTS
  - Django REST Framework (DRF) 3.14+
  - SimpleJWT (Autenticación por tokens con rotación)
  - django-cors-headers
  - ReportLab 4.1+ (Generación de PDF)
- **Frontend**:
  - React 18
  - Vite 5.4
  - React Router DOM 6
  - Axios (con interceptores para adjuntar automáticamente el token JWT)
  - CSS modular responsive

---

## 📁 Estructura del Proyecto

`
patologia-app/
├── backend/
│   ├── accounts/              # Módulo de usuarios, roles y autenticación
│   │   ├── models.py          # Modelo Usuario personalizado con roles
│   │   ├── permissions.py     # Permisos DRF (EsPatologoOAdmin, EsSoloLectura)
│   │   ├── serializers.py     # Serializadores de login, registro y perfil
│   │   ├── urls.py            # Endpoints /api/auth/
│   │   └── views.py           # Vistas de autenticación y JWT
│   ├── config/                # Configuración principal de Django
│   │   ├── settings.py        # Settings, JWT, CORS e internacionalización
│   │   ├── urls.py            # Enrutador general
│   │   └── wsgi.py / asgi.py
│   ├── informes/              # Módulo principal de patología
│   │   ├── management/
│   │   │   └── commands/
│   │   │       └── seed_data.py # Población inicial (usuarios + 14 patologías)
│   │   ├── models.py          # Modelos Patologia, Plantilla, Informe
│   │   ├── serializers.py     # Serializadores de informes y esquemas
│   │   ├── urls.py            # Endpoints /api/
│   │   ├── utils.py           # Generador de descripción y constructor PDF
│   │   └── views.py           # ViewSets para CRUD de informes y descarga PDF
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── public/
│   │   ├── favicon.svg
│   │   └── icons.svg
│   ├── src/
│   │   ├── api/
│   │   │   └── client.js      # Cliente Axios configurado con base URL y JWT
│   │   ├── assets/
│   │   ├── components/
│   │   │   └── Navbar.jsx     # Barra de navegación con datos del usuario y rol
│   │   ├── context/
│   │   │   └── AuthContext.jsx# Contexto global de sesión y permisos
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx     # Inicio de sesión con validación
│   │   │   ├── DashboardPage.jsx # Panel principal con métricas e historial
│   │   │   ├── InformePage.jsx   # Formulario dinámico, vista previa y guardado
│   │   │   └── BuscarPage.jsx    # Búsqueda multicriterio y exportación
│   │   ├── App.jsx            # Enrutador principal y rutas protegidas
│   │   ├── index.css          # Estilos globales y componentes UI
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js         # Configuración Vite con proxy hacia backend
│   └── .env.example
├── .gitignore
└── README.md
`

---

## 📦 Requisitos Previos

Asegúrate de tener instaladas las siguientes herramientas en tu entorno:

- **Python**: 3.10 o superior ([python.org](https://www.python.org/))
- **Node.js**: 18 o superior y **npm** ([nodejs.org](https://nodejs.org/))
- **Git**: 2.30 o superior ([git-scm.com](https://git-scm.com/))

---

## 🚀 Instalación y Configuración Local

### 1. Clonar el Repositorio

`ash
git clone https://github.com/juansalamanca01-glitch/patologia-app.git
cd patologia-app
`

---

### 2. Configuración del Backend (Django)

1. **Navega al directorio backend**:
   `ash
   cd backend
   `

2. **Crea y activa un entorno virtual**:
   - En Windows (PowerShell):
     `powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     `
   - En Linux / macOS:
     `ash
     python3 -m venv venv
     source venv/bin/activate
     `

3. **Instala las dependencias**:
   `ash
   pip install -r requirements.txt
   `

4. **Configura el archivo de variables de entorno (opcional en desarrollo)**:
   `ash
   copy .env.example .env     # En Windows
   # cp .env.example .env      # En Linux/macOS
   `

5. **Aplica las migraciones de base de datos**:
   `ash
   python manage.py migrate
   `

6. **Puebla la base de datos con las 14 patologías y los usuarios de prueba**:
   `ash
   python manage.py seed_data
   `

7. **Inicia el servidor de desarrollo**:
   `ash
   python manage.py runserver
   `
   El backend estará disponible en http://127.0.0.1:8000/.

---

### 3. Configuración del Frontend (React + Vite)

Abre una **segunda terminal** en la raíz del proyecto:

1. **Navega al directorio frontend**:
   `ash
   cd frontend
   `

2. **Instala las dependencias de Node**:
   `ash
   npm install
   `

3. **Inicia el servidor de desarrollo Vite**:
   `ash
   npm run dev
   `
   La aplicación web estará disponible en http://localhost:5173/.

> [!NOTE]
> Vite incluye un proxy preconfigurado en ite.config.js que redirige automáticamente todas las peticiones /api al backend en el puerto 8000.

---

## 👥 Usuarios y Cuentas de Prueba

El comando python manage.py seed_data crea automáticamente tres usuarios para pruebas de cada rol del sistema:

| Usuario | Contraseña | Rol | Permisos Principales |
|---|---|---|---|
| dmin | dmin1234 | **Administrador** | Acceso al panel Django Admin, gestión de usuarios, creación de patologías y plantillas. |
| patologo1 | patologo1234 | **Patólogo** | Creación y edición de informes, generación de descripciones, finalización de casos y descarga PDF. |
| uditor1 | uditor1234 | **Auditor** | Acceso de solo lectura al dashboard, buscador de informes y descarga de PDF para auditorías. |

---

## 🏥 Catálogo de Patologías Incluidas

El sistema incluye plantillas clínicas detalladas para 14 tipos de especímenes:

1. **Biopsia de Piel** (Localización, punch/escisional/shave, dimensiones, bordes, color).
2. **Biopsia de Mama** (Lateralidad, tipo muestra, márgenes quirúrgicos, tamaño tumor, ganglios).
3. **Apéndice Cecal** (Longitud, diámetro, superficie serosa, consistencia, color).
4. **Vesícula Biliar** (Dimensiones, pared/espesor, mucosa, cálculos y conteo).
5. **Biopsia de Próstata** (Número de cilindros, localización anatómica, longitud agregada, PSA).
6. **Tiroides** (Lateralidad, nódulos, cápsula, dimensiones, peso).
7. **Colon y Recto** (Localización anatómica, morfología lesional, márgenes, ganglios).
8. **Útero y Cérvix** (Dimensiones uterinas, miomas, grosor endometrial, cuello y anexos).
9. **Ganglio Linfático** (Tipo biopsia, localización, número, necrosis, cápsula).
10. **Biopsia Gástrica** (Región gástrica, conteo de fragmentos, sospecha de *H. pylori*).
11. **Pulmón** (Lateralidad, lóbulo, márgenes bronquial y vascular, compromiso pleural).
12. **Riñón** (Nefrectomía/biopsia, tamaño tumoral, cápsula y vena renal).
13. **Amígdalas y Adenoides** (Dimensiones bilaterales, criptas, exudado, consistencia).
14. **Tejido Blando** (Lesión sospechada: lipoma/quiste/etc., planos anatómicos, márgenes).

---

## 🔌 Referencia de la API REST

### Autenticación (/api/auth/)
| Método | Endpoint | Descripción | Acceso |
|---|---|---|---|
| POST | /api/auth/login/ | Iniciar sesión y obtener token JWT (access + refresh) | Público |
| POST | /api/auth/refresh/ | Refrescar token de acceso | Público |
| GET | /api/auth/perfil/ | Obtener datos del usuario autenticado | Autenticado |
| POST | /api/auth/cambiar-password/ | Cambio de contraseña | Autenticado |
| GET | /api/auth/usuarios/ | Listar usuarios del sistema | Solo Admin |

### Informes y Patología (/api/)
| Método | Endpoint | Descripción | Acceso |
|---|---|---|---|
| GET | /api/patologias/ | Listar tipos de patología activas | Todos |
| GET | /api/patologias/{id}/ | Detalle de patología con sus campos de plantilla | Todos |
| GET | /api/plantillas/?patologia={id} | Obtener campos dinámicos de una patología | Patólogo / Admin |
| GET | /api/informes/ | Listar informes con filtros (q, echa_desde, echa_hasta, estado, patologia) | Todos |
| POST | /api/informes/ | Crear nuevo informe (genera descripción macroscópica) | Patólogo / Admin |
| GET | /api/informes/{id}/ | Ver informe completo | Todos |
| PUT/PATCH| /api/informes/{id}/ | Actualizar informe en estado borrador | Patólogo / Admin |
| POST | /api/informes/{id}/finalizar/ | Marcar informe como finalizado (bloquea edición) | Patólogo / Admin |
| GET | /api/informes/{id}/pdf/ | Generar y descargar informe clínico en formato PDF | Todos |

---

## 🔄 Flujo de Trabajo del Informe

`mermaid
graph TD
    A[Inicio de Sesión] --> B{Rol del Usuario}
    B -->|Patólogo / Admin| C[Crear Nuevo Informe]
    B -->|Auditor| D[Buscador / Dashboard]
    C --> E[Seleccionar Patología Clínica]
    E --> F[Carga de Plantilla Dinámica]
    F --> G[Llenar Datos Macroscópicos]
    G --> H[Guardar como Borrador]
    H --> I[Generador Automático de Texto Macroscópico]
    I --> J{¿Revisión Satisfactoria?}
    J -->|No| G
    J -->|Sí| K[Finalizar Informe]
    K --> L[Generar y Descargar PDF Formal]
    D --> L
`

---

## 🗺️ Hoja de Ruta (Roadmap)

Para continuar con el desarrollo en el nuevo semestre:

- [ ] **Módulo de Descripción Microscópica**: Integrar plantillas de diagnóstico microscópico e inmunohistoquímica (IHQ).
- [ ] **Carga de Imágenes Macroscópicas/Microscópicas**: Adjuntar microfotografías directamente al informe y al PDF.
- [ ] **Firma Digital Biométrica**: Firma electrónica de patólogos con certificado o trazo digital.
- [ ] **Integración HL7 / FHIR**: Interoperabilidad con Sistemas de Información Hospitalaria (HIS/LIS).
- [ ] **Contenedorización Docker**: Creación de Dockerfile y docker-compose.yml para despliegue en un clic.

---

## 👨‍💻 Autor y Contacto

- **Proyecto**: PathoLab (patologia-app)
- **Desarrollado por**: Juan Salamanca ([@juansalamanca01-glitch](https://github.com/juansalamanca01-glitch))
- **Institución**: Unicatólica
