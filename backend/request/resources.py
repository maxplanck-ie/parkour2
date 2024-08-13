from django.db import transaction
from django.utils import timezone
from django.utils.crypto import get_random_string
from import_export import fields, resources
from import_export.results import RowResult
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget
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


# TODO: use BarcodeCounter instead of get_random_string, drop the import
# TODO: what about other fields from Libraries or Samples? like status
class RequestResource(resources.ModelResource):
    record_type = fields.Field(column_name="record_type")

    class Meta:
        model = Request
        fields = (
            "name",
            "description",
        )
        export_order = fields
        exclude = ("id", "user")
        import_id_fields = ["name"]
        use_bulk = True
        skip_unchanged = True

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.request_instance = None
        self.libraries_resource = LibrariesResource()
        self.samples_resource = SamplesResource()

    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        if not dry_run and self.request_instance is None:
            self.request_instance = Request.objects.create(
                name=f"Imported Request {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}",
                user=self.user,
                description="Imported NET-CAGE Request",
            )

    def import_row(self, row, instance_loader, **kwargs):
        if self.request_instance is None:
            self.before_import(None, False, False)

        row_result = RowResult()
        row_result.import_type = RowResult.IMPORT_TYPE_UPDATE
        row_result.object_id = self.request_instance.pk
        row_result.object_repr = str(self.request_instance)

        record_type = row.get("record_type", "").upper()
        if record_type not in ["L", "S"]:
            row_result.errors.append(f"Invalid record_type: {record_type}")
            return row_result

        if record_type == "L":
            resource = self.libraries_resource
            relation = self.request_instance.libraries
        else:
            resource = self.samples_resource
            relation = self.request_instance.samples

        # Use the appropriate resource to import the row
        import_result = resource.import_row(row, instance_loader, **kwargs)

        if import_result.import_type != import_result.IMPORT_TYPE_SKIP:
            record = import_result.object_id
            if record:
                relation.add(record)

        self.request_instance.save()

        return row_result

    def get_or_init_instance(self, instance_loader, row):
        return self.request_instance, False

    def save_instance(self, instance, using_transactions=True, dry_run=False):
        if not dry_run:
            instance.save()
