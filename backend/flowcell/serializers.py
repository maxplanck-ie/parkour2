import itertools
from collections import Counter
from pprint import pprint

from django.apps import apps
from django.db import transaction
from django.db.models import Q
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    CharField,
    IntegerField,
    ListSerializer,
    ModelSerializer,
    SerializerMethodField,
)

from .models import Flowcell, Lane, Sequencer

Request = apps.get_model("request", "Request")
Library = apps.get_model("library", "Library")
Sample = apps.get_model("sample", "Sample")
Pool = apps.get_model("index_generator", "Pool")


class SequencerSerializer(ModelSerializer):
    class Meta:
        model = Sequencer
        fields = (
            "id",
            "name",
            "lanes",
            "lane_capacity",
        )


class LaneListSerializer(ListSerializer):
    def update(self, instance, validated_data):
        # Maps for id->instance and id->data item.
        object_mapping = {obj.pk: obj for obj in instance}
        data_mapping = {item["pk"]: item for item in validated_data}

        # Perform updates
        ret = []
        for obj_id, data in data_mapping.items():
            obj = object_mapping.get(obj_id, None)
            if obj is not None:
                if (
                    "quality_check" in data.keys()
                    and data["quality_check"] == "completed"
                ):
                    obj.completed = True
                ret.append(self.child.update(obj, data))
        return ret


class LaneSerializer(ModelSerializer):
    pk = IntegerField()
    pool_name = SerializerMethodField()
    read_length_name = SerializerMethodField()
    index_i7_show = SerializerMethodField()
    index_i5_show = SerializerMethodField()
    quality_check = CharField(required=False)
    request = SerializerMethodField()
    protocol = SerializerMethodField()
    has_delivered_records = SerializerMethodField()

    class Meta:
        list_serializer_class = LaneListSerializer
        model = Lane
        fields = (
            "pk",
            "name",
            "pool",
            "pool_name",
            "read_length_name",
            "index_i7_show",
            "index_i5_show",
            "loading_concentration",
            "phix",
            "quality_check",
            "request",
            "protocol",
            "has_delivered_records",
        )
        extra_kwargs = {
            "name": {"required": False},
            "pool": {"required": False},
        }

    def get_request(self, obj):
        requests = []
        records = obj.pool.libraries.all() or obj.pool.samples.all()

        for record in records:
            for req in record.request.all():
                requests.append(req.name)

        unique_requests = list(dict.fromkeys(requests))
        if not unique_requests:
            return None
        if len(unique_requests) == 1:
            return unique_requests[0]
        return ", ".join(unique_requests)

    def get_protocol(self, obj):
        protocols = []

        records = obj.pool.libraries.all() or obj.pool.samples.all()

        for record in records:
            if record.library_protocol:
                protocols.append(record.library_protocol.name)
            else:
                protocols.append(None)

        if len(protocols) == 1 or len(set(protocols)) == 1:
            return protocols[0]
        else:
            return ";".join(protocols)

    def get_has_delivered_records(self, obj):
        if not obj.pool_id:
            return False
        return (
            obj.pool.libraries.filter(status=6).exists()
            or obj.pool.samples.filter(status=6).exists()
        )

    def get_pool_name(self, obj):
        return obj.pool.name

    def get_read_length_name(self, obj):
        read_lengths = []
        i = 0
        records = obj.pool.libraries.all() or obj.pool.samples.all()
        for record in records:
            # print(record.library_protocol.name)
            read_lengths.append(str(record.read_length.name))

        if len(read_lengths) == 1 or len(set(read_lengths)) == 1:
            return read_lengths[0]
        else:
            return ";".join(read_lengths)

    def get_index_i7_show(self, obj):
        """we show the actual index instead of a yes/no entry"""
        records = obj.pool.libraries.all() or obj.pool.samples.all()
        idx = []
        contains_i7 = False
        for record in records:
            if str(record.index_i7) != "":
                contains_i7 = True
                break
                # idx.append(str(record.index_i7))

        # if len(idx) == 1 or len(set(idx)) == 1:
        #    return idx[0]
        # else:
        #    return ";".join(idx)
        if contains_i7:
            return "Yes"
        else:
            return ""

    def get_index_i5_show(self, obj):
        """we show the actual index instead of a yes/no entry"""

        records = obj.pool.libraries.all() or obj.pool.samples.all()
        idx = []
        contains_i5 = False
        for record in records:
            if str(record.index_i5) != "":
                contains_i5 = True
                break
                # idx.append(str(record.index_i5))

        # if len(idx) == 1 or len(set(idx)) == 1:
        #    return idx[0]
        # else:
        #    return ";".join(idx)
        if contains_i5:
            return "Yes"
        else:
            return ""
        # return None


class FlowcellListSerializer(ModelSerializer):
    flowcell = SerializerMethodField()
    sequencer_name = SerializerMethodField()
    lanes = LaneSerializer(many=True)

    class Meta:
        model = Flowcell
        fields = (
            "flowcell",
            "flowcell_id",
            "sequencer",
            "sequencer_name",
            "create_time",
            "lanes",
        )

    def get_flowcell(self, obj):
        # pprint(vars(obj))
        return obj.pk

    def get_sequencer_name(self, obj):
        return obj.sequencer.name

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if not any(data["lanes"]):
            return []

        return list(
            map(
                lambda x: {
                    **{
                        "flowcell": data["flowcell"],
                        "flowcell_id": data["flowcell_id"],
                        "sequencer": data["sequencer"],
                        "sequencer_name": data["sequencer_name"],
                        "create_time": data["create_time"],
                    },
                    **x,
                },
                data.pop("lanes"),
            )
        )


class FlowcellSerializer(ModelSerializer):
    class Meta:
        model = Flowcell
        fields = (
            "flowcell_id",
            "sequencer",
        )

    def to_internal_value(self, data):
        internal_value = super().to_internal_value(data)

        lanes = data.get("lanes", [])
        if not lanes:
            raise ValidationError(
                {
                    "lanes": ["No lanes are provided."],
                }
            )

        # Check if all lanes are loaded
        sequencer = internal_value.get("sequencer")
        if len(lanes) != sequencer.lanes:
            raise ValidationError(
                {
                    "lanes": ["All lanes must be loaded."],
                }
            )

        lane_errors, pool_warnings = self._validate_lanes_for_sequencer(
            lanes, sequencer
        )
        if lane_errors:
            raise ValidationError({"lanes": lane_errors})

        self.pool_warnings = pool_warnings
        internal_value.update({"lanes": lanes})

        return internal_value

    def _get_pool_read_length_name(self, pool):
        library_read_lengths = list(
            pool.libraries.values_list("read_length__name", flat=True).distinct()
        )
        sample_read_lengths = list(
            pool.samples.values_list("read_length__name", flat=True).distinct()
        )
        read_lengths = {
            read_length_name
            for read_length_name in library_read_lengths + sample_read_lengths
            if read_length_name
        }
        if not read_lengths:
            return None
        if len(read_lengths) == 1:
            return next(iter(read_lengths))
        return "mixed"

    def _is_pool_ready(self, pool):
        libraries_statuses = [x.status for x in pool.libraries.all()]
        samples_statuses = [x.status for x in pool.samples.all()]
        statuses = list(libraries_statuses) + list(samples_statuses)
        return bool(statuses) and statuses.count(4) == len(statuses)

    def _pool_has_blocking_status(self, pool):
        """True if the pool contains a library/sample that is neither fully
        pooled (status 4) nor QC-failed (negative status). Negative statuses
        (e.g. -1 "Quality Check Failed") are allowed to be loaded anyway --
        anything else mid-workflow is not."""
        libraries_statuses = [x.status for x in pool.libraries.all()]
        samples_statuses = [x.status for x in pool.samples.all()]
        statuses = list(libraries_statuses) + list(samples_statuses)
        if not statuses:
            return True
        return any(status != 4 and status >= 0 for status in statuses)

    def _validate_lanes_for_sequencer(self, lanes, sequencer):
        errors = []
        warnings = []

        lane_names = [lane.get("name") for lane in lanes]
        if len(lane_names) != len(set(lane_names)):
            errors.append("Lane names must be unique.")

        pool_ids = [lane.get("pool_id") for lane in lanes if lane.get("pool_id")]
        if len(pool_ids) != len(lanes):
            errors.append("Each lane must reference a pool.")
            return errors, warnings

        pools_by_id = Pool.objects.filter(archived=False, pk__in=pool_ids).in_bulk()
        missing_pool_ids = sorted(set(pool_ids) - set(pools_by_id.keys()))
        if missing_pool_ids:
            errors.append(
                "Some selected pools were not found or are archived: "
                + ", ".join(map(str, missing_pool_ids))
                + "."
            )
            return errors, warnings

        pool_assignment_counts = Counter(pool_ids)
        read_length_names = set()

        for pool_id, lane_count in pool_assignment_counts.items():
            pool = pools_by_id[pool_id]

            if pool.size and pool.loaded + lane_count > pool.size.multiplier:
                errors.append(
                    f"Pool '{pool.name}' does not have enough remaining loads for the selected lanes."
                )

            if not self._is_pool_ready(pool):
                if self._pool_has_blocking_status(pool):
                    errors.append(
                        f"Pool '{pool.name}' is not ready and cannot be loaded on a flowcell."
                    )
                else:
                    warnings.append(
                        f"Pool '{pool.name}' was loaded even though it contains "
                        "QC-failed libraries/samples."
                    )

            if pool.size and pool.size.size > sequencer.lane_capacity:
                errors.append(
                    f"Pool '{pool.name}' cannot fit on a lane with capacity {sequencer.lane_capacity}."
                )

            pool_read_length_name = self._get_pool_read_length_name(pool)
            if pool_read_length_name in (None, "mixed"):
                errors.append(
                    f"Pool '{pool.name}' has invalid read length information."
                )
            else:
                read_length_names.add(pool_read_length_name)

        if len(read_length_names) > 1:
            errors.append("Read Length must be the same for all pools on a flowcell.")

        return errors, warnings

    def create(self, validated_data):
        lanes = validated_data.pop("lanes")
        with transaction.atomic():
            instance = super().create(validated_data)

            # Create Lane objects and add them to the flowcell
            lane_ids = []
            for lane_dict in lanes:
                lane = Lane(name=lane_dict["name"], pool_id=lane_dict["pool_id"])
                lane.save()
                lane_ids.append(lane.pk)
            instance.lanes.add(*lane_ids)

            pool_ids = list(
                Lane.objects.all()
                .filter(pk__in=lane_ids)
                .values_list(
                    "pool",
                    flat=True,
                )
                .distinct()
            )
            pools = Pool.objects.filter(archived=False, pk__in=pool_ids)

            # After creating a flowcell, update all pool's libraries' and
            # samples' statuses if the pool is fully loaded
            for pool in pools:
                if pool.loaded == pool.size.multiplier:
                    pool.libraries.all().filter(status=4).update(status=5)
                    pool.samples.all().filter(status=4).update(status=5)

            # When a Flowcell is loaded, save the all corresponding requests
            libraries = Library.objects.filter(pool__in=pools)
            samples = Sample.objects.filter(pool__in=pools)
            requests = Request.objects.filter(
                archived=False,
                pk__in=set(
                    itertools.chain(
                        libraries.values_list("request", flat=True).distinct(),
                        samples.values_list("request", flat=True).distinct(),
                    )
                ),
            )
            requests.update(sequenced=True)
            instance.requests.add(*requests)

        return instance


class PoolListSerializer(ModelSerializer):
    read_length = SerializerMethodField()
    read_length_name = SerializerMethodField()
    pool_size_id = SerializerMethodField()
    pool_size = SerializerMethodField()
    ready = SerializerMethodField()

    class Meta:
        model = Pool
        fields = (
            "pk",
            "name",
            "read_length",
            "read_length_name",
            "pool_size_id",
            "pool_size",
            "loaded",
            "ready",
        )

    def get_read_length(self, obj):
        records = obj.libraries.all() or obj.samples.all()
        if records.count() > 0:
            return records[0].read_length.pk
        return None

    def get_read_length_name(self, obj):
        records = obj.libraries.all() or obj.samples.all()
        if records.count() > 0:
            return records[0].read_length.name
        return None

    def get_pool_size_id(self, obj):
        return obj.size.pk

    def get_pool_size(self, obj):
        return obj.size.multiplier

    def get_ready(self, obj):
        libraries_statuses = [x.status for x in obj.libraries.all()]
        samples_statuses = [x.status for x in obj.samples.all()]
        statuses = list(libraries_statuses) + list(samples_statuses)
        return statuses.count(4) == len(statuses)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Ignore pools if all of its libraries/samples are
        # not ready yet or failed
        if instance.libraries.count() + instance.samples.count() == 0:
            return {}
        return data


class PoolInfoBaseSerializer(ModelSerializer):
    record_type = SerializerMethodField()
    protocol_name = SerializerMethodField()
    request_name = SerializerMethodField()

    class Meta:
        fields = (
            "name",
            "barcode",
            "record_type",
            "protocol_name",
            "request_name",
        )

    def get_record_type(self, obj):
        return obj.__class__.__name__

    def get_protocol_name(self, obj):
        return obj.library_protocol.name

    def get_request_name(self, obj):
        return obj.request.get().name


class PoolInfoLibrarySerializer(PoolInfoBaseSerializer):
    class Meta(PoolInfoBaseSerializer.Meta):
        model = Library
        fields = PoolInfoBaseSerializer.Meta.fields


class PoolInfoSampleSerializer(PoolInfoBaseSerializer):
    class Meta(PoolInfoBaseSerializer.Meta):
        model = Sample
        fields = PoolInfoBaseSerializer.Meta.fields + ("is_converted",)


class PoolInfoSerializer(ModelSerializer):
    libraries = SerializerMethodField()
    samples = SerializerMethodField()

    class Meta:
        model = Pool
        fields = (
            "id",
            "name",
            "libraries",
            "samples",
        )

    def get_libraries(self, obj):
        queryset = obj.libraries.filter(~Q(status=-1))
        serializer = PoolInfoLibrarySerializer(queryset, many=True)
        return serializer.data

    def get_samples(self, obj):
        queryset = obj.samples.filter(~Q(status=-1))
        serializer = PoolInfoSampleSerializer(queryset, many=True)
        return serializer.data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        libraries = data.pop("libraries")
        samples = data.pop("samples")
        records = libraries + samples

        data.update({"records": sorted(records, key=lambda x: x["barcode"][3:])})

        return data
