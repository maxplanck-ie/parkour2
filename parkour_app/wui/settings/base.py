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

SECRET_KEY = os.environ["SECRET_KEY"]


# Allow all host headers
ALLOWED_HOSTS = ["*"]

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"

# Fix FileUpload
X_FRAME_OPTIONS = "SAMEORIGIN"


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
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
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

DATABASES = {"default": dj_database_url.config()}


# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = os.environ["TIME_ZONE"]
USE_I18N = True
USE_L10N = True
USE_TZ = True


ADMINS = [
    (os.environ["ADMIN_NAME"], os.environ["ADMIN_EMAIL"]),
]


AUTH_USER_MODEL = "common.User"  # authtools


# Email config
EMAIL_HOST = os.environ["EMAIL_HOST"]
EMAIL_SUBJECT_PREFIX = os.environ["EMAIL_SUBJECT_PREFIX"]
SERVER_EMAIL = os.environ["SERVER_EMAIL"]


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
            "maxBytes": 15 * 1024 * 1024,  # 15 MB
            "backupCount": 2,
        },
        "dblogfile": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "db.log"),
            "formatter": "verbose",
            "maxBytes": 15 * 1024 * 1024,
            "backupCount": 2,
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
FILES_PATH = os.path.join(BASE_DIR, MEDIA_ROOT, "files")

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "SEARCH_PARAM": "query",
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


# OBSOLETE/NON-OBSOLETE STATUS
NON_OBSOLETE = 1
OBSOLETE = 2

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
OIDC_GENOMICSCF_GROUPS= os.environ.get("OIDC_GENOMICSCF_GROUPS", '')
OIDC_BIOINFOCF_GROUPS= os.environ.get("OIDC_BIOINFOCF_GROUPS", '')

# Costance
CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'
CONSTANCE_SUPERUSER_ONLY = False
CONSTANCE_CONFIG = {'STAFF_EMAIL_ADDRESS': ('genomics@imb-mainz.de',
                                            'Shared email address of the the genomics laboratory',
                                            str),
                    'OIDC_ALLOWED_GROUPS': (OIDC_ALLOWED_GROUPS,
                                            'Comma-separated list of LDAP group(s) that are allowed to log in Parkour. '
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
                    'DOCUMENTATION_URL': ('https://gitlab.rlp.net/imbforge/parkour2/-/wikis/home',
                                          "Link for Parkour's manual",
                                          str),
                    'GRID_INTRO_VIDEO_URL': ('https://gitlab.rlp.net/imbforge/parkour2/-/wikis/home',
                                             "Link for the video introduction to Parkour's grid",
                                             str)}
