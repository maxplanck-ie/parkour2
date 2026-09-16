from .prod import *

DEMO_MODE = True

# A bare Fly Machine has no fronting Caddy container the way the docker-compose
# deploy does, so gunicorn serves collectstatic output directly via whitenoise.
MIDDLEWARE = list(MIDDLEWARE)
MIDDLEWARE.insert(
    MIDDLEWARE.index("django.middleware.security.SecurityMiddleware") + 1,
    "whitenoise.middleware.WhiteNoiseMiddleware",
)
# base.py/prod.py never set STORAGES, so it's only Django's implicit global
# default -- not a name `from .prod import *` actually re-exports. Spell it out.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

# Fixture staff user (backend/common/fixtures/user.json, pk=2) that every request
# gets auto-authenticated as. Overridable so a different demo dataset can point
# at a different fixture user without a code change.
DEMO_STAFF_USER_EMAIL = os.environ.get("DEMO_STAFF_USER_EMAIL", "staff@omics.dev")

_auth_middleware_index = MIDDLEWARE.index(
    "django.contrib.auth.middleware.AuthenticationMiddleware"
)
MIDDLEWARE.insert(
    _auth_middleware_index + 1, "common.middleware.DemoAutoLoginMiddleware"
)
