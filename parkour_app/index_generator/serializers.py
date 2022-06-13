from django.apps import apps

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    ModelSerializer,
    ListSerializer,
    SerializerMethodField,
    IntegerField,
)

from .models import PoolSize

Request = apps.get_model('request', 'Request')
Library = apps.get_model('library', 'Library')
Sample = apps.get_model('sample', 'Sample')


class PoolSizeSerializer(ModelSerializer):
    name = SerializerMethodField()

    class Meta:
        model = PoolSize
        fields = ('id', 'name', 'multiplier', 'size',)

    def get_name(self, obj):
        return f'{obj.multiplier}x{obj.size}'


class IndexGeneratorListSerializer(ListSerializer):
    def update(self, instance, validated_data):
        # Maps for id->instance and id->data item.
        object_mapping = {obj.pk: obj for obj in instance}
        data_mapping = {item['pk']: item for item in validated_data}

        # Perform updates
        ret = []
        for obj_id, data in data_mapping.items():
            obj = object_mapping.get(obj_id, None)
            if obj is not None:
                ret.append(self.child.update(obj, data))
        return ret


class IndexGeneratorBaseSerializer(ModelSerializer):
    pk = IntegerField()
    record_type = SerializerMethodField()
    library_protocol_name = SerializerMethodField()

    class Meta:
        list_serializer_class = IndexGeneratorListSerializer
        fields = (
            'pk',
            'record_type',
            'name',
            'barcode',
            'sequencing_depth',
            'library_protocol_name',
            'read_length',
            'index_type',
            'index_i7_id',
            'index_i7',
            'index_i5_id',
            'index_i5',
        )
        extra_kwargs = {
            'name': {'required': False},
            'barcode': {'required': False},
            'sequencing_depth': {'required': False},
            'read_length': {'required': False},
        }

    def get_record_type(self, obj):
        return obj.__class__.__name__

    def get_library_protocol_name(self, obj):
        return obj.library_protocol.name

    def get_index_type_format(self, obj):
        return obj.index_type.format if obj.index_type else None

    def to_internal_value(self, data):
        internal_value = super().to_internal_value(data)

        index_type = data.get('index_type', None)
        if index_type:
            if data['record_type'] == 'Sample':
                internal_value.update({
                    'index_type_id': index_type
                })
            else:
                raise ValidationError({
                    'index_type': ['A sample is required.'],
                })

        return internal_value


class IndexGeneratorLibrarySerializer(IndexGeneratorBaseSerializer):
    class Meta(IndexGeneratorBaseSerializer.Meta):
        model = Library


class IndexGeneratorSampleSerializer(IndexGeneratorBaseSerializer):
    class Meta(IndexGeneratorBaseSerializer.Meta):
        model = Sample


class IndexGeneratorSerializer(ModelSerializer):
    request = SerializerMethodField()
    request_name = SerializerMethodField()
    libraries = IndexGeneratorLibrarySerializer(many=True)
    samples = IndexGeneratorSampleSerializer(many=True)

    class Meta:
        model = Request
        fields = ('request', 'request_name', 'libraries', 'samples',)

    def get_request(self, obj):
        return obj.pk

    def get_request_name(self, obj):
        return obj.name

    def to_representation(self, instance):
        data = super().to_representation(instance)
        result = []

        if not any(data['libraries']) and not any(data['samples']):
            return []

        for type in ['libraries', 'samples']:
            result.extend(list(map(
                lambda x: {**{
                    'request': data['request'],
                    'request_name': data['request_name'],
                }, **x},
                data.pop(type),
            )))

        return result
