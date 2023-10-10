from common import models, views
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.urls import include, path
from neapolitan.views import CRUDView

urlpatterns = [
    path("", views.index, name="index"),
    path("get_navigation_tree/", views.get_navigation_tree, name="get_navigation_tree"),
    path("media/<path:url_path>", views.protected_media, name="protected_media"),
    path(
        "login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"
    ),
    path("logout/", auth_views.LogoutView.as_view(next_page="/"), name="logout"),
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            success_url="/password_reset/done/",
            from_email=settings.SERVER_EMAIL,
            subject_template_name="email/password_reset_subject.txt",
            email_template_name="email/password_reset_email.html",
        ),
        name="password_reset",
    ),
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view()),
    path(
        "password_reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(success_url="/login/"),
        name="password_reset_confirm",
    ),
]


class DutyView(CRUDView):
    model = models.Duty
    fields = [
        "main_name",
        "backup_name",
        "start_date",
        "end_date",
        "facility",
        "platform",
        "comment",
    ]
    filterset_fields = ["archived"]


urlpatterns += DutyView.get_urls()
