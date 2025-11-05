from django.apps import apps

from common.utils import retrieve_group_items

Request = apps.get_model("request", "Request")


def get_accessible_requests(django_request):
    queryset = Request.objects.filter(archived=False)
    if django_request.user.is_staff:
        return queryset
    if getattr(django_request.user, "is_pi", False):
        return retrieve_group_items(django_request, queryset)
    return queryset.filter(user=django_request.user)

