from pathlib import Path
from datetime import timedelta
from decouple import config, Csv, UndefinedValueError
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------- Core / seguridad general ----------
# SECRET_KEY, DEBUG y ALLOWED_HOSTS se leen de variables de entorno (.env).
# No hay SECRET_KEY por defecto: el código es público y con esa clave se podrían
# falsificar tokens JWT. Si falta, la app no arranca (auditoría C-3).
try:
    SECRET_KEY = config('SECRET_KEY')
except UndefinedValueError:
    raise ImproperlyConfigured(
        'Falta la variable SECRET_KEY. Copia backend/.env.example como backend/.env '
        'y pon una clave propia (ver README).'
    )

# Si no se define, DEBUG queda desactivado (modo seguro para producción).
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# ---------- Applications ----------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    # Local
    'accounts',
    'informes',
    'foro',
]

# ---------- Middleware ----------
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ---------- Database (persistencia) ----------
# En desarrollo usa SQLite. En producción, definiendo DB_NAME en el .env
# se conecta automáticamente a Postgres (persistencia real, no efímera).
if config('DB_NAME', default=''):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
            'CONN_MAX_AGE': 60,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ---------- Auth ----------
AUTH_USER_MODEL = 'accounts.Usuario'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------- REST Framework ----------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    # ---- Anti-SPAM / seguridad de la API REST ----
    # Limita cuántas peticiones puede hacer un cliente en una ventana de tiempo,
    # para frenar fuerza bruta en login y flood de publicaciones/comentarios.
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',
        'user': '120/minute',
        'login': '10/minute',
        'registro': '5/minute',
        'foro_publicacion': '10/minute',
        'foro_comentario': '20/minute',
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ---------- CORS ----------
# En desarrollo (DEBUG=True) se permite todo para no trabar al equipo.
# En producción SOLO se permiten los orígenes listados explícitamente en el .env.
CORS_ALLOW_ALL_ORIGINS = DEBUG
if not DEBUG:
    CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='', cast=Csv())

# ---------- Seguridad general adicional ----------
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

if not DEBUG:
    # Solo se activan en producción real (detrás de HTTPS) para no romper
    # el entorno de desarrollo local.
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ---------- Archivos subidos (imágenes del foro) ----------
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
# Tamaño máximo de cada imagen del foro. Lo comprueba foro/views.py (auditoría I-6).
# El frontend (ForoPage.jsx) usa el mismo valor para avisar antes de publicar.
FORO_MAX_TAMANO_IMAGEN = 10 * 1024 * 1024
# DATA_UPLOAD_MAX_MEMORY_SIZE limita el cuerpo de la petición SIN contar los archivos,
# así que no sirve para limitar imágenes. Para FILE_UPLOAD_MAX_MEMORY_SIZE se deja el
# valor por defecto de Django (2,5 MB): los archivos más grandes van a disco temporal
# en vez de ocupar RAM.
# En producción, el servidor web debe cortar las peticiones enormes antes de que
# lleguen a Django (por ejemplo, en Nginx: client_max_body_size 60m;).
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# ---------- i18n ----------
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# ---------- Static ----------
STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
