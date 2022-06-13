from django.apps import apps

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    ModelSerializer,
    ListSerializer,
    SerializerMethodField,
    IntegerField,
    CharField,
)

Library = apps.get_model('library', 'Library')
Sample = apps.get_model('sample', 'Sample')
Pool = apps.get_model('index_generator', 'Pool')


class BaseListSerializer(ListSerializer):
    def update(self, instance, validated_data):
        # Maps for id->instance and id->data item.
        object_mapping = {obj.pk: obj for obj in instance}
        data_mapping = {item['pk']: item for item in validated_data}

        # Perform updates
        ret = []
        for obj_id, data in data_mapping.items():
            obj = object_mapping.get(obj_id, None)
            if obj is not None:
                if 'quality_check' in data.keys():
                    if data['quality_check'] == 'passed':
                        obj.status = 4
                    elif data['quality_check'] == 'failed':
                        obj.status = -1
                ret.append(self.child.update(obj, data))
        return ret


class PoolingBaseSerializer(ModelSerializer):
    pk = IntegerField()
    record_type = SerializerMethodField()
    request = SerializerMethodField()
    request_name = SerializerMethodField()
    concentration_c1 = SerializerMethodField()
    concentration_library = SerializerMethodField()
    mean_fragment_size = SerializerMethodField()
    coordinate = SerializerMethodField()
    create_time = SerializerMethodField()
    quality_check = CharField(required=False)

    class Meta:
        list_serializer_class = BaseListSerializer
        fields = (
            'pk',
            'record_type',
            'name',
            'status',
            'barcode',
            'request',
            'request_name',
            'sequencing_depth',
            'concentration_c1',
            'concentration_library',
            'mean_fragment_size',
            'create_time',
            'quality_check',
            'coordinate',
            'index_i7_id',
            'index_i5_id',
            'index_i7',
            'index_i5',
        )
        extra_kwargs = {
            'name': {'required': False},
            'barcode': {'required': False},
            'sequencing_depth': {'required': False},
        }

    def get_record_type(self, obj):
        return obj.__class__.__name__

    def get_request(self, obj):
        return self._get_request(obj).get('pk', None)

    def get_request_name(self, obj):
        return self._get_request(obj).get('name', None)

    def get_concentration_c1(self, obj):
        pooling_object = self._get_pooling_object(obj)
        return pooling_object.concentration_c1 if pooling_object else None

    def get_coordinate(self, obj):
        coordinates = self.context.get('coordinates', {})
        index_type = obj.index_type.pk if obj.index_type else ''
        key = (
            index_type,
            obj.index_i7_id,
            obj.index_i5_id,
        )
        return coordinates.get(key, '')

    def get_create_time(self, obj):
        pooling_object = self._get_pooling_object(obj)
        return pooling_object.create_time if pooling_object else None

    def to_internal_value(self, data):
        internal_value = super().to_internal_value(data)

        concentration_c1 = data.get('concentration_c1', None)
        if concentration_c1:
            try:
                internal_value.update({
                    'concentration_c1': float(concentration_c1)
                })
            except ValueError:
                raise ValidationError({
                    'concentration_c1': ['A valid float is required.'],
                })

        return internal_value

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr == 'concentration_c1':
                setattr(instance.pooling, attr, value)

        instance.pooling.save()
        instance.save()

        return instance

    def _get_request(self, obj):
        return self.context.get('requests').get(
            (obj.pk, obj.__class__.__name__), {}
        )

    def _get_pooling_object(self, obj):
        return self.context.get('pooling').get(
            (obj.pk, obj.__class__.__name__), None
        )


class PoolingLibrarySerializer(PoolingBaseSerializer):
    class Meta(PoolingBaseSerializer.Meta):
        model = Library

    def get_concentration_library(self, obj):
        return obj.concentration_facility

    def get_mean_fragment_size(self, obj):
        return obj.size_distribution_facility


class PoolingSampleSerializer(PoolingBaseSerializer):
    class Meta(PoolingBaseSerializer.Meta):
        model = Sample
        fields = PoolingBaseSerializer.Meta.fields + ('is_converted',)

    def get_concentration_library(self, obj):
        lib_prep_obj = self._get_library_preparation_object(obj)
        return lib_prep_obj.concentration_library if lib_prep_obj else None

    def get_mean_fragment_size(self, obj):
        lib_prep_obj = self._get_library_preparation_object(obj)
        return lib_prep_obj.mean_fragment_size if lib_prep_obj else None

    def _get_library_preparation_object(self, obj):
        return self.context.get('library_preparation').get(obj.pk, None)


class PoolSerializer(ModelSerializer):
    pool = SerializerMethodField()
    pool_name = SerializerMethodField()
    pool_size = SerializerMethodField()

    libraries = SerializerMethodField()
    samples = SerializerMethodField()
    comment = SerializerMethodField()

    class Meta:
        model = Pool
        fields = ('pool', 'pool_name', 'pool_size', 'libraries', 'samples','comment',)

    def get_pool(self, obj):
        return obj.pk

    def get_pool_name(self, obj):
        return obj.name

    def get_pool_size(self, obj):
        size = obj.size
        return f'{size.multiplier}x{size.size}'

    def get_libraries(self, obj):
        serializer = PoolingLibrarySerializer(
            obj.libraries, many=True, context=self.context)
        return serializer.data

    def get_samples(self, obj):
        serializer = PoolingSampleSerializer(
            obj.samples, many=True, context=self.context)
        return serializer.data

    def get_comment(self,obj):
        return obj.comment


    def to_representation(self, instance):
        data = super().to_representation(instance)
        result = []

        if not any(data['libraries']) and not any(data['samples']):
            return []

        for type in ['libraries', 'samples']:
            result.extend(list(map(
                lambda x: {**{
                    'pool': data['pool'],
                    'pool_name': data['pool_name'],
                    'pool_size': data['pool_size'],
                    'percentage_library': '{}%'.format(round(
                        x['sequencing_depth'] /
                        instance.total_sequencing_depth * 100
                    )),

                    'comment': data['comment']
                }, **x},
                data.pop(type),
            )))

        return result
