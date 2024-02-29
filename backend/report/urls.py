from django.urls import re_path
from report import views

urlpatterns = [
    # disabled becaused it can be accessed at api/usage/report
    # re_path("report/", views.report, name="report"),
    re_path("db/", views.database, name="database"),
    # re_path("db_data/", views.database_data, name="database-data"),
]
