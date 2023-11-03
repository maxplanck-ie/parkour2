from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from .api import router

urlpatterns = [
    re_path("admin/", admin.site.urls),
    #   url("accounts/", include("authtools.urls")),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("api/", include(router.urls)),
    path("api/usage/", include("usage.urls")),
    path("", include("common.urls")),
    path("", include("report.urls")),
    path("openapi/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "openapi/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "openapi/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]

if settings.DEBUG:

    urlpatterns += [
        path("schema-viewer/", include("schema_viewer.urls")),
        path("__debug__/", include("debug_toolbar.urls")),
    ]
