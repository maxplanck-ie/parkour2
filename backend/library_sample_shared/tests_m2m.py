"""Test if django-import-export handles M2M import for IndexI7/IndexI5."""
from django.test import TestCase
from library_sample_shared.models import IndexType, IndexI7
from library_sample_shared.admin import IndexI7Resource
from tablib import Dataset

class M2MImportTest(TestCase):
    def test_m2m_import(self):
        it, _ = IndexType.objects.get_or_create(name='TestIndexType')
        
        data = Dataset(headers=['id', 'prefix', 'number', 'index', 'index_type__name'])
        data.append(['', 'Ad2.', '1', 'TAAGGCGA', 'TestIndexType'])
        
        resource = IndexI7Resource()
        result = resource.import_data(data, dry_run=False)
        
        i7 = IndexI7.objects.get(prefix='Ad2.', number='1')
        
        # Assert M2M was set
        self.assertEqual(list(i7.index_type.all()), [it])
        self.assertEqual(list(it.indices_i7.all()), [i7])
