from pathlib import Path
from decouple import config  # type: ignore[import-untyped]
import os

BASE_DIR = Path(__file__).resolve().parent.parent

FRONTEND_DIST = Path(
    os.environ.get(
        'FIRECAT_FRONTEND_DIST',
        str(BASE_DIR.parent / 'frontend' / 'dist')
    )
)

SECRET_KEY    = config('SECRET_KEY', default='django-insecure-change-in-production')
DEBUG         = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'apps.preferences',
    'apps.bookmarks',
    'apps.history',
    'apps.search',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'firecat_project.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [str(FRONTEND_DIST)],
    'APP_DIRS': False,
    'OPTIONS': {
        'loaders': [
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        ],
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]

WSGI_APPLICATION = 'firecat_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME':   BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'UTC'
USE_I18N      = True
USE_TZ        = True

STATIC_URL         = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SESSION_ENGINE          = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE      = 60 * 60 * 24 * 30

X_FRAME_OPTIONS = 'ALLOWALL'

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES':       ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_PARSER_CLASSES':         ['rest_framework.parsers.JSONParser'],
    'DEFAULT_AUTHENTICATION_CLASSES': ['firecat_project.authentication.CsrfExemptSessionAuthentication'],
    'DEFAULT_PERMISSION_CLASSES':     ['rest_framework.permissions.AllowAny'],
}

CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8765',
    'http://localhost:8765',
    'http://127.0.0.1:5173',
    'http://localhost:5173',
]

CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:5173,http://127.0.0.1:5173'
).split(',')
CORS_ALLOW_CREDENTIALS = True

# Cache — uses locmem in dev; swap for Redis in prod via CACHE_URL env var
_CACHE_URL = config('CACHE_URL', default='')
if _CACHE_URL:
    CACHES = {
        'default': {
            'BACKEND':  'django.core.cache.backends.redis.RedisCache',
            'LOCATION': _CACHE_URL,
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND':  'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'firecat-search-cache',
            'OPTIONS':  {'MAX_ENTRIES': 500},
        }
    }

# Required for StreamingHttpResponse to work correctly with Django's dev server
# When behind a proxy/nginx, ensure proxy_buffering is off for /api/search/
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB