import warnings

## Suppress warnings that are expected/known in the test environment:
## - RuntimeWarning: naive datetime when time zone support is active (test
##   fixtures intentionally use naive datetimes).
## - DeprecationWarning from fpdf2 (arial font substitution, deprecated `ln`
##   cell parameter).
## Must be set BEFORE any Django apps are loaded (before base import).
warnings.filterwarnings(
    "ignore", category=RuntimeWarning, message=".*received a naive datetime.*"
)
warnings.filterwarnings(
    "ignore", category=DeprecationWarning, message=".*Substituting font.*"
)
warnings.filterwarnings(
    "ignore", category=DeprecationWarning, message='.*parameter "ln" is deprecated.*'
)

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
]

MIDDLEWARE += [
    "django.middleware.common.CommonMiddleware",
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
        "handlers": [],
        "level": "ERROR",
        "propagate": False,
    },
    "django": {
        "handlers": [],
        "propagate": False,
    },
    "django.db.backends": {
        "handlers": [],
        "propagate": False,
    },
    "db": {
        "handlers": [],
    },
    "requests.packages.urllib3": {
        "handlers": [],
        "level": "ERROR",
        "propagate": False,
    },
    "fPDF": {
        "handlers": [],
        "level": "ERROR",
        "propagate": False,
    },
}
