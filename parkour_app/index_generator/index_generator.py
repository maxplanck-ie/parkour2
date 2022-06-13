import re
import random
import string
import itertools
from collections import namedtuple, OrderedDict, defaultdict, Counter

from django.apps import apps

IndexI7 = apps.get_model('library_sample_shared', 'IndexI7')
IndexI5 = apps.get_model('library_sample_shared', 'IndexI5')
IndexPair = apps.get_model('library_sample_shared', 'IndexPair')
Library = apps.get_model('library', 'Library')
Sample = apps.get_model('sample', 'Sample')

Pair = namedtuple('Pair', ['index1', 'index2', 'coordinate'])


class IndexRegistry:
    """
    Class for storing fetched and sorted indices i7/i5 and index pairs.
    """

    def __init__(self, mode, index_types, start_coord='A1', direction='right'):
        self.indices = {}
        self.pairs = {}

        # In case if an empty string was passed
        start_coord = start_coord if start_coord else 'A1'
        direction = direction if direction else 'right'

        self.mode = mode
        self.index_types = index_types
        char_coord, num_coord = self.split_coordinate(start_coord)

        # Fetch indices and index pairs
        for index_type in self.index_types:
            if index_type.format == 'single':
                self.fetch_indices(index_type)
            else:
                self.fetch_pairs(index_type, char_coord, num_coord, direction)

    def fetch_indices(self, index_type):
        """ Fetch indices i7 and i5 for a given index type. """
        if index_type.pk not in self.indices.keys():
            self.indices[index_type.pk] = {'i7': [], 'i5': []}

        self.indices[index_type.pk]['i7'] = self.to_list(
            index_type.format,
            index_type.pk,
            index_type.read_type,
            index_type.indices_i7.all(),
        )

        if self.mode == 'dual':
            self.indices[index_type.pk]['i5'] = self.to_list(
                index_type.format,
                index_type.pk,
                index_type.read_type,
                index_type.indices_i5.all(),
            )

    def fetch_pairs(self, index_type, char_coord, num_coord, direction):
        """
        Fetch index pairs (Index i7 + Index i5) for a given index type,
        start coordinate, and direction.
        """
        if index_type.pk not in self.pairs.keys():
            self.pairs[index_type.pk] = []

        index_pairs = IndexPair.objects.filter(
            index_type=index_type).select_related('index1', 'index2')

        # Sort index pairs according to the chosen direction
        if direction == 'right':
            index_pairs = index_pairs.order_by('char_coord', 'num_coord')
        elif direction == 'down':
            index_pairs = index_pairs.order_by('num_coord', 'char_coord')
        else:  # diagonal
            index_pairs = self.get_diagonal(index_pairs)

        start_idx = None
        for i, pair in enumerate(index_pairs):
            if pair.char_coord == char_coord and pair.num_coord == num_coord:
                start_idx = i
                break

        if start_idx is None:
            raise ValueError(
                f'No index pairs for Index Type "{index_type.name}" ' +
                f'and start coordinate "{char_coord + str(num_coord)}".'
            )

        # Make the index pairs list begin with a provided start coordinate
        index_pairs = index_pairs[start_idx:] + index_pairs[:start_idx]

        for pair in index_pairs:
            index1 = self.create_index_dict(
                index_type.format, index_type.pk, index_type.read_type,
                pair.index1.prefix, pair.index1.number,
                pair.index1.index, pair.coordinate,
                )

            if self.mode == 'dual':
                index2 = self.create_index_dict(
                    index_type.format, index_type.pk, index_type.read_type,
                    pair.index2.prefix, pair.index2.number,
                    pair.index2.index, pair.coordinate,
                )
            else:
                index2 = self.create_index_dict()

            self.pairs[index_type.pk].append(
                Pair(index1, index2, pair.coordinate))

    def get_diagonal(self, index_pairs):
        """ Sort index pairs diagonally. """
        letters = string.ascii_uppercase  # ABCD...
        last_coord = max([(x.char_coord, x.num_coord) for x in index_pairs])
        char_coord, num_coord = last_coord  # e.g., 'H' and 12
        rows = letters[:letters.index(char_coord) + 1]

        # Build coordinate matrix
        # A1, A2, ... , A12
        # ...
        # H1, H2, ... , H12
        coord_matrix = [
            [char + str(num + 1) for num in range(num_coord)]
            for char in list(rows)
        ]

        # Find diagonals, e.g., H1, G1, H2, ... , A1, B2, ... , A12
        diags = defaultdict(list)
        for i in range(len(rows)):
            for j in range(num_coord):
                diags[j - i].append(coord_matrix[i][j])

        coords = itertools.chain(*[diags[i] for i in sorted(diags)])
        order = {k: i for i, k in enumerate(coords)}

        # Return index pairs sorted according to the custom order
        return sorted(index_pairs, key=lambda x: order[x.coordinate])

    def get_indices(self, index_type_id, index_group):
        """
        Return a list of indices for a given index type id and index group.
        """
        return self.indices.get(
            index_type_id, {'i7': [], 'i5': []}).get(index_group, [])

    def get_pairs(self, index_type_id):
        """ Return a list of index pairs for a given index type id. """
        return self.pairs.get(index_type_id, [])

    def to_list(self, format, index_type, read_type, indices):
        """ Return a list of index dicts. """
        return list(map(lambda x: self.create_index_dict(
            format, index_type, read_type, x.prefix, x.number, x.index), indices))

    @staticmethod
    def create_index_dict(format='', index_type='', read_type='', prefix='',
                          number='', index='', coordinate='',
                          is_library=False):
        return {
            'format': format,
            'index_type': index_type,
            'read_type' : read_type,
            'prefix': prefix,
            'number': number,
            'index': index,
            'coordinate': coordinate,
            'is_library': is_library,
        }

    @staticmethod
    def split_coordinate(coordinate):
        """
        Split a submitted coordinate into a character and a numeric parts.
        """
        match = re.match(r'([A-Z]+)([0-9]+)', coordinate)
        if not match:
            raise ValueError('Invalid start coordinate.')
        return match[1], int(match[2])


class IndexGenerator:
    """
    Main class that fetches provided libraries and samples, checks the
    compatibility of their index types, generates indices, and assigns
    them to the libraries and samples.
    """
    index_registry = None
    libraries = None
    samples = None
    num_libraries = 0
    num_samples = 0
    index_length = 0
    format = ''
    mode = ''
    MAX_ATTEMPTS = 30
    MAX_RANDOM_SAMPLES = 5

    def __init__(self, library_ids, sample_ids, start_coord, direction):
        self._result = []

        self.libraries = Library.objects.filter(
            pk__in=library_ids
        ).select_related(
            'read_length',
            'index_type',
        ).prefetch_related(
            'index_type__indices_i7',
            'index_type__indices_i5',
        ).only(
            'id',
            'name',
            'barcode',
            'sequencing_depth',
            'read_length__id',
            'index_type',
            'index_i7',
            'index_i5',
        ).order_by('barcode')

        self.samples = Sample.objects.filter(
            pk__in=sample_ids
        ).select_related(
            'read_length',
            'index_type',
        ).prefetch_related(
            'index_type__indices_i7',
            'index_type__indices_i5',
        ).only(
            'id',
            'name',
            'barcode',
            'sequencing_depth',
            'read_length__id',
            'index_type',
        ).order_by(
            'index_type__format',
            'index_type__id',
            'barcode',
        )

        self.num_libraries = len(self.libraries)
        self.num_samples = len(self.samples)

        if self.num_samples == 0:
            raise ValueError('No samples provided.')

        records = list(itertools.chain(self.libraries, self.samples))
        read_lengths = [x.read_length for x in records]
        if len(set(read_lengths)) != 1:
            raise ValueError(
                'Read Length must be the same for all libraries and samples.')

        index_types = self.validate_index_types(records)

        self.index_registry = IndexRegistry(
            self.mode, index_types, start_coord, direction)

    def validate_index_types(self, records):
        """ Check the compatibility of provided libraries and samples. """
        index_types = [x.index_type for x in records]
        index_types = list(filter(None, index_types))

        if len(index_types) != len(records):
            raise ValueError(
                'Index Type must be set for all libraries and samples.')
        index_types = list(set(index_types))

        is_dual = [x.is_dual for x in index_types]
        if len(set(is_dual)) != 1:
            raise ValueError('Mixed single/dual indices are not allowed.')
        self.mode = 'dual' if is_dual[0] else 'single'

        index_read_type = [x.read_type for x in index_types]
        if len(set(index_read_type)) != 1:
            raise ValueError('Mixed long-read and short-read indices are not allowed')

        index_lengths = [x.index_length for x in index_types]
        if len(set(index_lengths)) != 1:
            raise ValueError('Index Types with mixed index lengths ' +
                             'are not allowed.')

        self.index_length = int(index_lengths[0])

        return index_types

    def generate(self):
        """ Main method that generates indices. """
        if self.num_libraries > 0:
            self.add_libraries_to_result()

        # If a single sample was selected, then add it directly to the result
        if not any(self._result) and self.num_samples == 1:
            index_i7, index_i5 = self.find_random(self.samples[0])
            self._result.append(
                self.create_result_dict(
                    self.samples[0], index_i7, index_i5))
            return self.result

        depths = [x.sequencing_depth for x in self.samples]
        init_index_pairs, init_indices_i7, init_indices_i5 = [], [], []

        if any(self._result):
            depths = [x['sequencing_depth'] for x in self._result] + depths

            # If there are libraries in the result, extract their indices
            for item in self._result:
                init_index_pairs.append((item['index_i7'], item['index_i5']))
                init_indices_i7.append(item['index_i7'])
                init_indices_i5.append(item['index_i5'])

        depths = self.sort_sequencing_depths(depths)

        # Group samples by the index type format
        plate_samples, tube_samples = [], []
        for sample in self.samples:
            if sample.index_type.format == 'plate':
                plate_samples.append(sample)
            else:
                tube_samples.append(sample)

        # If the number of samples with index type 'plate' is large enough,
        # or read_type is "long"
        # take pairs in the selected order (don't actually generate them)
        if len(plate_samples) > self.MAX_RANDOM_SAMPLES or self.samples[0].index_type.read_type == 'long':
            pairs = self.find_pairs_fixed(plate_samples, init_index_pairs)
            for pair in pairs:
                init_index_pairs.append(pair)
                init_indices_i7.append(pair[0])
                init_indices_i5.append(pair[1])
            plate_samples = []

        # Ignore the first sample because it will be processed separately
        if not any(init_index_pairs):
            if self.samples[0].index_type.format == 'plate':
                plate_samples.pop(0)
            else:
                tube_samples.pop(0)

        attempt = 0
        is_ok = False

        while not is_ok and attempt < self.MAX_ATTEMPTS:
            init_pairs = list(init_index_pairs)
            init_i7 = list(init_indices_i7)
            init_i5 = list(init_indices_i5)

            if not any(init_pairs):
                pair_1 = self.find_random(self.samples[0])
                init_pairs.append(pair_1)
                init_i7.append(pair_1[0])
                init_i5.append(pair_1[1])

            # Find index pairs
            pairs = self.find_pairs(plate_samples, depths, init_pairs)
            # Extract indices from the pairs
            # for pair in pairs[1:]:
            for pair in pairs[len(init_pairs):]:
                init_i7.append(pair[0])
                init_i5.append(pair[1])

            # Find indices I7 and I5 independently
            indices_i7 = self.find_indices(
                tube_samples, depths, 'i7', init_i7)
            if self.mode == 'single':
                indices_i5 = [
                    self.index_registry.create_index_dict()] * len(indices_i7)
            else:
                indices_i5 = self.find_indices(
                    tube_samples, depths, 'i5', init_i5)

            # Ensure uniqueness
            i7_extracted = [x['index'] for x in indices_i7]
            i5_extracted = [x['index'] for x in indices_i5]
            all_pairs = list(zip(i7_extracted, i5_extracted))

            # If all pairs are unique, exit. Otherwise, re-generate the indices
            if len(all_pairs) == len(set(all_pairs)):
                is_ok = True

            attempt += 1

        if not is_ok:
            raise ValueError('Failed to generate indices.')

        # Skip indices which are already in the result
        indices_i7 = indices_i7[len(self._result):]
        indices_i5 = indices_i5[len(self._result):]

        # Add generated indices to the result
        for i, sample in enumerate(self.samples):
            self._result.append(
                self.create_result_dict(
                    sample, indices_i7[i], indices_i5[i]))

        return self.result

    def add_libraries_to_result(self):
        """ Add all libraries directly to the result. """

        def idx_dict(class_model, index, index_type):
            idx = class_model.objects.filter(
                index=index, index_type=index_type)
            if idx:
                idx = self.index_registry.create_index_dict(
                    index_type.format, index_type.pk, index_type.read_type, idx[0].prefix,
                    idx[0].number, idx[0].index, is_library=True)
            else:
                idx = self.index_registry.create_index_dict(
                    index=index, is_library=True)
            return idx

        no_index = []
        with_index = []

        for library in self.libraries:
            index_i7 = idx_dict(IndexI7, library.index_i7, library.index_type)
            index_i5 = self.index_registry.create_index_dict(is_library=True)

            if self.mode == 'dual':
                index_i5 = idx_dict(
                    IndexI5, library.index_i5, library.index_type)

            d = self.create_result_dict(library, index_i7, index_i5)
            if d['index_i7']['prefix'] != '':
                with_index.append(d)
            else:
                no_index.append(d)

        with_index = sorted(with_index, key=lambda x: (
            x['index_i7']['prefix'], int(x['index_i7']['number'])
        ))

        self._result.extend(no_index + with_index)

    def find_random(self, sample):
        """ Find a pair of random indices I7/I5 for a given sample. """

        if sample.index_type.format == 'single':
            index_i7 = random.choice(
                self.index_registry.get_indices(sample.index_type.pk, 'i7'))
            index_i5 = self.index_registry.create_index_dict()
            if self.mode == 'dual':
                index_i5 = random.choice(
                    self.index_registry.get_indices(
                        sample.index_type.pk, 'i5'))
            return (index_i7, index_i5)

        else:
            pair = random.choice(
                self.index_registry.get_pairs(sample.index_type.pk))
            return (pair.index1, pair.index2)

    def find_indices(self, samples, depths, index_group, init_indices):
        """ Generate indices for given samples and index group (I7/I5). """
        if not any(samples):
            return init_indices

        indices = list(init_indices)

        for sample in samples:
            index = self.find_index(
                sample, index_group, indices, depths)
            if 'index' not in index:
                raise ValueError('Index not found.')
            index = index['index']
            indices.append(index)

        if len(indices) == len(init_indices) + len(samples):
            library_indices = [x for x in indices if x['is_library']]
            plate_indices = [x for x in indices if x['format'] ==
                             'plate' and not x['is_library']]
            tube_indices = [x for x in indices if x['format'] ==
                            'single' and not x['is_library']]
            return library_indices + plate_indices + \
                self.sort_indices(tube_indices)
        raise ValueError(f'Could not generate indices "{index_group}" ' +
                         'for the selected samples.')


    def find_index(self, sample, index_group, current_indices, depths):
        """ Helper function for `find_indices()`. """
        indices_in_result = [x['index'] for x in current_indices]
        result_index = {'avg_score': 100.0}

        indices = list(self.index_registry.get_indices(
            sample.index_type.pk, index_group))
        random.shuffle(indices)

        # Ensure uniqueness
        if self.mode == 'single':
            indices = [
                x for x in indices
                if x['index'] not in indices_in_result
            ]

        # Calculate color distribution
        color_distribution, total_depth = self.calculate_color_distribution(
            indices_in_result, depths, sample)

        for index in indices:
            if sample.index_type.read_type == 'long':
                result_index = {'avg_score': 999, 'index': index}  # don't need to check score
            else:
                converted_index = self.convert_index(index['index'])
                scores = self.calculate_scores(
                    sample, converted_index, color_distribution, total_depth)
                avg_score = sum(scores) / self.index_length
                if avg_score < result_index['avg_score']:
                    result_index = {'avg_score': avg_score, 'index': index}

        return result_index

    def find_pairs(self, samples, depths, init_pairs):
        """ Generate index pairs for given samples. """
        if not any(samples):
            return init_pairs
        pairs = list(init_pairs)

        for sample in samples:
            pair = self.find_pair(sample, depths, pairs)
            if 'pair' not in pair:
                raise ValueError('Pair not found.')
            pair = pair['pair']
            pairs.append(pair)

        if len(pairs) == len(init_pairs) + len(samples):
            library_pairs = [x for x in pairs if x[0]['is_library']]
            plate_pairs = [x for x in pairs if not x[0]['is_library']]
            if len(plate_pairs) <= self.MAX_RANDOM_SAMPLES:
                plate_pairs = self.sort_pairs(plate_pairs)
            return library_pairs + plate_pairs

        raise ValueError('Could not generate index pairs for the ' +
                         'selected samples.')

    def find_pair(self, sample, depths, current_pairs):
        """ Helper function for `find_pairs()`. """
        result_pair = {'avg_score': 100.0}
        pairs = list(self.index_registry.get_pairs(sample.index_type.pk))
        random.shuffle(pairs)

        # Ensure uniqueness
        if self.mode == 'single':
            pairs = [
                x for x in pairs
                if (x.index1, x.index2) not in current_pairs
            ]

        if self.mode == 'single':
            indices_in_result = list(map(
                lambda x: x[0]['index'], current_pairs))
        else:
            indices_in_result = list(map(
                lambda x: x[0]['index'] + x[1]['index'],
                current_pairs,
            ))

        # Calculate color distribution
        index_length = len(indices_in_result[0])
        color_distribution, total_depth = self.calculate_color_distribution(
            indices_in_result, depths, sample)

        for pair in pairs:
            if sample.index_type.read_type == 'long':
                result_pair = {
                    'avg_score': 999,
                    'pair': (pair.index1, pair.index2),
                }
            else:
                converted_index = self.convert_index(
                    self._concat_index_pair(pair))
                scores = self.calculate_scores(
                    sample, converted_index, color_distribution, total_depth)
                avg_score = sum(scores) / index_length
                if avg_score < result_pair['avg_score']:
                    result_pair = {
                        'avg_score': avg_score,
                        'pair': (pair.index1, pair.index2),
                    }

        return result_pair

    def find_pairs_fixed(self, plate_samples, init_index_pairs):
        """
        Return subsequent index pairs from the Index Registry
        starting from the first one.
        """
        result = []
        indices_in_result = [(x[0]['index'], x[1]['index']) for x in init_index_pairs]
        # Group by index type
        samples_dict = OrderedDict()
        for sample in plate_samples:
            if sample.index_type.pk not in samples_dict:
                samples_dict[sample.index_type.pk] = []
            samples_dict[sample.index_type.pk].append(sample)

        for index_type_id, samples in samples_dict.items():
            pairs = self.index_registry.get_pairs(index_type_id)
            # ensure uniqueness
            if self.mode == 'single':
                pairs = [
                    x for x in pairs
                    if (x.index1['index'], x.index2['index']) not in indices_in_result
                ]
            if len(samples) > len(pairs):
                raise IndexError(f'Not enough indices of type {sample.index_type} for given number of samples')
            for i, sample in enumerate(samples):
                pair = pairs[i]
                result.append((pair.index1, pair.index2))

        return result

    def calculate_color_distribution(self, indices, sequencing_depths, sample):
        total_depth = 0
        index_length = len(indices[0])
        color_distribution = [{'G': 0, 'R': 0} for _ in range(index_length)]
        for i, index in enumerate(indices):
            idx = self.convert_index(index)
            for cycle in range(index_length):
                color = idx[cycle]
                color_distribution[cycle][color] += sequencing_depths[i]
            total_depth += sequencing_depths[i]
        total_depth += sample.sequencing_depth
        return color_distribution, total_depth

    def calculate_scores(self, current_sample, current_converted_index,
                         current_color_distribution, total_depth):
        """
        Calculate the scores for a given sample.

        Score is an absolute difference between the sequencing depths of
        the two indices divided by the total sequencing depth (in %).

        The ideal score is 0.0 (50% green and 50% red),
        an acceptable score is 60.0 (80%/20% or 20%/80%).

        If the score > 60%, then the indices are not compatible.
        """
        distribution = list(current_color_distribution)
        result = []

        for cycle in range(len(current_converted_index)):
            color = current_converted_index[cycle]
            distribution[cycle][color] += current_sample.sequencing_depth

            if distribution[cycle]['G'] > 0 and distribution[cycle]['R'] > 0:
                difference = abs((distribution[cycle]['G'] -
                                  distribution[cycle]['R']) /
                                 total_depth) * 100
                result.append(difference)
            else:
                result.append(100.0)

        return result

    def _concat_index_pair(self, pair):
        return pair.index1['index'] + pair.index2['index'] \
            if self.mode == 'dual' else pair.index1['index']

    @property
    def result(self):
        """ Construct a list of all records and their indices. """
        result = []

        for record in self._result:
            index_i7 = record['index_i7']
            index_i5 = record['index_i5']
            rec = dict(record)

            rec['coordinate'] = index_i7['coordinate']
            rec['index_i7_id'] = index_i7['prefix'] + index_i7['number']
            rec['index_i5_id'] = index_i5['prefix'] + index_i5['number']

            # Needed for the client
            for i in range(len(index_i7['index'])):
                rec[f'index_i7_{i + 1}'] = index_i7['index'][i]
            for i in range(len(index_i5['index'])):
                rec[f'index_i5_{i + 1}'] = index_i5['index'][i]

            result.append(rec)

        return result

    @staticmethod
    def sort_sequencing_depths(depths):
        """ Sort sequencing depths to improve the result. """
        counter = Counter(depths)
        keys = counter.keys()
        min_value, max_value = min(keys), max(keys)

        if min_value == max_value:
            return depths
        elif counter[min_value] >= counter[max_value]:
            return sorted(depths)
        else:
            return sorted(depths, reverse=True)

    @staticmethod
    def convert_index(index):
        """ Convert A/C into R (red) and T into G (green). """
        return re.sub('T', 'G', re.sub('A|C', 'R', index))

    @staticmethod
    def sort_indices(indices):
        """ Sort indices I7/I5 by ID. """
        return sorted(
            indices, key=lambda x: (x['index_type'], int(x['number'])))

    @staticmethod
    def sort_pairs(pairs):
        """ Sort index pairs (only by Index I7 ID). """
        return sorted(
            pairs, key=lambda x: (x[0]['index_type'], int(x[0]['number'])))

    @staticmethod
    def create_result_dict(obj, index_i7, index_i5):
        return {
            'pk': obj.pk,
            'name': obj.name,
            'record_type': obj.__class__.__name__,
            'read_length': obj.read_length_id,
            'sequencing_depth': obj.sequencing_depth,
            'index_i7': index_i7,
            'index_i5': index_i5,
        }
