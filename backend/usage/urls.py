from django.urls import re_path

from . import views

urlpatterns = [
    re_path("records/", views.RecordsUsage.as_view(), name="records-usage"),
    re_path(
        "organizations/",
        views.OrganizationsUsage.as_view(),
        name="organizations-usage",
    ),
    re_path(
        "principal_investigators/",
        views.PrincipalInvestigatorsUsage.as_view(),
        name="principal-investigators--usage",
    ),
    re_path(
        "analysis_types/",
        views.AnalysisTypesUsage.as_view(),
        name="analysis-types-usage",
    ),
]
