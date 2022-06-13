from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^records/$', views.RecordsUsage.as_view(), name='records-usage'),
    url(r'^organizations/$', views.OrganizationsUsage.as_view(), name='organizations-usage'),
    url(r'^principal_investigators/$', views.PrincipalInvestigatorsUsage.as_view(), name='principal-investigators--usage'),
    url(r'^library_types/$', views.LibraryTypesUsage.as_view(), name='library-types-usage'),
]
