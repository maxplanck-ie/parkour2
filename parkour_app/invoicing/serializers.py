import logging
import itertools
from decimal import Decimal
from functools import reduce
from collections import Counter
import datetime
from django.apps import apps
from django.db.models import Prefetch

from rest_framework.fields import empty
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from .models import FixedCosts, LibraryPreparationCosts, SequencingCosts
from pprint import pprint
Request = apps.get_model('request', 'Request')
ReadLength = apps.get_model('library_sample_shared', 'ReadLength')
LibraryProtocol = apps.get_model('library_sample_shared', 'LibraryProtocol')
Library = apps.get_model('library', 'Library')
Sample = apps.get_model('sample', 'Sample')
Pool = apps.get_model('index_generator', 'Pool')
Sequencer = apps.get_model('flowcell', 'Sequencer')

logger = logging.getLogger('db')

def trunc_datetime(someDate):
    return someDate.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


class InvoicingSerializer(ModelSerializer):
    request = SerializerMethodField()
    cost_unit = SerializerMethodField()
    sequencer = SerializerMethodField()
    flowcell = SerializerMethodField()
    pool = SerializerMethodField()
    percentage = SerializerMethodField()
    read_length = SerializerMethodField()
    num_libraries_samples = SerializerMethodField()
    num_libraries_samples_show = SerializerMethodField()
    library_protocol = SerializerMethodField()
    fixed_costs = SerializerMethodField()
    sequencing_costs = SerializerMethodField()
    preparation_costs = SerializerMethodField()
    variable_costs = SerializerMethodField()
    total_costs = SerializerMethodField()

    class Meta:
        model = Request
        fields = ('request', 'cost_unit', 'sequencer', 'flowcell', 'pool',
                  'percentage', 'read_length', 'num_libraries_samples','num_libraries_samples_show',
                  'library_protocol', 'fixed_costs', 'sequencing_costs',
                  'preparation_costs', 'variable_costs', 'total_costs',)

    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)

        # Fetch all pools
        libraries_qs = Library.objects.all().select_related(
            'read_length',
        ).only(
            'read_length',
            'sequencing_depth',
        )
        samples_qs = Sample.objects.all().select_related(
            'read_length',
        ).only(
            'read_length',
            'sequencing_depth',
        )

        curr_month = int(self.context['curr_month'])
        curr_year = int(self.context['curr_year'])

        pool_ids = instance.values_list('flowcell__lanes__pool')
        pools = Pool.objects.filter(pk__in=pool_ids).prefetch_related(
            Prefetch('libraries', queryset=libraries_qs),
            Prefetch('samples', queryset=samples_qs),
        ).order_by('pk')

        # Fetch Fixed Costs
        fixed_costs = FixedCosts.objects.values('sequencer', 'price')
        fixed_costs = {x['sequencer']: x['price'] for x in fixed_costs}

        # Fetch Preparation Costs
        preparation_costs = LibraryPreparationCosts.objects.values(
            'library_protocol', 'price')
        preparation_costs = {x['library_protocol']: x['price']
                             for x in preparation_costs}

        # Fetch Sequencing Costs
        sequencing_costs = SequencingCosts.objects.values(
            'sequencer', 'read_length', 'price')
        sequencing_costs = {
            str(x['sequencer']) + '_' + str(x['read_length']): x['price']
            for x in sequencing_costs
        }

        self.context.update({
            'pools': pools,
            'fixed_costs': fixed_costs,
            'preparation_costs': preparation_costs,
            'sequencing_costs': sequencing_costs,
            'curr_month': curr_month,
            'curr_year': curr_year,
        })

    def get_request(self, obj):
        return obj.name

    def get_cost_unit(self, obj):
        return obj.cost_unit.name if obj.cost_unit else None

    def get_sequencer(self, obj):
        return [{
            'flowcell_id': flowcell.flowcell_id,
            'sequencer_name': flowcell.sequencer.name,
        } for flowcell in obj.flowcell.all()]

    def get_flowcell(self, obj):
        return ['{} {}'.format(
            flowcell.create_time.strftime('%d.%m.%Y'),
            flowcell.flowcell_id,
        ) for flowcell in obj.flowcell.all()]

    def get_pool(self, obj):
        return self._get_pools(obj).values_list('name', flat=True)

    def get_percentage(self, obj):
        pools = self._get_pools(obj)
        data = []


        for flowcell in obj.flowcell.all():

            flowcell_dict = {
                'flowcell_id': flowcell.flowcell_id,
                'sequencer': flowcell.sequencer.pk,
                'pools': [],
                'flowcell_create_month':int(flowcell.create_time.strftime('%m')),
                'flowcell_create_year': int(flowcell.create_time.strftime('%Y')),
                'flowcell_create_time': flowcell.create_time
            }

            count = Counter(flowcell.lanes.values_list('pool', flat=True))
            for pool in pools.filter(pk__in=count.keys()):
                libraries = pool.libraries.all()
                samples = pool.samples.all()
                items = list(itertools.chain(libraries, samples))
                total_depth = sum([x.sequencing_depth for x in items])

                # Calculate Sequencing Depth for all request's
                # libraries and samples
                libraries = pool.libraries.filter(request=obj)
                samples = pool.samples.filter(request=obj)
                library_ids = []
                sample_ids = []
                for library in libraries:
                    library_ids.append(library.pk)
                for sample in samples:
                    sample_ids.append(sample.pk)

                depth = sum(libraries.values_list(
                    'sequencing_depth', flat=True)) + \
                    sum(samples.values_list('sequencing_depth', flat=True))

                percentage = round(depth / total_depth, 2)
                if percentage == 1.0:
                    percentage = 1

                item = libraries.first() or samples.first()

                flowcell_dict['pools'].append({
                    'name': pool.name,
                    'read_length': item.read_length.pk,
                    'percentage': f'{percentage}*{count[pool.pk]}',
                    'libraries':library_ids,
                    'samples': sample_ids,
                })
            data.append(flowcell_dict)

        return data

    def get_read_length(self, obj):
        return set([x.read_length.pk for x in obj.records])

    def get_num_libraries_samples_show(self,obj):

        num_libraries = obj.libraries.count()
        num_samples = obj.samples.count()

        if num_libraries > 0:
            return f'{num_libraries} libraries'
        else:
            return f'{num_samples} samples'

    def get_num_libraries_samples(self, obj):

        flowcells = self.get_percentage(obj)

        mindt = min([d['flowcell_create_time'] for d in flowcells])

        #min_date = trunc_datetime(datetime.datetime(minYear, minMonth, 1))
        min_date = trunc_datetime(datetime.datetime(mindt.year,mindt.month,1))


        curr_date = trunc_datetime(datetime.datetime(self.context['curr_year'], self.context['curr_month'], 1))


        num_libraries = obj.libraries.count()
        num_samples = obj.samples.count()

        if num_libraries > 0:


            libcount = 0

            #for flowcell in flowcells:
            #    flowcell_dt = trunc_datetime(datetime.datetime(flowcell['flowcell_create_year'],flowcell['flowcell_create_month'],1))
            #    #if flowcell['flowcell_create_month'] == minMonth and flowcell['flowcell_create_year'] == minYear:
            #    if flowcell_dt == minDt:
            #        for pool in flowcell['pools']:
            #            libcount = libcount + len(pool['libraries'])

            '''de-coupling preparation costs from flowcell'''
            if curr_date == min_date:
                libcount = num_libraries


            return f'{libcount} libraries'


        else:
            sampcount = 0

            #for flowcell in flowcells:

             #   if flowcell['flowcell_create_month'] == minMonth and flowcell['flowcell_create_year'] == minYear:

              #      for pool in flowcell['pools']:
               #         sampcount = sampcount + len(pool['samples'])


            '''de-coupling preparation costs from flowcell'''
            if curr_date == min_date:
                sampcount = num_samples

            return f'{sampcount} samples'

    def get_library_protocol(self, obj):
        protocols = set([x.library_protocol.pk for x in obj.records])

        return protocols.pop() if protocols else ''

    def get_fixed_costs(self, obj):
        return 0

    def get_sequencing_costs(self, obj):
        return 0

    def get_preparation_costs(self, obj):
        return 0

    def get_variable_costs(self, obj):
        return 0

    def get_total_costs(self, obj):
        return 0

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        percentage = ret.get('percentage')
        library_protocol = ret.get('library_protocol')
        num_libraries_samples = ret.get('num_libraries_samples')

        fixed_costs = self.context['fixed_costs']
        preparation_costs = self.context['preparation_costs']
        sequencing_costs = self.context['sequencing_costs']

        '''
        Fix so samples of a request that have been sequenced in different months are not billed twice
        Only bill if it has been sequenced in the latest month that is in the flowcell list
        '''

        curr_date = trunc_datetime(datetime.datetime(self.context['curr_year'], self.context['curr_month'], 1))


        # Calculate Fixed Costs
        costs = 0
        for flowcell in percentage:
            dt = flowcell['flowcell_create_time']
            dt = trunc_datetime(datetime.datetime(dt.year,dt.month,1))
            #if flowcell['flowcell_create_month'] == int(self.context['curr_month']) and flowcell['flowcell_create_year'] == int(self.context['curr_year']):
            if dt == curr_date:

                for pool in flowcell['pools']:
                    costs += fixed_costs.get(flowcell['sequencer'], 0) * \
                        reduce(lambda x, y: Decimal(x) * Decimal(y),
                               pool['percentage'].split('*'))
        ret['fixed_costs'] = costs

        # Calculate Sequencing Costs
        costs = 0
        for flowcell in percentage:
            dt = flowcell['flowcell_create_time']
            dt = trunc_datetime(datetime.datetime(dt.year, dt.month, 1))
            #if flowcell['flowcell_create_month'] == self.context['curr_month'] and flowcell['flowcell_create_year'] == self.context['curr_year']:
            if dt == curr_date:
                for pool in flowcell['pools']:
                    key = f"{flowcell['sequencer']}_{pool['read_length']}"
                    costs += sequencing_costs.get(key, 0) * \
                        reduce(lambda x, y: Decimal(x) * Decimal(y),
                            pool['percentage'].split('*'))
        ret['sequencing_costs'] = costs

        # Calculate Preparation Costs
        costs = 0
        split = num_libraries_samples.split(' ')
        if split[1] == 'samples':

            costs = preparation_costs.get(library_protocol, 0) * \
                Decimal(split[0])
        else:
            try:
                price = LibraryPreparationCosts.objects.get(
                    library_protocol__name='Quality Control').price
                costs = Decimal(split[0]) * price
            except LibraryPreparationCosts.DoesNotExist:
                logger.exception(
                    f'Preparation Cost for libraries is not set.')
        ret['preparation_costs'] = costs

        ret['variable_costs'] = ret['sequencing_costs'] + \
            ret['preparation_costs']

        ret['total_costs'] = ret['fixed_costs'] + \
            ret['variable_costs']

        return ret

    def _get_pools(self, obj):
        ids1 = obj.flowcell.values_list('lanes__pool', flat=True).distinct()
        ids2 = set(itertools.chain(
            obj.libraries.values_list('pool', flat=True),
            obj.samples.values_list('pool', flat=True),
        ))
        ids = ids2.intersection(ids1)
        return self.context['pools'].filter(pk__in=ids)


class BaseSerializer(ModelSerializer):
    name = SerializerMethodField()

    class Meta:
        fields = ('name',)

    def get_name(self, obj):
        return str(obj)


class FixedCostsSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = FixedCosts
        fields = ('id', 'sequencer', 'price',) + \
            BaseSerializer.Meta.fields
        extra_kwargs = {
            'sequencer': {'required': False},
        }


class LibraryPreparationCostsSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = LibraryPreparationCosts
        fields = ('id', 'library_protocol', 'price',) + \
            BaseSerializer.Meta.fields
        extra_kwargs = {
            'library_protocol': {'required': False},
        }


class SequencingCostsSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = SequencingCosts
        fields = ('id', 'sequencer', 'read_length', 'price',) +\
            BaseSerializer.Meta.fields
        extra_kwargs = {
            'sequencer': {'required': False},
            'read_length': {'required': False},
        }
