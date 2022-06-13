from django.apps import apps

from rest_framework.serializers import ModelSerializer, SerializerMethodField


Request = apps.get_model('request', 'Request')
Library = apps.get_model('library', 'Library')
Sample = apps.get_model('sample', 'Sample')
Flowcell = apps.get_model('flowcell', 'Flowcell')


class BaseSerializer(ModelSerializer):
    library_name = SerializerMethodField()
    library_strategy = SerializerMethodField()
    library_layout = SerializerMethodField()
    insert_size = SerializerMethodField()
    library_construction_protocol = SerializerMethodField()
    scientific_name = SerializerMethodField()
    taxon_id = SerializerMethodField()
    sample_description = SerializerMethodField()
    file_name = SerializerMethodField()
    file_format = SerializerMethodField()

    class Meta:
        fields = (
            'pk',
            'barcode',
            'library_name',
            'library_strategy',
            'library_layout',
            'insert_size',
            'library_construction_protocol',
            'scientific_name',
            'taxon_id',
            'sample_description',
            'file_name',
            'file_format',
        )

    def get_library_name(self, obj):
        return obj.name

    def get_library_strategy(self, obj):
        return obj.library_type.name

    def get_library_layout(self, obj):
        return 'single' if obj.read_length.name[0] == '1' else 'paired'

    def get_library_construction_protocol(self, obj):
        return obj.library_protocol.name

    def get_scientific_name(self, obj):
        return obj.organism.scientific_name

    def get_taxon_id(self, obj):
        return obj.organism.taxon_id

    def get_sample_description(self, obj):
        return obj.comments

    def get_file_name(self, obj):
        postfix = 'R1' if obj.read_length.name[0] == '1' else 'R2'
        return f'{obj.name}_{postfix}.fastaq.qz'

    def get_file_format(self, obj):
        return 'fastaq'


class LibrarySerializer(BaseSerializer):
    class Meta:
        model = Library
        fields = BaseSerializer.Meta.fields

    def get_insert_size(self, obj):
        return obj.mean_fragment_size


class SampleSerializer(BaseSerializer):
    class Meta:
        model = Sample
        fields = BaseSerializer.Meta.fields

    def get_insert_size(self, obj):
        try:
            return obj.librarypreparation.mean_fragment_size
        except Exception:
            return None


class MetadataSerializer(ModelSerializer):
    libraries = SampleSerializer(many=True)
    samples = SampleSerializer(many=True)

    class Meta:
        model = Request
        fields = ('description', 'libraries', 'samples',)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        result = []

        if not any(data['libraries']) and not any(data['samples']):
            return []

        flowcell = instance.flowcell.only('sequencer__name').first()
        sequencer_name = flowcell.sequencer.name if flowcell else None

        for type in ['libraries', 'samples']:
            result.extend(list(map(
                lambda x: {**{
                    'design_description': data['description'],
                    'instrument_model': sequencer_name,
                }, **x},
                data.pop(type),
            )))

        return {'result': result}
