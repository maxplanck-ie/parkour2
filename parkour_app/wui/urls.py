from django.contrib import admin
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.views.defaults import page_not_found, server_error
from .api import router


urlpatterns = [
    url("admin/", admin.site.urls),
    url("accounts/", include("authtools.urls")),
    url("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    url("api/", include(router.urls)),
    url("api/usage/", include("usage.urls")),
    url("", include("common.urls")),
    url("", include("report.urls")),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        url("404/", page_not_found, kwargs={"exception": Exception("Page not Found")}),
        url("500/", server_error),
        url("__debug__/", include(debug_toolbar.urls)),
    ]

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
