from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    CharField,
    IntegerField,
    ListSerializer,
    ModelSerializer,
    SerializerMethodField,
)

from .models import LibraryPreparation


class LibraryPreparationListSerializer(ListSerializer):
    def update(self, instance, validated_data):
        # Maps for id->instance and id->data item.
        object_mapping = {obj.pk: obj for obj in instance}
        data_mapping = {item["pk"]: item for item in validated_data}

        # Perform updates
        ret = []
        for obj_id, data in data_mapping.items():
            obj = object_mapping.get(obj_id, None)
            if obj is not None:
                if "concentration_sample" in data.keys():
                    obj.sample.measured_value_facility = data["concentration_sample"]

                if "comments_facility" in data.keys():
                    obj.sample.comments_facility = data["comments_facility"]

                if "size_distribution_facility" in data.keys():
                    obj.sample.size_distribution_facility = data[
                        "size_distribution_facility"
                    ]

                if "measuring_unit_facility" in data.keys():
                    obj.sample.measuring_unit_facility = data["measuring_unit_facility"]

                if "measured_value_facility" in data.keys():
                    obj.sample.measured_value_facility = data["measured_value_facility"]

                obj.sample.save(
                    update_fields=[
                        "comments_facility",
                        "size_distribution_facility",
                        "measuring_unit_facility",
                        "measured_value_facility",
                    ]
                )

                if "quality_check" in data.keys():
                    if data["quality_check"] == "passed":
                        obj.sample.status = 3
                    elif data["quality_check"] == "failed":
                        obj.sample.status = -1
                    obj.sample.save(update_fields=["status"])

                ret.append(self.child.update(obj, data))
        return ret


class LibraryPreparationSerializer(ModelSerializer):
    pk = IntegerField()
    name = SerializerMethodField()
    barcode = SerializerMethodField()
    request_name = SerializerMethodField()
    pool_name = SerializerMethodField()
    is_converted = SerializerMethodField()
    library_protocol = SerializerMethodField()
    library_protocol_name = SerializerMethodField()
    concentration_sample = SerializerMethodField()
    comments_facility = SerializerMethodField()
    coordinate = SerializerMethodField()
    index_type = SerializerMethodField()
    index_i7_id = SerializerMethodField()
    index_i5_id = SerializerMethodField()
    quality_check = CharField(required=False)
    size_distribution_facility = SerializerMethodField()
    measuring_unit_facility = SerializerMethodField()
    measured_value_facility = SerializerMethodField()
    comments_library_sample = SerializerMethodField()

    class Meta:
        model = LibraryPreparation
        list_serializer_class = LibraryPreparationListSerializer
        fields = (
            "pk",
            "name",
            "barcode",
            "is_converted",
            "request_name",
            "pool_name",
            "library_protocol",
            "library_protocol_name",
            "starting_amount",
            "pcr_cycles",
            "concentration_library",
            "concentration_sample",
            "mean_fragment_size",
            "coordinate",
            "index_type",
            "index_i7_id",
            "index_i5_id",
            "create_time",
            "quality_check",
            "smear_analysis",
            "size_distribution_facility",
            "measuring_unit_facility",
            "measured_value_facility",
            "comments",
            "comments_facility",
            "comments_library_sample",
        )

    def to_internal_value(self, data):
        internal_value = super().to_internal_value(data)

        if "concentration_sample" in data:
            raw = data["concentration_sample"]
            if raw in (None, ""):
                internal_value["concentration_sample"] = None
            else:
                try:
                    internal_value["concentration_sample"] = float(raw)
                except (TypeError, ValueError):
                    raise ValidationError(
                        {"concentration_sample": ["A valid float is required."]}
                    )

        if "size_distribution_facility" in data:
            raw = data["size_distribution_facility"]
            if raw in (None, ""):
                internal_value["size_distribution_facility"] = None
            else:
                try:
                    internal_value["size_distribution_facility"] = float(raw)
                except (TypeError, ValueError):
                    raise ValidationError(
                        {"size_distribution_facility": ["A valid float is required."]}
                    )

        if "measuring_unit_facility" in data:
            internal_value["measuring_unit_facility"] = data["measuring_unit_facility"]

        if "measured_value_facility" in data:
            internal_value["measured_value_facility"] = data["measured_value_facility"]

        if "comments_facility" in data:
            internal_value["comments_facility"] = data["comments_facility"]

        return internal_value

    def get_name(self, obj):
        return obj.sample.name

    def get_barcode(self, obj):
        return obj.sample.barcode

    def get_request_name(self, obj):
        return self.context.get("requests").get(obj.sample.pk)

    def get_pool_name(self, obj):
        return self.context.get("pools").get(obj.sample.pk)

    def get_is_converted(self, obj):
        return obj.sample.is_converted

    def get_library_protocol(self, obj):
        return obj.sample.library_protocol.pk

    def get_library_protocol_name(self, obj):
        return obj.sample.library_protocol.name

    def get_concentration_sample(self, obj):
        return obj.sample.measured_value_facility

    def get_coordinate(self, obj):
        coordinates = self.context.get("coordinates", {})
        index_type = obj.sample.index_type.pk if obj.sample.index_type else ""
        key = (
            index_type,
            obj.sample.index_i7_id,
            obj.sample.index_i5_id,
        )
        return coordinates.get(key, "")

    def get_index_type(self, obj):
        return obj.sample.index_type.name if obj.sample.index_type else ""

    def get_index_i7_id(self, obj):
        return obj.sample.index_i7_id

    def get_index_i5_id(self, obj):
        return obj.sample.index_i5_id

    def get_size_distribution_facility(self, obj):
        return obj.sample.size_distribution_facility

    def get_measuring_unit_facility(self, obj):
        return obj.sample.measuring_unit_facility

    def get_measured_value_facility(self, obj):
        return obj.sample.measured_value_facility

    def get_comments_library_sample(self, obj):
        return obj.sample.comments

    def get_comments_facility(self, obj):
        return obj.sample.comments_facility
