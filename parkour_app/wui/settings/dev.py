from .base import *

DEBUG = True

INSTALLED_APPS += [
    "debug_toolbar",
    "django_linear_migrations",
    "django_migration_linter",
]

MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]


def show_toolbar_to_all_IPs(request):
    return True


DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": show_toolbar_to_all_IPs,
}

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

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.history.HistoryPanel',
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
]