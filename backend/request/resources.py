from django.utils.crypto import get_random_string
from import_export import fields, resources
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


from django.utils.crypto import get_random_string
from import_export import fields, resources
from import_export.widgets import ManyToManyWidget

from .models import Library, Request, Sample

# TODO: use BarcodeCounter instead of get_random_string, drop the import
# TODO: what about other fields from Libraries or Samples? like status
# TODO: this version imported each row as a new request...


class RequestResource(resources.ModelResource):
    libraries = fields.Field(
        column_name="libraries",
        attribute="libraries",
        widget=ManyToManyWidget(Library, field="name", separator=", "),
    )
    samples = fields.Field(
        column_name="samples",
        attribute="samples",
        widget=ManyToManyWidget(Sample, field="name", separator=", "),
    )

    class Meta:
        model = Request
        fields = (
            "name",
            "description",
            "libraries",
            "samples",
        )
        export_order = fields
        exclude = ("id", "user")
        import_id_fields = ["name"]
        use_bulk = True
        skip_unchanged = True

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def dehydrate_libraries(self, request):
        return ", ".join([library.name for library in request.libraries.all()])

    def dehydrate_samples(self, request):
        return ", ".join([sample.name for sample in request.samples.all()])

    def import_row(self, row, instance_loader, **kwargs):
        # Copied from parent class
        import_result = super().import_row(row, instance_loader, **kwargs)

        if import_result.import_type != import_result.IMPORT_TYPE_SKIP:
            instance = import_result.object_id
            if instance:
                # Set the user
                Request.objects.filter(id=instance).update(user=self.user)

                # Handle libraries and samples
                for field_name in ["libraries", "samples"]:
                    if field_name in row:
                        model = Library if field_name == "libraries" else Sample
                        names = row[field_name].split(", ")
                        related_objects = []

                        for name in names:
                            name = name.strip()
                            related_obj, created = model.objects.get_or_create(
                                name=name
                            )
                            if created:
                                # Set a barcode for new libraries or samples
                                related_obj.barcode = get_random_string(10).upper()
                                related_obj.save()
                            related_objects.append(related_obj)

                        # Set the related objects
                        getattr(Request.objects.get(id=instance), field_name).set(
                            related_objects
                        )

        return import_result

    def get_or_init_instance(self, instance_loader, row):
        instance, created = super().get_or_init_instance(instance_loader, row)

        if created:
            instance.user = self.user

        return instance, created
