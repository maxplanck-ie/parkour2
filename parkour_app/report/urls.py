from django.conf.urls import url
from report import views


urlpatterns = [
    url("report/", views.report, name="report"),
    url("db/", views.database, name="database"),
    url("db_data/", views.database_data, name="database-data"),
]
