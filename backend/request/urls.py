from django.urls import include, path
from request import views

urlpatterns = [
    path("export_request/", views.export_request, name="export_request"),
    path("import_request/", views.import_request, name="import_request"),
]
