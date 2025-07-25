import socket
import subprocess

from .base import *

DEBUG = True

INSTALLED_APPS += [
    "schema_viewer",
    # "debug_toolbar",
    "django_migration_linter",
    "corsheaders"   ,
    # "explorer",
]

MIDDLEWARE = [
    # "debug_toolbar.middleware.DebugToolbarMiddleware",
    *MIDDLEWARE,
    "corsheaders.middleware.CorsMiddleware",
]

INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]

hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS += [ip[: ip.rfind(".")] + ".1" for ip in ips]

# Additional support for Docker desktop on Windows/Mac
try:
    result = subprocess.run(
        ["hostname", "-I"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        docker_ips = result.stdout.strip().split()
        INTERNAL_IPS.extend(docker_ips)
except (subprocess.SubprocessError, FileNotFoundError):
    pass

additional_ips = os.environ.get("DEBUG_TOOLBAR_INTERNAL_IPS")
if additional_ips:
    INTERNAL_IPS.extend(ip.strip() for ip in additional_ips.split(","))


# CORS settings to enable API calls for Vue.js while development
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5174",
]

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda _: True,
    "SHOW_COLLAPSED": True,
    "SHOW_TEMPLATE_CONTEXT": True,
    "DISABLE_PANELS": set(),
    "RENDER_PANELS": False,
    "RESULTS_CACHE_SIZE": 100,
    "SQL_WARNING_THRESHOLD": 500,  # milliseconds
}

MIGRATION_LINTER_OPTIONS = {
    "no_cache": True,
}

READONLY_DATABASE_URL = os.environ.get(
    "READONLY_DATABASE_URL",
    "sqlite:////usr/src/db.sqlite",
)

DATABASES["readonly"] = dj_database_url.config(
    default=dj_database_url.parse(READONLY_DATABASE_URL),
    conn_max_age=1800,
    conn_health_checks=True,
)

EXPLORER_CONNECTIONS = {"Default": "readonly"}
EXPLORER_DEFAULT_CONNECTION = "readonly"

# this experiment was abandoned, before re-establishing do check lederboards...
# https://aider.chat/docs/leaderboards/by-release-date.html
# https://openrouter.ai/models?fmt=cards&max_price=0&order=top-weekly
EXPLORER_ASSISTANT_MODEL = {
    "name": "meta-llama/llama-3.1-8b-instruct:free",
    "max_tokens": 131072,
}

EXPLORER_ASSISTANT_BASE_URL = "https://openrouter.ai/api/v1"
EXPLORER_AI_API_KEY = os.environ.get("OPENROUTER_API_KEY", "aaaaaaaaaaaaaaa")

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
