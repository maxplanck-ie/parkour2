from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path

from .api import router

urlpatterns = [
    re_path("admin/", admin.site.urls),
    #   url("accounts/", include("authtools.urls")),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("api/", include(router.urls)),
    path("api/usage/", include("usage.urls")),
    path("", include("common.urls")),
    path("", include("report.urls")),
]

if settings.DEBUG:

    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
