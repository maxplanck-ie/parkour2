from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Installs the fixture(s) in the database.'

    def handle(self, *args, **options):
        # Load initial data for all apps
        self.load_common_fixtures()
        self.load_library_sample_shared_fixtures()
        self.load_sample_fixtures()
        self.load_index_generator_fixtures()
        self.load_flowcell_fixtures()
        self.load_invoicing_fixtures()

        self.stdout.write(self.style.SUCCESS(
            'Successfully loaded initial data.'))

    def load_common_fixtures(self):
        call_command('loaddata', 'organizations', app_label='common')
        call_command('loaddata', 'principal_investigators', app_label='common')
        call_command('loaddata', 'cost_units', app_label='common')

    def load_library_sample_shared_fixtures(self):
        call_command('loaddata', 'organisms',
                     app_label='library_sample_shared')

        call_command('loaddata', 'concentration_methods',
                     app_label='library_sample_shared')

        call_command('loaddata', 'read_lengths',
                     app_label='library_sample_shared')

        call_command('loaddata', 'indices_i7',
                     app_label='library_sample_shared')

        call_command('loaddata', 'indices_i5',
                     app_label='library_sample_shared')

        call_command('loaddata', 'index_types',
                     app_label='library_sample_shared')

        call_command('loaddata', 'index_pairs',
                     app_label='library_sample_shared')

        call_command('loaddata', 'library_protocols',
                     app_label='library_sample_shared')

        call_command('loaddata', 'library_types',
                     app_label='library_sample_shared')

    def load_sample_fixtures(self):
        call_command('loaddata', 'nucleic_acid_types', app_label='sample')

    def load_index_generator_fixtures(self):
        call_command('loaddata', 'pool_sizes', app_label='index_generator')

    def load_flowcell_fixtures(self):
        call_command('loaddata', 'sequencers', app_label='flowcell')

    def load_invoicing_fixtures(self):
        call_command('loaddata', 'fixed_costs', app_label='invoicing')
        call_command('loaddata', 'library_preparation_costs',
                     app_label='invoicing')
        call_command('loaddata', 'sequencing_costs', app_label='invoicing')
