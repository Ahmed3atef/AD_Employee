from pathlib import Path
from dotenv import load_dotenv
from .ad_conn import ADConnection
import os


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY")


DEBUG = True

ALLOWED_HOSTS = ['*']

CORS_ALLOWED_ORIGINS = [
    'http://localhost:8000',
    'http://172.0.0.1:8000'
]

# CORS_ALLOW_ALL_ORIGINS = True

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'corsheaders',
    # my apps
    'core',
    'employee',
]


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

if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = [
        '127.0.0.1',
    ]

ROOT_URLCONF = 'ADIWA.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'frontend/templates')],
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

WSGI_APPLICATION = 'ADIWA.wsgi.application'



DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE'),
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),  
        'PORT': os.getenv('DB_PORT'),
        'OPTIONS': {
            'driver': 'ODBC Driver 18 for SQL Server',
            'extra_params': 'TrustServerCertificate=yes;',
        },
    }
}

SERVER_HOST = os.getenv('AD_SERVER')  
DOMAIN = os.getenv('AD_DOMAIN')
BASE_DN = os.getenv('AD_BASE_DN')
CONTAINER_DN_BASE = os.getenv('AD_CONTAINER_DN_BASE')

ACTIVE_DIR = ADConnection(
    server_host=SERVER_HOST,
    domain=DOMAIN,
    base_dn=BASE_DN,
    base_container=CONTAINER_DN_BASE,
)

CACHES = {
    'default':{
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }   
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

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'frontend/static'),
]

STATIC_ROOT = BASE_DIR / 'staticfiles'

# SESSION_ENGINE = 'django.contrib.sessions.backends.db'
# SESSION_COOKIE_HTTPONLY = True
# SESSION_COOKIE_SECURE = False  # HTTPS only
# SESSION_SAVE_EVERY_REQUEST = False



DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'core.User'

AUTHENTICATION_BACKENDS = [
    'core.auth_backends.ActiveDirectoryBackend',
    'django.contrib.auth.backends.ModelBackend',   
]


JAZZMIN_SETTINGS = {
    'site_title': 'AD Web App',
    'site_header': 'AD Web App',
    'site_brand': 'AD Web App',
    
    "custom_links": {
        "employee": [  
            {
                "name": "Transfer OU", 
                "url": "admin:transfer_ou_page",  
                "icon": "fas fa-exchange-alt", 
                "permissions": ["employee.view_employee"]
            },
        ],
    },
    
    "show_sidebar": True,
}


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'COERCE_DECIMAL_TO_STRING': False,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'AD Web App API',
    'DESCRIPTION': 'AD Web App API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}