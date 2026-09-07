from pathlib import Path
import os
import dj_database_url
import cloudinary
from dotenv import load_dotenv  

# =========================
# Cargar variables de entorno
# =========================
load_dotenv()

# =========================
# Rutas y claves
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("SECRET_KEY", "insecure-secret-key")
DEBUG = os.getenv("DEBUG", "False") == "True"

# =========================
# Hosts y seguridad
# =========================
if DEBUG:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1","192.168.100.2"]
    CSRF_TRUSTED_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
else:
    ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")
    CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")

# =========================
# Configuración de Cloudinary
# =========================
cloudinary.config(  
    cloud_name=os.getenv("CLOUD_NAME"), 
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET"),
    secure=True
)

# =========================
# Aplicaciones instaladas
# =========================
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "corsheaders",
    "rest_framework",
    "cloudinary",
    "tailwind",
    'apiApp',
    "theme"
]

# =========================
# Middleware
# =========================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# =========================
# Configuración de REST Framework
# =========================
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
    ]
}

# =========================
# URLs y WSGI
# =========================
ROOT_URLCONF = 'BackGobadyperu.urls'
WSGI_APPLICATION = 'BackGobadyperu.wsgi.application'

# =========================
# Templates
# =========================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# =========================
# Base de datos
# =========================
if DEBUG:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": dj_database_url.parse(os.getenv("DATABASE_URL"))
    }

# =========================
# Validación de contraseñas
# =========================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# =========================
# Internacionalización
# =========================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True

# =========================
# Archivos estáticos y media
# =========================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"

# ✅ CAMBIO: agregar STATICFILES_DIRS para que collectstatic encuentre el CSS de Tailwind
STATICFILES_DIRS = [
    BASE_DIR / "theme" / "static",
]

if not DEBUG:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =========================
# Otras configuraciones
# =========================
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").replace(" ", "").split(",")

# IA
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Cache para rate limiting
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'chatbot-cache',
    }
}

# TAILWIND
TAILWIND_APP_NAME = "theme"
NPM_BIN_PATH = r"npm.cmd"