import random

from django.apps import apps
from library_sample_shared.serializers import LibrarySampleBaseSerializer
from rest_framework.serializers import (
    IntegerField,
    ModelSerializer,
    SerializerMethodField,
)
from sample.serializers import SampleSerializer

Library = apps.get_model("library", "Library")
Request = apps.get_model("request", "Request")


class LibrarySerializer(LibrarySampleBaseSerializer):
    pk = IntegerField(required=False)
    index_type_name = SerializerMethodField()
    record_type = SerializerMethodField()

    class Meta(LibrarySampleBaseSerializer.Meta):
        model = Library
        fields = LibrarySampleBaseSerializer.Meta.fields + (
            "pk",
            "record_type",
            "index_type",
            "index_type_name",
            "index_reads",
            "index_i7",
            "index_i5",
            "mean_fragment_size",
            "measuring_unit",
            "measured_value",
        )

    def get_record_type(self, obj):
        return "Library"

    def get_index_type_name(self, obj):
        return obj.index_type.name


class RequestParentNodeSerializer(ModelSerializer):
    id = SerializerMethodField()
    cls = SerializerMethodField()
    leaf = SerializerMethodField()

    class Meta:
        model = Request
        fields = (
            "id",
            "name",
            "total_records_count",
            "total_sequencing_depth",
            "cls",
            "leaf",
        )

    def get_id(self, obj):
        return obj.pk

    def get_cls(self, obj):
        return "parent-node-name"

    def get_leaf(self, obj):
        return False


class LibraryChildNodeSerializer(LibrarySerializer):
    leaf = SerializerMethodField()

    class Meta(LibrarySerializer.Meta):
        fields = LibrarySerializer.Meta.fields + ("leaf",)

    def get_request_id(self, obj):
        return None

    def get_request_name(self, obj):
        return None

    def get_leaf(self, obj):
        return True


class SampleChildNodeSerializer(SampleSerializer):
    leaf = SerializerMethodField()

    class Meta(SampleSerializer.Meta):
        fields = SampleSerializer.Meta.fields + ("leaf",)

    def get_request_id(self, obj):
        return None

    def get_request_name(self, obj):
        return None

    def get_leaf(self, obj):
        return True


class RequestChildrenNodesSerializer(ModelSerializer):
    id = SerializerMethodField()
    request_id = SerializerMethodField()
    request_name = SerializerMethodField()
    libraries = LibraryChildNodeSerializer(many=True)
    samples = SampleChildNodeSerializer(many=True)

    class Meta:
        model = Request
        fields = (
            "id",
            "request_id",
            "request_name",
            "libraries",
            "samples",
        )

    def get_id(self, obj):
        # Each leaf node needs a unique id
        return obj.pk + random.randint(0, 1000)

    def get_request_id(self, obj):
        return obj.pk

    def get_request_name(self, obj):
        return obj.name

    def to_representation(self, instance):
        data = super().to_representation(instance)
        result = []

        for type in ["libraries", "samples"]:
            result.extend(
                list(
                    map(
                        lambda x: {
                            **x,
                            **{
                                "id": data["id"] + x["pk"],
                                "request_id": data["request_id"],
                                "request_name": data["request_name"],
                            },
                        },
                        data.pop(type),
                    )
                )
            )

        return {"children": sorted(result, key=lambda x: x["barcode"][3:])}
