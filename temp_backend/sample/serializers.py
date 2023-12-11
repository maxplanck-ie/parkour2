from library_sample_shared.serializers import LibrarySampleBaseSerializer
from rest_framework.serializers import (
    IntegerField,
    ModelSerializer,
    SerializerMethodField,
)
from sample.models import NucleicAcidType, Sample


class NucleicAcidTypeSerializer(ModelSerializer):

    type = SerializerMethodField()

    def get_type(self, obj):
        if obj.single_cell:
            return f'SingleCell{obj.type}'
        else:
            return obj.type
    
    class Meta:
        model = NucleicAcidType
        fields = (
            "id",
            "name",
            "type",
            "single_cell",
        )


class SampleSerializer(LibrarySampleBaseSerializer):
    pk = IntegerField(required=False)
    record_type = SerializerMethodField()
    nucleic_acid_type_name = SerializerMethodField()

    class Meta(LibrarySampleBaseSerializer.Meta):
        model = Sample
        fields = LibrarySampleBaseSerializer.Meta.fields + (
            "pk",
            "record_type",
            "is_converted",
            "rna_quality",
            "nucleic_acid_type",
            "nucleic_acid_type_name",
            "cell_density",
            "cell_viability", 
            "starting_number_cells",
            "number_targeted_cells"
        )

    def get_record_type(self, obj):
        return "Sample"

    def get_nucleic_acid_type_name(self, obj):
        return obj.nucleic_acid_type.name
