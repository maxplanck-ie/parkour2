import os

import dj_database_url

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__),
        )
    )
)

LOG_DIR = os.path.join(BASE_DIR, "logs")

# Make sure the 'logs' directory exists. If not, create it
try:
    os.makedirs(LOG_DIR)
except OSError:
    pass

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

SECRET_KEY = os.environ.get("SECRET_KEY", "94e9206c6a0ac99409aa")


# Allow all host headers
ALLOWED_HOSTS = ["*"]

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"

# Fix FileUpload
X_FRAME_OPTIONS = "SAMEORIGIN"


# CSRF cookie
CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS")
CSRF_TRUSTED_ORIGINS = (
    CSRF_TRUSTED_ORIGINS.split(",") if CSRF_TRUSTED_ORIGINS is not None else []
)


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
    'constance',
    'constance.backends.database',
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
    'mozilla_django_oidc',
    "drf_spectacular",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "extra.middleware.ErrorMiddleware",
    'mozilla_django_oidc.middleware.SessionRefresh',
]

AUTHENTICATION_BACKENDS = [
    'common.oidc.ParkourOIDCAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
]

ROOT_URLCONF = "wui.urls"

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
            "debug": True,
        },
    },
]

WSGI_APPLICATION = "wui.wsgi.application"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

# SQLite is fallback option if no DATABASE_URL env-var is found by the extension
DATABASES = {
    "default": dj_database_url.config(
        default="sqlite:////usr/src/db.sqlite",
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 12,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
    {
        'NAME': 'wui.password_validators.CapitalSymbolPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = os.environ.get("TIME_ZONE", "CET")
USE_I18N = True
USE_TZ = True


ADMINS = [
    (
        os.environ.get("ADMIN_NAME", "ParkourAdmin"),
        os.environ.get("ADMIN_EMAIL", "admin@mail.server.tld"),
    ),
]


AUTH_USER_MODEL = "common.User"  # authtools


# Email config
EMAIL_HOST = os.environ.get("EMAIL_HOST", "mail.server.tld")
EMAIL_SUBJECT_PREFIX = os.environ.get("EMAIL_SUBJECT_PREFIX", "[Parkour2]")
SERVER_EMAIL = os.environ.get("SERVER_EMAIL", "something@server.tld")


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {
        "simple": {
            "format": "[%(levelname)s] [%(asctime)s] %(message)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
        "verbose": {
            "format": "[%(levelname)s] [%(asctime)s] [%(pathname)s:%(lineno)s]: %(funcName)s(): %(message)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
        "rich": {"datefmt": "[%d-%b %X]"},
    },
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            # 'class': 'django.utils.log.AdminEmailHandler'
            "class": "common.logger.CustomAdminEmailHandler",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "logfile": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "django.log"),
            "formatter": "verbose",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 2,
            "delay": True,
        },
        "dblogfile": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "db.log"),
            "formatter": "verbose",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 2,
            "delay": True,
        },
    },
}

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = "/static/"

STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

MEDIA_URL = "/media/"

MEDIA_ROOT = os.path.join(BASE_DIR, "media")

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "SEARCH_PARAM": "query",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Parkour",
    "DESCRIPTION": "Quickly jump to that information that you need!",
    "VERSION": "2",
    "SERVE_INCLUDE_SCHEMA": False,
    # OTHER SETTINGS
}

# Use plain Python by default for shell_plus
SHELL_PLUS = "plain"

NOTEBOOK_ARGUMENTS = [
    "--notebook-dir",
    os.path.join(BASE_DIR, "notebooks"),
]

IPYTHON_ARGUMENTS = [
    "--debug",
]


# Admin user defaults

SETUP_ADMIN_EMAIL = os.environ.get("SETUP_ADMIN_EMAIL", "")
SETUP_ADMIN_PASSWORD = os.environ.get("SETUP_ADMIN_PASSWORD", None)

# OIDC
OIDC_RP_CLIENT_ID = os.environ["OIDC_RP_CLIENT_ID"]
OIDC_RP_CLIENT_SECRET = os.environ["OIDC_RP_CLIENT_SECRET"]
OIDC_RP_SIGN_ALGO = os.environ["OIDC_RP_SIGN_ALGO"]
OIDC_OP_JWKS_ENDPOINT = os.environ["OIDC_OP_JWKS_ENDPOINT"]
OIDC_OP_AUTHORIZATION_ENDPOINT = os.environ["OIDC_OP_AUTHORIZATION_ENDPOINT"]
OIDC_OP_TOKEN_ENDPOINT = os.environ["OIDC_OP_TOKEN_ENDPOINT"]
OIDC_OP_USER_ENDPOINT = os.environ["OIDC_OP_USER_ENDPOINT"]
OIDC_RP_SCOPES = 'openid email name groups'
OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS = 86400 # 24 h

OIDC_ALLOWED_GROUPS = os.environ.get("OIDC_ALLOWED_GROUPS", '')
OIDC_GENOMICSCF_GROUPS = os.environ.get("OIDC_GENOMICSCF_GROUPS", '')
OIDC_BIOINFOCF_GROUPS = os.environ.get("OIDC_BIOINFOCF_GROUPS", '')
OIDC_ALLOWED_USER_EMAILS = os.environ.get("OIDC_ALLOWED_USER_EMAILS", '')

# Costance
STAFF_EMAIL_ADDRESS = os.environ.get("STAFF_EMAIL_ADDRESS", '')
DOCUMENTATION_URL = os.environ.get("DOCUMENTATION_URL", '')
GRID_INTRO_VIDEO_URL = os.environ.get("GRID_INTRO_VIDEO_URL", '')
CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'
CONSTANCE_SUPERUSER_ONLY = True
CONSTANCE_CONFIG = {'STAFF_EMAIL_ADDRESS': (STAFF_EMAIL_ADDRESS,
                                            'Shared email address of the the genomics laboratory',
                                            str),
                    'OIDC_ALLOWED_GROUPS': (OIDC_ALLOWED_GROUPS,
                                            'Comma-separated list of LDAP group(s) that are allowed to log in Parkour. '
                                            'Lower case, no spaces',
                                            str),
                    'OIDC_ALLOWED_USER_EMAILS': (OIDC_ALLOWED_USER_EMAILS,
                                            'Comma-separated list of email addresses that are allowed to log in Parkour. '
                                            'Lower case, no spaces',
                                            str),
                    'OIDC_GENOMICSCF_GROUPS': (OIDC_GENOMICSCF_GROUPS,
                                               'Comma-separated list of LDAP group(s) for staff of the genomics laboratory. '
                                               'Lower case, no spaces',
                                               str),
                    'OIDC_BIOINFOCF_GROUPS': (OIDC_BIOINFOCF_GROUPS,
                                              'Comma-separated list of LDAP group(s) for staff of the bioinformatics group. '
                                              'Lower case, no spaces',
                                              str),
                    'DOCUMENTATION_URL': (DOCUMENTATION_URL,
                                          "Link for Parkour's manual",
                                          str),
                    'GRID_INTRO_VIDEO_URL': (GRID_INTRO_VIDEO_URL,
                                             "Link for the video introduction to Parkour's grid",
                                             str)}

# Facilities
DEEPSEQ = 'Genomics-CF'
BIOINFO = 'Bioinfo-CF'
