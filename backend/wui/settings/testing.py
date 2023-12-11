from .base import *

## These are the same as in dev.py but without Django-debug-toolbar

DEBUG = True


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "authtools",
    "rest_framework",
    "django_admin_listfilter_dropdown",
    "django_extensions",
    "import_export",
    "django_linear_migrations",
    "common",
    "library_sample_shared",
    "library",
    "sample",
    "request",
    "incoming_libraries",
    "index_generator",
    "library_preparation",
    "pooling",
    "flowcell",
    "report",
    "invoicing",
    "usage",
    "stats",
    "metadata_exporter",
    "drf_spectacular",
    "corsheaders",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "extra.middleware.ErrorMiddleware",
]

MIGRATION_LINTER_OPTIONS = {
    "no_cache": True,
}

LOGGING["handlers"] = {
    "rich_console": {
        "class": "rich.logging.RichHandler",
        "formatter": "rich",
        "level": "DEBUG",
        "rich_tracebacks": True,
        "tracebacks_show_locals": True,
    },
}

LOGGING["loggers"] = {
    "django.request": {
        "handlers": ["rich_console"],
        "level": "ERROR",
        "propagate": True,
    },
    "django": {
        "handlers": ["rich_console"],
        "propagate": False,
    },
    "django.db.backends": {
        "handlers": ["rich_console"],
        "propagate": False,
    },
    "db": {
        "handlers": ["rich_console"],
    },
}

## These are the same as in prod.py

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
    "rest_framework.renderers.JSONRenderer",
]

NOTEBOOK_ARGUMENTS += [
    "--ip",
    "0.0.0.0",
    "--allow-root",
]

# CORS settings to enable API calls for Vue.js while development
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5174",
]
