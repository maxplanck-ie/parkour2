from .prod import *

DEMO_MODE = True

# Fixture staff user (backend/common/fixtures/user.json, pk=2) that every request
# gets auto-authenticated as. Overridable so a different demo dataset can point
# at a different fixture user without a code change.
DEMO_STAFF_USER_EMAIL = os.environ.get("DEMO_STAFF_USER_EMAIL", "staff@omics.dev")

MIDDLEWARE = list(MIDDLEWARE)
_auth_middleware_index = MIDDLEWARE.index(
    "django.contrib.auth.middleware.AuthenticationMiddleware"
)
MIDDLEWARE.insert(
    _auth_middleware_index + 1, "common.middleware.DemoAutoLoginMiddleware"
)
