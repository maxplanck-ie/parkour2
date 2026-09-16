import os

from django.conf import settings
from django.http import HttpResponse
from django.urls import re_path

from .urls import urlpatterns


# Demo-only: pk2_demo folds the Vue SPA's prod build (normally its own
# parkour2-vite + nginx-proxied container, see misc/nginx-server.conf) into
# this single Django process. WhiteNoise (WHITENOISE_ROOT, see demo.py)
# serves real built files under /vue/ (e.g. /vue/vue-assets/*.js) and passes
# through anything else, so this catch-all only ever answers a client-side
# vue-router path that isn't a real file on disk -- same as nginx's plain
# `proxy_pass http://frontend` behind `npx serve -s dist` did.
#
# Read lazily per-request, not at import time: CI's settings-validation step
# (`manage.py check` against config.settings.demo) never runs the frontend
# build, so the file doesn't exist there, and importing this module must
# still succeed.
def _vue_spa_fallback(request, **kwargs):
    with open(os.path.join(settings.WHITENOISE_ROOT, "vue", "index.html"), "rb") as f:
        return HttpResponse(f.read(), content_type="text/html")


urlpatterns = urlpatterns + [
    re_path(r"^vue/.*$", _vue_spa_fallback, name="vue-spa-fallback"),
]
