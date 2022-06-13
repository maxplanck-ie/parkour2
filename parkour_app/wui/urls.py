"""wui URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.views.defaults import page_not_found, server_error
from .api import router


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/', include('authtools.urls')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/', include(router.urls)),
    url(r'^api/usage/', include('usage.urls')),

    url(r'', include('common.urls')),
    url(r'', include('report.urls')),
]

if settings.DEBUG:
    # import debug_toolbar

    urlpatterns += [
        url(r'^404/$', page_not_found, kwargs={'exception': Exception('Page not Found')}),
        url(r'^500/$', server_error),
        # url(r'^__debug__/', include(debug_toolbar.urls)),
    ]

    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT,
    )
