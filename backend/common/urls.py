from common import models, views
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.urls import include, path, reverse_lazy
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(
    r"libraries-and-samples-templates",
    views.LibrariesAndSamplesTemplateViewSet,
    basename="libraries_and_samples_template",
)

router.register(
    r"incoming-libraries-samples-templates",
    views.IncomingLibrariesSamplesTemplateViewSet,
    basename="incoming_libraries_samples_template",
)

router.register(
    r"library-preparation-templates",
    views.LibraryPreparationTemplateViewSet,
    basename="library_preparation_template",
)

router.register(
    r"pooling-templates",
    views.PoolingTemplateViewSet,
    basename="pooling_template",
)

router.register(
    r"load-flowcells-templates",
    views.LoadFlowcellsTemplateViewSet,
    basename="load_flowcells_template",
)

router.register(
    r"run-statistics-templates",
    views.RunStatisticsTemplateViewSet,
    basename="run_statistics_template",
)

router.register(
    r"sequences-statistics-templates",
    views.SequencesStatisticsTemplateViewSet,
    basename="sequences_statistics_template",
)

router.register(
    r"invoicing-templates",
    views.InvoicingTemplateViewSet,
    basename="invoicing_template",
)

urlpatterns = [
    path("", views.index, name="index"),
    path("get_navigation_tree/", views.get_navigation_tree, name="get_navigation_tree"),
    path("media/<path:url_path>", views.protected_media, name="protected_media"),
    path(
        "login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"
    ),
    path("api_user_details", views.user_details, name="user_details"),
    path("danke", views.danke, name="danke"),
    path("logout/", auth_views.LogoutView.as_view(next_page="/"), name="logout"),
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            success_url=reverse_lazy("password_reset_done"),
            from_email=settings.SERVER_EMAIL,
            subject_template_name="email/password_reset_subject.txt",
            email_template_name="email/password_reset_email.txt",
            html_email_template_name="email/password_reset_email.html",
        ),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "password_reset/<uidb64>/<token>/",
        views.PasswordSetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
            success_url=reverse_lazy("password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "password_reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path("api/", include(router.urls)),
]
