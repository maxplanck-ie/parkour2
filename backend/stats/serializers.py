from django.apps import apps
from rest_framework.serializers import ModelSerializer, SerializerMethodField

Flowcell = apps.get_model("flowcell", "Flowcell")


class RunsSerializer(ModelSerializer):
    sequencing_kit = SerializerMethodField()

    class Meta:
        model = Flowcell
        fields = (
            "pk",
            "flowcell_id",
            "create_time",
            "sequencing_kit",
            "matrix",
        )

    def get_sequencing_kit(self, obj):
        return str(obj.pool_size)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        result = []

        lanes = {}
        for lane in instance.fetched_lanes:
            records = lane.pool.fetched_libraries or lane.pool.fetched_samples
            lanes[lane.name] = {
                "pool": lane.pool.name,
                "loading_concentration": lane.loading_concentration,
                "phix": lane.phix,
                "read_length": records[0].read_length.name,
                "library_preparation": records[0].library_protocol.name,
                "library_type": records[0].library_type.name,
                "request": records[0].fetched_request[0].name,
            }

        num_lanes = len(lanes)
        for item in data["matrix"]:
            lane_key = "Lane 1" if num_lanes == 1 else item["name"]
            item["name"] = item["name"].lower().replace('lane', '').strip()
            result.append(
                {
                    **{
                        "pk": data["pk"],
                        "flowcell_id": data["flowcell_id"],
                        "create_time": data["create_time"],
                        "sequencing_kit": data["sequencing_kit"],
                        "read_length": lanes.get(lane_key, {}).get("read_length", None),
                        "library_preparation": lanes.get(lane_key, {}).get(
                            "library_preparation", None
                        ),
                        "library_type": lanes.get(lane_key, {}).get(
                            "library_type", None
                        ),
                        "loading_concentration": lanes.get(lane_key, {}).get(
                            "loading_concentration", None
                        ),
                        "phix": lanes.get(lane_key, {}).get("phix", None),
                        "pool": lanes.get(lane_key, {}).get("pool", None),
                        "request": lanes.get(lane_key, {}).get("request", None),
                    },
                    **item,
                }
            )

        return sorted(result, key=lambda x: x["name"])


class SequencesSerializer(ModelSerializer):
    sequencing_kit = SerializerMethodField()

    class Meta:
        model = Flowcell
        fields = (
            "pk",
            "flowcell_id",
            "create_time",
            "sequencing_kit",
            "sequences",
        )

    def get_sequencing_kit(self, obj):
        return str(obj.pool_size)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        result = []

        pools, lanes = {}, {}
        for lane in instance.fetched_lanes:
            pool = lane.pool
            records = pool.fetched_libraries + pool.fetched_samples
            for record in records:
                barcode = record.barcode
                pools[barcode] = pool.name
                if barcode not in lanes:
                    lanes[barcode] = []
                lanes[barcode].append(lane.name.split(" ")[1])

        items, processed_requests = {}, {}
        for request in instance.fetched_requests:
            if request.name not in processed_requests:
                records = request.fetched_libraries + request.fetched_samples
                for record in records:
                    barcode = record.barcode
                    items[barcode] = {
                        "name": record.name,
                        "barcode": record.barcode,
                        "request": request.name,
                        "library_protocol": record.library_protocol.name,
                        "library_type": record.library_type.name,
                        "reads_pf_requested": record.sequencing_depth,
                        "pool": pools.get(barcode, ""),
                        "lane": lanes.get(barcode, ""),
                    }
                processed_requests[request.name] = True

        # If merge-lanes-sequences-checkbox is ticked, sum reads_pf_sequenced for 
        # samples with identical name from different lanes of the same flowcell

        if self.context.get('merge_lanes', True):

            merged_data_sequences = {}
            for item in data['sequences']:
                reads_pf_sequenced = merged_data_sequences.get(item["name"], {'reads_pf_sequenced': 0})['reads_pf_sequenced'] + \
                                     item.get("reads_pf_sequenced", 0)
                merged_data_sequences[item["name"]] = {'barcode': item.get('barcode', ''),
                                                       'reads_pf_sequenced': reads_pf_sequenced}
            merged_data_sequences = [{'name': n,
                                      'lane': 'All',
                                      'barcode': d.get('barcode', ''),
                                      'reads_pf_sequenced': d.get('reads_pf_sequenced', 0),}
                                     for n, d in merged_data_sequences.items()]
            data["sequences"] = merged_data_sequences

        for item in data["sequences"]:
            obj = items.get(item["barcode"], {})
            result.append(
                {
                    **{
                        "pk": data["pk"],
                        "flowcell_id": data["flowcell_id"],
                        "create_time": data["create_time"],
                        "sequencing_kit": data["sequencing_kit"],
                        "request": obj.get("request", ""),
                        "barcode": obj.get("barcode", ""),
                        "name": obj.get("name", ""),
                        "lane": obj.get("lane", ""),
                        "pool": obj.get("pool", ""),
                        "library_protocol": obj.get("library_protocol", ""),
                        "library_type": obj.get("library_type", ""),
                        "reads_pf_requested": obj.get("reads_pf_requested", ""),
                    },
                    **item,
                }
            )

        return sorted(result, key=lambda x: x["barcode"][3:])
