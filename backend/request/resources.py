from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget
from library.models import Library
from sample.models import Sample

from .models import Request


class LibrariesResource(resources.ModelResource):
    class Meta:
        model = Library
        fields = (
            # "id",
            "name",
            # "barcode",
            "library_protocol",
            "library_type",
            "concentration",
            "mean_fragment_size",
            "index_type",
            "index_reads",
            "index_i7",
            "index_i5",
            "read_length",
            "sequencing_depth",
            "organism",
            "comments",
        )


class SamplesResource(resources.ModelResource):
    class Meta:
        model = Sample
        fields = (
            # "id",
            "name",
            # "barcode",
            "nucleic_acid_type",
            "library_protocol",
            "library_type",
            "concentration",
            "rna_quality",
            "read_length",
            "sequencing_depth",
            "organism",
            "comments",
        )


class RequestResource(resources.ModelResource):
    libraries = fields.Field(
        column_name="libraries",
        attribute="libraries",
        widget=ForeignKeyWidget(Library, "name"),
    )
    samples = fields.Field(
        column_name="samples",
        attribute="samples",
        widget=ForeignKeyWidget(Sample, "name"),
    )

    class Meta:
        model = Request
        fields = (
            "name",
            "description",
            "status",
            "libraries",
            "samples",
            # Add other fields from your Request model as needed
        )
        export_order = fields

    def dehydrate_libraries(self, request):
        return ", ".join([library.name for library in request.libraries.all()])

    def dehydrate_samples(self, request):
        return ", ".join([sample.name for sample in request.samples.all()])
