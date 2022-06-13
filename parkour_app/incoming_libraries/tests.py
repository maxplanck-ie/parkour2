import json

from django.core.urlresolvers import reverse

from common.tests import BaseTestCase
from request.models import Request
from library.models import Library
from sample.models import Sample
from library.tests import create_library
from sample.tests import create_sample


# Views

class TestIncomingLibraries(BaseTestCase):
    """ Tests for incoming libraries and samples. """

    def setUp(self):
        user = self.create_user()
        self.create_user('non-staff@test.io', 'test', False)  # non-staff user

        # Submission completed
        self.library1 = create_library(self._get_random_name(), status=1)
        self.sample1 = create_sample(self._get_random_name(), status=1)
        self.sample2 = create_sample(self._get_random_name(), status=1)

        # Failed library
        self.library2 = create_library(self._get_random_name(), status=-1)

        self.request = Request(user=user)
        self.request.save()
        self.request.libraries.add(*[self.library1, self.library2])
        self.request.samples.add(*[self.sample1, self.sample2])

    def test_incoming_libraries_list(self):
        """ Ensure get incoming libraries and samples behaves correctly. """
        self.login()
        response = self.client.get(reverse('incoming-libraries-list'))
        data = response.json()
        libraries = [x['name'] for x in data if x['record_type'] == 'Library']
        samples = [x['name'] for x in data if x['record_type'] == 'Sample']
        self.assertTrue(response.status_code, 200)
        self.assertIn(self.library1.name, libraries)
        self.assertIn(self.sample1.name, samples)
        self.assertIn(self.sample2.name, samples)
        self.assertNotIn(self.library2.name, libraries)

    def test_incoming_libraries_list_non_staff(self):
        """Ensure error is thrown if a non-staff user tries to get the list."""
        self.client.login(email='non-staff@test.io', password='test')
        response = self.client.get(reverse('incoming-libraries-list'))
        self.assertTrue(response.status_code, 403)

    def test_update_library(self):
        """ Ensure update library behaves correctly. """
        self.client.login(email='test@test.io', password='foo-bar')
        library = create_library(self._get_random_name(), status=1)
        response = self.client.post(reverse('incoming-libraries-edit'), {
            'data': json.dumps([{
                'pk': library.pk,
                'record_type': 'Library',
                'dilution_factor': 2,
                'concentration_facility': 2.0,
            }])
        })
        updated_library = Library.objects.get(pk=library.pk)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(updated_library.dilution_factor, 2)
        self.assertEqual(updated_library.concentration_facility, 2.0)

    def test_contains_invalid_records(self):
        """
        Ensure update libraries and samples containing invalid records
        bahaves correctly.
        """
        self.client.login(email='test@test.io', password='foo-bar')
        library1 = create_library(self._get_random_name(), status=1)
        library2 = create_library(self._get_random_name(), status=1)
        response = self.client.post(reverse('incoming-libraries-edit'), {
            'data': json.dumps([{
                'pk': library1.pk,
                'record_type': 'Library',
                'concentration_facility': 2.0,
            }, {
                'pk': library2.pk,
                'record_type': 'Library',
                'dilution_factor': 'string value',
            }])
        })
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Some records cannot be updated.')
        self.assertEqual(Library.objects.get(
            pk=library1.pk).concentration_facility, 2.0)

    def test_contains_invalid_id(self):
        """
        Ensure update libraries and samples containing records with
        invalid ids bahaves correctly.
        """
        self.client.login(email='test@test.io', password='foo-bar')
        library = create_library(self._get_random_name(), status=1)
        response = self.client.post(reverse('incoming-libraries-edit'), {
            'data': json.dumps([{
                'pk': library.pk,
                'record_type': 'Library',
                'concentration_facility': 2.0,
            }, {
                'pk': 'blah',
                'record_type': 'Sample',
                'concentration_facility': 2.0,
            }])
        })
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(Library.objects.get(
            pk=library.pk).concentration_facility, 2.0)

    def test_quality_check_passed(self):
        """ Ensure quality check has passed behaves correctly. """
        self.client.login(email='test@test.io', password='foo-bar')
        library = create_library(self._get_random_name(), status=1)
        response = self.client.post(reverse('incoming-libraries-edit'), {
            'data': json.dumps([{
                'pk': library.pk,
                'record_type': 'Library',
                'quality_check': 'passed',
            }])
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(Library.objects.get(pk=library.pk).status, 2)

    def test_quality_check_multiple(self):
        """ Ensure quality check has failed behaves correctly. """
        self.client.login(email='test@test.io', password='foo-bar')
        sample1 = create_sample(self._get_random_name(), status=1)
        sample2 = create_sample(self._get_random_name(), status=1)
        response = self.client.post(reverse('incoming-libraries-edit'), {
            'data': json.dumps([{
                'pk': sample1.pk,
                'record_type': 'Sample',
                'quality_check': 'failed',
            }, {
                'pk': sample2.pk,
                'record_type': 'Sample',
                'quality_check': 'compromised',
            }])
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(Sample.objects.get(pk=sample1.pk).status, -1)
        self.assertEqual(Sample.objects.get(pk=sample2.pk).status, -2)

    def test_invalid_json(self):
        """ Ensure error is thrown if the JSON object is empty. """
        self.client.login(email='test@test.io', password='foo-bar')
        response = self.client.post(reverse('incoming-libraries-edit'), {})
        data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data['success'])
        self.assertIn('Invalid payload.', data['message'])
