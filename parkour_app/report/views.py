from datetime import datetime
from collections import OrderedDict, Counter

from django.apps import apps
from django.http import JsonResponse
from django.shortcuts import render
from django.db import connection
from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

import numpy as np
from pandas import DataFrame

from .sql import QUERY, LIBRARY_SELECT, SAMPLE_SELECT, SAMPLE_JOINS

Organization = apps.get_model('common', 'Organization')
PrincipalInvestigator = apps.get_model('common', 'PrincipalInvestigator')
LibraryProtocol = apps.get_model(
    'library_sample_shared', 'LibraryProtocol')

Library = apps.get_model('library', 'Library')
Sample = apps.get_model('sample', 'Sample')
Request = apps.get_model('request', 'Request')
Pool = apps.get_model('index_generator', 'Pool')
Sequencer = apps.get_model('flowcell', 'Sequencer')
Flowcell = apps.get_model('flowcell', 'Flowcell')
Lane = apps.get_model('flowcell', 'Lane')


class Report:
    def __init__(self, start, end):
        libraries_qs = Library.objects.select_related(
            'library_protocol').only('id', 'library_protocol__name').filter(
                create_time__gt=start, create_time__lt=end)

        samples_qs = Sample.objects.select_related(
            'library_protocol').only('id', 'library_protocol__name').filter(
                create_time__gt=start, create_time__lt=end)

        self.requests = Request.objects.select_related(
            'user__organization', 'user__pi',
        ).prefetch_related(
            Prefetch('libraries', queryset=libraries_qs,
                     to_attr='fetched_libraries'),
            Prefetch('samples', queryset=samples_qs,
                     to_attr='fetched_samples'),
        ).only(
            'id',
            'libraries',
            'samples',
            'user__organization__name',
            'user__pi__name',
        )

        lanes_qs = Lane.objects.select_related('pool').prefetch_related(
            Prefetch('pool__libraries', queryset=libraries_qs,
                     to_attr='fetched_libraries'),
            Prefetch('pool__samples', queryset=samples_qs,
                     to_attr='fetched_samples'),
        ).only('id', 'pool__libraries', 'pool__samples')

        self.flowcells = Flowcell.objects.select_related(
            'sequencer',
        ).prefetch_related(
            Prefetch('lanes', queryset=lanes_qs, to_attr='fetched_lanes'),
        ).only('id', 'sequencer__name', 'lanes')

    def get_total_counts(self):
        data = []
        num_libraries = 0
        num_samples = 0

        for req in self.requests:
            num_libraries += len(req.fetched_libraries)
            num_samples += len(req.fetched_samples)

        if num_samples > 0:
            data.append({'type': 'Samples', 'count': num_samples})

        if num_libraries > 0:
            data.append({'type': 'Libraries', 'count': num_libraries})

        return data

    def get_organization_counts(self):
        counts = {}

        for req in self.requests:
            organization = req.user.organization
            org_name = organization.name if organization else 'None'
            if org_name not in counts.keys():
                counts[org_name] = {'libraries': 0, 'samples': 0}
            counts[org_name]['libraries'] += len(req.fetched_libraries)
            counts[org_name]['samples'] += len(req.fetched_samples)

        return self._get_data(counts)

    def get_library_protocol_counts(self):
        counts = {}

        for req in self.requests:
            # Extract Library Protocols
            library_protocols = [
                x.library_protocol.name for x in req.fetched_libraries]
            sample_protocols = [
                x.library_protocol.name for x in req.fetched_samples]

            # Merge the counts
            library_cnt = {x[0]: {'libraries': x[1]}
                           for x in Counter(library_protocols).items()}
            sample_cnt = {x[0]: {'samples': x[1]}
                          for x in Counter(sample_protocols).items()}
            count = {
                k: {
                    **library_cnt.get(k, {'libraries': 0}),
                    **sample_cnt.get(k, {'samples': 0}),
                }
                for k in library_cnt.keys() | sample_cnt.keys()
            }

            for k, v in count.items():
                temp_dict = counts.get(k, {'libraries': 0, 'samples': 0})
                temp_dict['libraries'] += v['libraries']
                temp_dict['samples'] += v['samples']
                counts[k] = temp_dict

        return self._get_data(counts)

    def get_pi_counts(self):
        counts = {}

        for req in self.requests:
            pi = req.user.pi
            pi_name = pi.name if pi else 'None'
            if pi_name not in counts.keys():
                counts[pi_name] = {'libraries': 0, 'samples': 0}
            counts[pi_name]['libraries'] += len(req.fetched_libraries)
            counts[pi_name]['samples'] += len(req.fetched_samples)

        return self._get_data(counts)

    def get_sequencer_counts(self):
        counts = {}

        for flowcell in self.flowcells:
            sequencer_name = flowcell.sequencer.name
            if sequencer_name not in counts.keys():
                counts[sequencer_name] = {
                    'libraries': 0, 'samples': 0, 'runs': 0}
            counts[sequencer_name]['runs'] += 1

            pools = {x.pool for x in flowcell.fetched_lanes}
            for pool in pools:
                counts[sequencer_name]['libraries'] += \
                    len(pool.fetched_libraries)
                counts[sequencer_name]['samples'] += \
                    len(pool.fetched_samples)

        data = [
            {
                'name': name,
                'items_count': count['libraries'] + count['samples'],
                'runs_count': count['runs'],
            }
            for name, count in counts.items()
            if count['libraries'] + count['samples'] > 0
        ]

        return sorted(data, key=lambda x: x['name'])

    def get_sequencers_list(self):
        return sorted({x.sequencer.name for x in self.flowcells})

    def get_pi_sequencer_counts(self):
        sequencer_mapping = {}
        for flowcell in self.flowcells:    # gets records from flowcell
            sequencer_name = flowcell.sequencer.name
            pools = {x.pool for x in flowcell.fetched_lanes}
            for pool in pools:
                records = pool.fetched_libraries + pool.fetched_samples
                for record in records:
                    if record not in sequencer_mapping:
                        sequencer_mapping[record] = []
                    sequencer_mapping[record].append(sequencer_name)
        items = sequencer_mapping.keys()

        pi_mapping = {}
        for req in self.requests:    # gets records from requests
            pi = req.user.pi
            pi_name = pi.name if pi else 'None'
            records = req.fetched_libraries + req.fetched_samples

            pi_mapping.update({
                record: pi_name for record in records if record in items
            })

        pairs = []
        for k, v in sequencer_mapping.items():
            for sequencer_name in v:
                try:
                    pairs.append((pi_mapping[k], sequencer_name))
                except KeyError:    # KeyError if record exists under flowcell but the correspond. request was deleted.
                    pass    # could add a warning pop-up here
        counts = Counter(pairs)

        data = {}
        for item, count in counts.items():
            if item[0] not in data:
                data[item[0]] = {}
            data[item[0]][item[1]] = count

        return OrderedDict(sorted(data.items()))

    def get_turnaround(self):
        query = '''
        CREATE TEMPORARY TABLE IF NOT EXISTS temp1 AS SELECT
            L.id,
            CAST('Library' AS CHAR(7)) rtype,
            L.create_time date1,
            CAST(NULL AS TIMESTAMPTZ) date2
        FROM library_library L;

        CREATE TEMPORARY TABLE IF NOT EXISTS temp2 AS SELECT
            L.id,
            MIN(F.create_time) date3
        FROM library_library L
        LEFT JOIN index_generator_pool_libraries PR
            ON L.id = PR.library_id
        LEFT JOIN index_generator_pool P
            ON PR.pool_id = P.id
        LEFT JOIN flowcell_lane La
            ON P.id = La.pool_id
        LEFT JOIN flowcell_flowcell_lanes FL
            ON La.id = FL.lane_id
        LEFT JOIN flowcell_flowcell F
            ON FL.flowcell_id = F.id
        GROUP BY L.id;

        CREATE TEMPORARY TABLE IF NOT EXISTS temp3 AS SELECT
            S.id,
            CAST('Sample' AS CHAR(6)) rtype,
            S.create_time date1,
            LP.create_time date2
        FROM sample_sample S
        LEFT JOIN library_preparation_librarypreparation LP
            ON S.id = LP.sample_id;

        CREATE TEMPORARY TABLE IF NOT EXISTS temp4 AS SELECT
            S.id,
            MIN(F.create_time) date3
        FROM sample_sample S
        LEFT JOIN index_generator_pool_samples PR
            ON S.id = PR.sample_id
        LEFT JOIN index_generator_pool P
            ON PR.pool_id = P.id
        LEFT JOIN flowcell_lane L
            ON P.id = L.pool_id
        LEFT JOIN flowcell_flowcell_lanes FL
            ON L.id = FL.lane_id
        LEFT JOIN flowcell_flowcell F
            ON FL.flowcell_id = F.id
        GROUP BY S.id;

        SELECT
            rtype, date1, date2, date3
        FROM (
            SELECT *
            FROM temp1 t1
            LEFT JOIN temp2 t2 ON t1.id = t2.id
            UNION ALL
            SELECT *
            FROM temp3 t1
            LEFT JOIN temp4 t2 ON t1.id = t2.id
        ) t
        '''

        with connection.cursor() as c:
            c.execute(query)
            columns = [x[0] for x in c.description]
            df = DataFrame(c.fetchall(), columns=columns)

        df['Request -> Preparation'] = df.date2 - df.date1
        df['Preparation -> Sequencing'] = df.date3 - df.date2
        df['Complete Workflow'] = df.date3 - df.date1

        agg_samples_df = \
            df[df.rtype == 'Sample'].aggregate(['mean', 'std']).fillna(0)
        agg_samples_df = (agg_samples_df / np.timedelta64(1, 'D')).astype(int)

        agg_libraries_df = df[df.rtype == 'Library'].iloc[:, -1]\
            .aggregate(['mean', 'std']).fillna(0)
        agg_libraries_df = \
            (agg_libraries_df / np.timedelta64(1, 'D')).astype(int)

        columns = [
            'Turnaround',
            'Sample (days)',
            'Sample Deviation (days)',
            'Library (days)',
            'Library Deviation (days)',
        ]

        result_df = DataFrame(columns=columns)
        result_df[columns[0]] = df.columns[4:]
        result_df[columns[1]] = agg_samples_df.loc['mean'].values
        result_df[columns[2]] = agg_samples_df.loc['std'].values
        result_df[columns[3]] = [0] * 2 + [agg_libraries_df.loc['mean']]
        result_df[columns[4]] = [0] * 2 + [agg_libraries_df.loc['std']]

        return {
            'columns': columns,
            'rows': result_df.T.to_dict().values(),
        }

    @staticmethod
    def _get_data(counts):
        data = [
            {
                'name': name,
                'libraries_count': count['libraries'],
                'samples_count': count['samples'],
            }
            for name, count in counts.items()
            if count['libraries'] + count['samples'] > 0
        ]

        return sorted(data, key=lambda x: x['name'])


@login_required
@staff_member_required
def report(request):
    data = {}

    now = datetime.now()
    start = request.GET.get('start', now)
    end = request.GET.get('end', now)

    try:
        start = datetime.strptime(start, '%d.%m.%Y') \
            if type(start) is str else start
    except ValueError:
        start = now
    finally:
        start = start.replace(hour=0, minute=0)

    try:
        end = datetime.strptime(end, '%d.%m.%Y') \
            if type(end) is str else end
    except ValueError:
        end = now
    finally:
        end = end.replace(hour=23, minute=59)

    if start > end:
        start = end.replace(hour=0, minute=0)

    report = Report(start, end)

    # Total Sample Count
    data['total_counts'] = report.get_total_counts()

    # Count by Organization
    data['organization_counts'] = report.get_organization_counts()

    # Count by Library Protocol
    data['protocol_counts'] = report.get_library_protocol_counts()

    # Count by Principal Investigator
    data['pi_counts'] = report.get_pi_counts()

    # Count by Sequencer
    data['sequencer_counts'] = report.get_sequencer_counts()

    # Count by PI and Sequencer
    data['sequencers_list'] = report.get_sequencers_list()
    data['libraries_on_sequencers_count'] = report.get_pi_sequencer_counts()

    # Count days
    data['turnaround'] = report.get_turnaround()

    return render(request, 'report.html', data)


@login_required
@staff_member_required
def database(request):
    return render(request, 'database.html')

# @print_sql_queries
@login_required
@staff_member_required
def database_data(request):
    with connection.cursor() as c:
        query = QUERY.format(
            table_name='library',
            table_name_plural='libraries',
            select=LIBRARY_SELECT,
            joins='',
        )
        c.execute(query)
        columns = [col[0] for col in c.description]
        libraries = [dict(zip(columns, row)) for row in c.fetchall()]

        query = QUERY.format(
            table_name='sample',
            table_name_plural='samples',
            select=SAMPLE_SELECT,
            joins=SAMPLE_JOINS,
        )
        c.execute(query)
        columns = [col[0] for col in c.description]
        samples = [dict(zip(columns, row)) for row in c.fetchall()]

    data = sorted(libraries + samples, key=lambda x: (
        int(x['Barcode'][:2]),
        int(x['Barcode'][3:]),
    ))

    columns = [
        'Name',
        'Barcode',
        'Status',
        'Request',
        'User',
        'Library Type',
        'Library Protocol',
        'Concentration',
        'Sequencing Depth',
        'Read Length',
        'Concentration Method',
        'Equal Representation of Nucleotides',
        'Index Type',
        'Index Reads',
        'Index I7 ID',
        'Index I7',
        'Index I5 ID',
        'Index I5',
        'Amplification Cycles',
        'Dilution Factor',
        'Concentration (Facility)',
        'Sample Volume (Facility)',
        'Amount (Facility)',
        'Size Distribution (Facility)',
        'Concentration Method (Facility)',
        'RNA Quality (Facility)',
        'Organism',
        'Concentration C1',
        'RNA Quality',
        'Nucleic Acid Type',
        'Starting Amount',
        'Spike-in Volume',
        'PCR Cycles',
        'Concentration Library',
        'Mean Fragment Size',
        'nM',
        'qPCR Result',
        'qPCR Result (Facility)',
        'Pool',
        'Pool Size',
        'Flowcell ID',
        'Flowcell create time',
        'Sequencer',
    ]

    return JsonResponse({'columns': columns, 'data': data})
