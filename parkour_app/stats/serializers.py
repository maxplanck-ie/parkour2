from django.apps import apps

from rest_framework.serializers import ModelSerializer, SerializerMethodField

Flowcell = apps.get_model('flowcell', 'Flowcell')


class RunsSerializer(ModelSerializer):
    sequencer = SerializerMethodField()

    class Meta:
        model = Flowcell
        fields = ('pk', 'flowcell_id', 'create_time', 'sequencer', 'matrix',)

    def get_sequencer(self, obj):
        return obj.sequencer.name

    def to_representation(self, instance):
        data = super().to_representation(instance)
        result = []

        lanes = {}
        for lane in instance.fetched_lanes:
            records = lane.pool.fetched_libraries or lane.pool.fetched_samples
            lanes[lane.name] = {
                'pool': lane.pool.name,
                'loading_concentration': lane.loading_concentration,
                'phix': lane.phix,
                'read_length': records[0].read_length.name,
                'library_preparation': records[0].library_protocol.name,
                'library_type': records[0].library_type.name,
                'request': records[0].fetched_request[0].name,
            }

        num_lanes = len(lanes)
        for item in data['matrix']:
            lane_key = 'Lane 1' if num_lanes == 1 else item['name']
            result.append({**{
                'pk': data['pk'],
                'flowcell_id': data['flowcell_id'],
                'create_time': data['create_time'],
                'sequencer': data['sequencer'],
                'read_length':
                lanes.get(lane_key, {}).get('read_length', None),
                'library_preparation':
                lanes.get(lane_key, {}).get('library_preparation', None),
                'library_type':
                lanes.get(lane_key, {}).get('library_type', None),
                'loading_concentration':
                lanes.get(lane_key, {}).get('loading_concentration', None),
                'phix': lanes.get(lane_key, {}).get('phix', None),
                'pool': lanes.get(lane_key, {}).get('pool', None),
                'request':
                lanes.get(lane_key, {}).get('request', None),
            }, **item})

        return sorted(result, key=lambda x: x['name'])


class SequencesSerializer(ModelSerializer):
    sequencer = SerializerMethodField()

    class Meta:
        model = Flowcell
        fields = (
            'pk',
            'flowcell_id',
            'create_time',
            'sequencer',
            'sequences',
        )

    def get_sequencer(self, obj):
        return obj.sequencer.name

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
                lanes[barcode].append(lane.name.split(' ')[1])

        items, processed_requests = {}, {}
        for request in instance.fetched_requests:
            if request.name not in processed_requests:
                records = request.fetched_libraries + request.fetched_samples
                for record in records:
                    barcode = record.barcode
                    items[barcode] = {
                        'name': record.name,
                        'barcode': record.barcode,
                        'request': request.name,
                        'library_protocol': record.library_protocol.name,
                        'library_type': record.library_type.name,
                        'reads_pf_requested': record.sequencing_depth,
                        'pool': pools.get(barcode, ''),
                        'lane': lanes.get(barcode, ''),
                    }
                processed_requests[request.name] = True

        for item in data['sequences']:
            obj = items.get(item['barcode'], {})
            result.append({**{
                'pk': data['pk'],
                'flowcell_id': data['flowcell_id'],
                'create_time': data['create_time'],
                'sequencer': data['sequencer'],
                'request': obj.get('request', ''),
                'barcode': obj.get('barcode', ''),
                'name': obj.get('name', ''),
                'lane': obj.get('lane', ''),
                'pool': obj.get('pool', ''),
                'library_protocol': obj.get('library_protocol', ''),
                'library_type': obj.get('library_type', ''),
                'reads_pf_requested': obj.get('reads_pf_requested', ''),
            }, **item})

        return sorted(result, key=lambda x: x['barcode'][3:])
