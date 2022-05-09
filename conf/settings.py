"""
Django settings for LightsOff project.

Generated by 'django-admin startproject' using Django 4.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

from pathlib import Path
import environ
from celery.schedules import crontab
import os


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Create environment using django-environ
env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)

# Load environment variables for the environment and .env file,
# if available
environ.Env.read_env(BASE_DIR / ".env")

DEBUG = env("DEBUG")
SECRET_KEY = env("SECRET_KEY")
DOMAIN_NAME = env("DOMAIN_NAME")
ALLOWED_HOSTS = [DOMAIN_NAME]
CORS_ALLOWED_ORIGINS = env("FRONT_END_ORIGINS", default="http://localhost:3000").split(",")
# URL to API endpoint that provides data about power cutoff schedules
API_BASE_URL = env("API_BASE_URL")

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps and modules
    "anymail",
    "crispy_forms",
    "crispy_tailwind",
    # Local apps,
    "django_celery_beat",
    "rest_framework",
    "lightsoff.apps.LightsoffConfig",
    "rest_framework_api_key",
    "corsheaders",
    'django_extensions',
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
]

ROOT_URLCONF = "conf.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "conf.wsgi.application"

# Database
DATABASES = {
    # read os.environ['DATABASE_URL']
    "default": {'ENGINE': 'django.db.backends.postgresql',
                'NAME': env("DB_NAME"),
                'USER': env("DB_USER"),
                'PASSWORD': env("DB_PASSWORD"),
                'HOST': env("DB_HOST"),
                'PORT': env("DB_PORT", cast=int, default=5432),
            },
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Redis server to schedule tasks using Celery
CACHES = {
    "default": env.cache_url("REDIS_URL"),
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-lk"
TIME_ZONE = "Asia/Colombo"
USE_I18N = True
USE_TZ = False

# Static files
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "/static/"
STATICFILES_DIRS = (BASE_DIR / "static",)
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# anymail settings
ANYMAIL = {
    "MAILGUN_API_KEY": env("MAILGUN_API_KEY"),
    "MAILGUN_SENDER_DOMAIN": env("MAILGUN_SENDER_DOMAIN"),
}
EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")
SERVER_EMAIL = env("DEFAULT_FROM_EMAIL")

# Celery settings
BROKER_URL = env("REDIS_URL")
CELERY_RESULT_BACKEND = env("REDIS_URL")

CELERYBEAT_SCHEDULE = {
    # Task to pull updates from API hourly
    "scrapper_data": {
        "task": "lightsoff.tasks.scrapper_data",
        # Change pull frquency here
        "schedule": crontab(minute="*/10"),
    },
}

SMS_API_USERNAME = env("SMS_API_USERNAME")
SMS_API_PASSWORD = env("SMS_API_PASSWORD")

CELERYBEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

CELERY_TASK_PUBLISH_RETRY = env("SEND_SMS_MAX_RETRY", cast=int)
CELERY_IMPORTS = ("lightsoff.tasks",)
# django-crispy-forms settings
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"
OTP_NUM_DIGITS = env("OTP_NUM_DIGITS", cast=int)
OTP_EXPIRE_SECONDS = env("OTP_EXPIRE_SECONDS", cast=int)
LIGHT_OFF_API_KEY = env("LIGHT_OFF_API_KEY", default="")
DATA_UPLOAD_MAX_NUMBER_FIELDS = 20000

SMS_MASK_NAME = env("SMS_MASK_NAME", default="Ekata")

JAZZMIN_SETTINGS = {
    "copyright": "hfsl"
}
