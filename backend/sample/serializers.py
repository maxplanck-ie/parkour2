from library_sample_shared.serializers import LibrarySampleBaseSerializer
from rest_framework.serializers import (
    IntegerField,
    ModelSerializer,
    SerializerMethodField,
)
from sample.models import NucleicAcidType, Sample


class NucleicAcidTypeSerializer(ModelSerializer):
    class Meta:
        model = NucleicAcidType
        fields = (
            "id",
            "name",
            "type",
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
            "measuring_unit",
            "measured_value",
            "gmo",
            "biosafety_level",
            "nucleic_acid_type",
            "nucleic_acid_type_name",
        )

    def get_record_type(self, obj):
        return "Sample"

    def get_nucleic_acid_type_name(self, obj):
        return obj.nucleic_acid_type.name
