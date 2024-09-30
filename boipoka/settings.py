"""
Django settings for boipoka project.

Generated by 'django-admin startproject' using Django 5.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""
import os 
import django_heroku
import dj_database_url
from pathlib import Path
from decouple import config
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG',default=False,cast=bool)

ALLOWED_HOSTS = ['boipokalibrarymangement-production.up.railway.app','localhost', '127.0.0.1']

CSRF_TRUSTED_ORIGINS = ['https://boipokalibrarymangement-production.up.railway.app']

LOGIN_URL='/login/'
LOGIN_REDIRECT_URL='/book_list/'
LOGOUT_REDIRECT_URL='/'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'boipoka_app',
    'tailwind',
    'theme'
]

TAILWIND_APP_NAME='theme'

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

ROOT_URLCONF = 'boipoka.urls'

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

WSGI_APPLICATION = 'boipoka.wsgi.application'

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_PORT = 587
EMAIL_HOST_USER = "apikey"  # Use 'apikey' as the username
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD') # Your SendGrid API Key
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = "fahadish861@gmail.com"
# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

if DEBUG:
    

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'postgres',  # Database name you created
            'USER': 'postgres',       # Username you created or 'postgres'
            'PASSWORD': 'admin',   # Password for the user
            'HOST': 'localhost',           # Or the IP address of your PostgreSQL server (default: localhost)
            'PORT': '5432',     
        }
    }
    
    
    
else: 
    DATABASES ={
        'default': dj_database_url.config(default=config('DATABASE_URL'))
    # 'default': {
    #     'ENGINE': 'django.db.backends.postgresql',
    #     'NAME': 'railway',  # Database name you created
    #     'USER': 'postgres',       # Username you created or 'postgres'
    #     'PASSWORD': 'xpFpntIAtcXRaFKdhkChyGSNUKQpFGHA',   # Password for the user
    #     'HOST': 'postgres-j0ir.railway.internal',           # Or the IP address of your PostgreSQL server (default: localhost)
    #     'PORT': '5432',     
    # }
}

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

# TIME_ZONE = 'UTC'

USE_I18N = True


USE_TZ = True  # Make sure this is set to True
TIME_ZONE = 'Asia/Dhaka'  # e.g., 'Asia/Dhaka'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL='media/'
MEDIA_ROOT=BASE_DIR/'media'
# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

GOOGLE_BOOKS_API_KEY = config('GOOGLE_BOOKS_API_KEY')


django_heroku.settings(locals())