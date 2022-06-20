from django.conf.urls import url

from . import views

urlpatterns = [
    url("records/", views.RecordsUsage.as_view(), name="records-usage"),
    url(
        "organizations/",
        views.OrganizationsUsage.as_view(),
        name="organizations-usage",
    ),
    url(
        "principal_investigators/",
        views.PrincipalInvestigatorsUsage.as_view(),
        name="principal-investigators--usage",
    ),
    url(
        "library_types/",
        views.LibraryTypesUsage.as_view(),
        name="library-types-usage",
    ),
]
