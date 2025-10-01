from pathlib import Path
import os
import dj_database_url
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv  
load_dotenv()


# Ruta principal del proyecto✅
BASE_DIR = Path(__file__).resolve().parent.parent
# Clave secreta del proyecto✅
SECRET_KEY = os.getenv("SECRET_KEY")
# Modo desarrollador ✅
DEBUG = os.getenv("DEBUG", "False") == "True"

# Hosts Permitidos  ⚠️
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")
CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")

# Cloudinary  - Django integrations
cloudinary.config(  
    cloud_name = os.getenv("CLOUD_NAME"), 
    api_key = os.getenv("API_KEY"),
    api_secret = os.getenv("API_SECRET")
)

# Definir aplicaciones
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "corsheaders",
    'apiApp',
    'rest_framework',
    'cloudinary',
       
]

# Middleware??
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

### para buscador no repetidos
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
    ]
}


# ???
ROOT_URLCONF = 'BackGobadyperu.urls'


# ???
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

WSGI_APPLICATION = 'BackGobadyperu.wsgi.application'


# La base de datos (ruta donde esta la base de datos y proveedor de base de datos)✅
DATABASES = {
    'default': dj_database_url.parse(os.getenv("DATABASE_URL"))
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Lima'

USE_I18N = True

USE_TZ = True


# Archivos estaticos
STATIC_URL = '/static/' 

# ???
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'  
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# IMAGENES
MEDIA_URL = '/media/' 
MEDIA_ROOT = BASE_DIR / 'media' 



CORS_ALLOW_ALL_ORIGINS = True 