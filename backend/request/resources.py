from import_export import resources
from library.models import Library
from sample.models import Sample

from .models import Request


class RequestResource(resources.ModelResource):
    class Meta:
        model = Request
