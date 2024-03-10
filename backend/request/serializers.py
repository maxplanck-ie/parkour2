from django.conf import settings
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer, SerializerMethodField, CharField
from django.utils.encoding import force_str
import os
import re

from .models import FileRequest, Request


class RequestSerializer(ModelSerializer):
    user_full_name = SerializerMethodField()
    pi_name = SerializerMethodField()
    bioinformatician_name = SerializerMethodField()
    handler_name = SerializerMethodField()
    pool_size_user_name = SerializerMethodField()
    cost_unit_name = SerializerMethodField()
    restrict_permissions = SerializerMethodField()
    deep_seq_request_name = SerializerMethodField()
    deep_seq_request_path = SerializerMethodField()
    approval_user_name = SerializerMethodField()
    completed = SerializerMethodField()
    files = SerializerMethodField()
    number_of_samples = SerializerMethodField()
    description = CharField(allow_blank=True)

    class Meta:
        model = Request
        fields = (
            "pk",
            "name",
            "user",
            "user_full_name",
            "pi",
            "pi_name",
            "bioinformatician",
            "bioinformatician_name",
            "handler",
            "handler_name",
            "pool_size_user",
            "pool_size_user_name",
            "create_time",
            "cost_unit",
            "cost_unit_name",
            "description",
            "pooled_libraries",
            "pooled_libraries_concentration_user",
            "pooled_libraries_volume_user",
            "pooled_libraries_fragment_size_user",
            "total_sequencing_depth",
            "restrict_permissions",
            "completed",
            "deep_seq_request_name",
            "deep_seq_request_path",
            "approval_user_name",
            "approval_time",
            "files",
            "sequenced",
            "invoice_date",
            "number_of_samples",
            "filepaths",
        )

    def get_user_full_name(self, obj):
        return obj.user.full_name

    def get_pi_name(self, obj):
        return str(obj.pi)
    
    def get_bioinformatician_name(self, obj):
        return str(obj.bioinformatician)

    def get_handler_name(self, obj):
        return str(obj.handler) if obj.handler else None

    def get_pool_size_user_name(self, obj):
        return str(obj.pool_size_user)

    def get_cost_unit_name(self, obj):
        return obj.cost_unit.name if obj.cost_unit else 'None'

    def get_number_of_samples(self, obj):
        return len(obj.statuses)

    def get_restrict_permissions(self, obj):
        """
        Don't allow the users to modify the requests and libraries/samples
        if they have reached status 1 or higher (or failed).
        """
        return True if not (obj.user.is_staff or obj.user.member_of_bcf) and (obj.statuses.count(0) == 0 and obj.approval_time) else False

    def get_completed(self, obj):
        """Return True if request's libraries and samples are sequenced."""
        return obj.statuses.count(6) > 0

    def get_deep_seq_request_name(self, obj):
        return obj.deep_seq_request.name.split("/")[-1] if obj.deep_seq_request else ""

    def get_deep_seq_request_path(self, obj):
        return (
            settings.MEDIA_URL + obj.deep_seq_request.name
            if obj.deep_seq_request
            else ""
        )

    def get_approval_user_name(self, obj):
        return str(obj.approval_user)

    def get_files(self, obj):
        files = [
            {
                "pk": file.pk,
                "name": file.name.split("/")[-1],
                "path": settings.MEDIA_URL + file.file.name,
            }
            for file in obj.files.all()
        ]
        return files

    def to_internal_value(self, data):
        internal_value = super().to_internal_value(data)

        records = data.get("records", [])
        # Disable checking if libraries/samples are present for now, NZ
        # if not records:
        #     raise ValidationError(
        #         {
        #             "records": ["No libraries or samples are provided."],
        #         }
        #     )

        files = data.get("files", [])

        libraries = []
        samples = []
        for obj in records:
            if obj["record_type"] == "Library":
                libraries.append(int(obj["pk"]))
            elif obj["record_type"] == "Sample":
                samples.append(int(obj["pk"]))

        internal_value.update(
            {
                "libraries": libraries,
                "samples": samples,
                "files": files,
            }
        )

        return internal_value

    def rename_files(self, instance):

        """Add LIMS ID to a request file name"""

        for request_file in instance.files.all().exclude(name__regex=r'^LIMS-[1-9]{1}[0-9]*_'):

            file_field = getattr(request_file, 'file')
            
            if file_field:

                file_name = force_str(file_field)
                file_basename = os.path.basename(file_name)
                file_dirname = os.path.dirname(file_name)

                # Create new file name
                new_file_basename = f'LIMS-{instance.pk}_{file_basename}'
                new_file_name = os.path.join(file_dirname, new_file_basename)

                # Essentially, rename file
                if file_name != new_file_name:
                    # file_field.storage.delete(new_file_name)
                    new_file_name = file_field.storage.save(new_file_name, file_field)
                    new_file_basename = os.path.basename(new_file_name)
                    file_field.close()
                    file_field.storage.delete(file_name)
                    request_file.name = new_file_basename
                    request_file.file = new_file_name
                    request_file.save()

    def create(self, validated_data):

        instance = super().create(validated_data)
        
        self.rename_files(instance)

        return instance

    def update(self, instance, validated_data):
        # Remember old files
        old_files = set(instance.files.all())
        instance.files.clear()

        # Update the request with new values
        instance = super().update(instance, validated_data)

        # Get new files
        new_files = set(instance.files.all())

        # Delete files which are not in the list of request's files anymore
        files_to_delete = list(old_files - new_files)
        for file in files_to_delete:
            file.delete()

        self.rename_files(instance)

        return instance


class RequestFileSerializer(ModelSerializer):
    name = SerializerMethodField()
    size = SerializerMethodField()
    path = SerializerMethodField()

    class Meta:
        model = FileRequest
        fields = ("id", "name", "size", "path")

    def get_name(self, obj):
        return re.sub(r'^LIMS-[1-9]{1}[0-9]*_', '', obj.name.split("/")[-1])

    def get_size(self, obj):
        return obj.file.size

    def get_path(self, obj):
        return settings.MEDIA_URL + obj.file.name
