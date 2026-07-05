"""Django settings for restoran project."""

from pathlib import Path
import os
import sys
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


def env_list(name, default=''):
    value = os.environ.get(name, default)
    return [item.strip() for item in value.split(',') if item.strip()]


def with_https(domain):
    if not domain:
        return None
    if domain.startswith(('http://', 'https://')):
        return domain
    return f'https://{domain}'


IS_RAILWAY = bool(os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_PUBLIC_DOMAIN'))
IS_RENDER = bool(os.environ.get('RENDER') or os.environ.get('RENDER_EXTERNAL_URL'))

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-restoran-pos-system-secret-key')

DEBUG = os.environ.get('DEBUG', 'False' if (IS_RAILWAY or IS_RENDER) else 'True').lower() in ('1', 'true', 'yes', 'on')
TESTING = 'test' in sys.argv

ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', '*')

RAILWAY_PUBLIC_DOMAIN = with_https(os.environ.get('RAILWAY_PUBLIC_DOMAIN'))
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL', '')

CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(env_list(
    'CSRF_TRUSTED_ORIGINS',
    'https://*.up.railway.app,https://restoranpos-production.up.railway.app,https://*.onrender.com',
) + ([RAILWAY_PUBLIC_DOMAIN] if RAILWAY_PUBLIC_DOMAIN else []) + ([RENDER_EXTERNAL_URL] if RENDER_EXTERNAL_URL else [])))

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'pos',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'restoran.urls'


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


WSGI_APPLICATION = 'restoran.wsgi.application'


# Database configuration - supports both SQLite and PostgreSQL
if os.environ.get('DATABASE_URL'):
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(conn_max_age=600, conn_health_checks=True)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


LANGUAGE_CODE = 'uz'

TIME_ZONE = 'Asia/Tashkent'

USE_I18N = True

USE_TZ = True


# ===================== STATIC FILES =====================

STATIC_URL = '/static/'

STATICFILES_DIRS = [BASE_DIR / 'pos/static']

STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': (
            'django.contrib.staticfiles.storage.StaticFilesStorage'
            if DEBUG or TESTING
            else 'whitenoise.storage.CompressedStaticFilesStorage'
        ),
    },
}


# ===================== DEFAULT =====================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ===================== LOGIN =====================

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'
