from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.defaults import page_not_found, server_error

from .api import router

urlpatterns = [
    re_path("admin/", admin.site.urls),
    #   url("accounts/", include("authtools.urls")),
    re_path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    re_path("api/", include(router.urls)),
    re_path("api/usage/", include("usage.urls")),
    re_path("", include("common.urls")),
    re_path("", include("report.urls")),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
