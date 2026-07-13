from django.conf import settings


def instance_info(request):
    return {
        "INSTANCE_NAME": settings.INSTANCE_NAME,
        "INSTANCE_VERSION": settings.INSTANCE_VERSION,
        "INSTANCE_TITLE": settings.INSTANCE_TITLE,
    }
