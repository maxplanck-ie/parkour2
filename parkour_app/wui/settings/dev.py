from .base import *

DEBUG = True

INSTALLED_APPS += [
    "debug_toolbar",
]

MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]


def show_toolbar_to_all_IPs(request):
    return True


DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": show_toolbar_to_all_IPs,
}

LOGGING["handlers"] = {
    "console": {
        "class": "rich.logging.RichHandler",
        "filters": ["require_debug_true"],
        "formatter": "rich",
        "level": "DEBUG",
        "rich_tracebacks": True,
        "tracebacks_show_locals": True,
    },
}

LOGGING["loggers"] = {
    "django.request": {
        "handlers": ["console"],
        "level": "ERROR",
        "propagate": True,
    },
    "django": {
        "handlers": ["console"],
        "propagate": False,
    },
    "django.db.backends": {
        "handlers": ["console"],
        "propagate": False,
    },
    "db": {
        "handlers": ["console"],
    },
}
