from import_export import resources
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
