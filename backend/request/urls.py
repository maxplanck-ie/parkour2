from django.urls import path
from request.views import approve_request_redirect

urlpatterns = [
    path("approve_request_redirect", approve_request_redirect, name="approve_request_redirect"),
]
