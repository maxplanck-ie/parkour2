from django.conf import settings
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from .models import Request, FileRequest


class RequestSerializer(ModelSerializer):
    user_full_name = SerializerMethodField()
    restrict_permissions = SerializerMethodField()
    deep_seq_request_name = SerializerMethodField()
    deep_seq_request_path = SerializerMethodField()
    completed = SerializerMethodField()
    files = SerializerMethodField()
    number_of_samples = SerializerMethodField()

    class Meta:
        model = Request
        fields = (
            'pk',
            'name',
            'user',
            'user_full_name',
            'create_time',
            'cost_unit',
            'description',
            'total_sequencing_depth',
            'restrict_permissions',
            'completed',
            'deep_seq_request_name',
            'deep_seq_request_path',
            'files',
            'sequenced',
            'number_of_samples',
        )

    def get_user_full_name(self, obj):
        return obj.user.full_name

    def get_number_of_samples(self,obj):
        return len(obj.statuses)

    def get_restrict_permissions(self, obj):
        """
        Don't allow the users to modify the requests and libraries/samples
        if they have reached status 1 or higher (or failed).
        """
        return True if not obj.user.is_staff and obj.statuses.count(0) == 0 \
            else False

    def get_completed(self, obj):
        """ Return True if request's libraries and samples are sequenced. """
        return obj.statuses.count(6) > 0

    def get_deep_seq_request_name(self, obj):
        return obj.deep_seq_request.name.split('/')[-1] \
            if obj.deep_seq_request else ''

    def get_deep_seq_request_path(self, obj):
        return settings.MEDIA_URL + obj.deep_seq_request.name \
            if obj.deep_seq_request else ''

    def get_files(self, obj):
        files = [{
            'pk': file.pk,
            'name': file.name.split('/')[-1],
            'path': settings.MEDIA_URL + file.file.name,
        } for file in obj.files.all()]
        return files

    def to_internal_value(self, data):
        internal_value = super().to_internal_value(data)

        records = data.get('records', [])
        if not records:
            raise ValidationError({
                'records': ['No libraries or samples are provided.'],
            })

        files = data.get('files', [])

        libraries = []
        samples = []
        for obj in records:
            if obj['record_type'] == 'Library':
                libraries.append(int(obj['pk']))
            elif obj['record_type'] == 'Sample':
                samples.append(int(obj['pk']))

        internal_value.update({
            'libraries': libraries,
            'samples': samples,
            'files': files,
        })

        return internal_value

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

        return instance


class RequestFileSerializer(ModelSerializer):
    size = SerializerMethodField()
    path = SerializerMethodField()

    class Meta:
        model = FileRequest
        fields = ('id', 'name', 'size', 'path')

    def get_size(self, obj):
        return obj.file.size

    def get_path(self, obj):
        return settings.MEDIA_URL + obj.file.name
