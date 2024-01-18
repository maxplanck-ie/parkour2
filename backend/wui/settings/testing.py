from .base import *

DEBUG = True

## These are the same as in prod.py

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
    "rest_framework.renderers.JSONRenderer",
]

NOTEBOOK_ARGUMENTS += [
    "--ip",
    "0.0.0.0",
    "--allow-root",
]

## These are the same as in dev.py BUT without Django-debug-toolbar

INSTALLED_APPS += [
    "schema_viewer",
    "django_migration_linter",
    "corsheaders",
]

MIDDLEWARE += [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]


# CORS settings to enable API calls for Vue.js while development
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5174",
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
