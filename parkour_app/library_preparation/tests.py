import json

from django.core.urlresolvers import reverse

from common.tests import BaseTestCase
from common.utils import get_random_name
from sample.tests import create_sample
from request.models import Request
from index_generator.tests import create_pool
from .models import LibraryPreparation


def create_library_preparation_obj(sample_name, user, sample_status):
    sample = create_sample(sample_name, status=sample_status)
    sample.save()

    request = Request(user=user)
    request.save()
    request.samples.add(sample)

    pool = create_pool(user)
    pool.samples.add(sample)

    return LibraryPreparation.objects.get(sample=sample)


# Models

class TestLibraryPreparationModel(BaseTestCase):
    def setUp(self):
        self.user = self.create_user()
        self.library_prep_obj = create_library_preparation_obj(
            self._get_random_name(), self.user, 2
        )

    def test_name(self):
        self.assertTrue(isinstance(self.library_prep_obj, LibraryPreparation))
        self.assertEqual(str(self.library_prep_obj), '{} ({})'.format(
            self.library_prep_obj.sample.name,
            self.library_prep_obj.sample.barcode,
        ))

    def test_create_library_preparation_object(self):
        """
        Ensure a Library Preparation object is created when a sample
        is added to a pool.
        """
        sample = create_sample(get_random_name(), 2)
        pool = create_pool(self.user)
        pool.samples.add(sample)
        self.assertEqual(
            LibraryPreparation.objects.filter(sample=sample).count(), 1)


# Views

class TestLibraryPreparation(BaseTestCase):
    def setUp(self):
        self.user = self.create_user()

    def test_library_preparation_list(self):
        """ Ensure get library preparation list behaves correctly. """
        self.login()

        library_prep_obj1 = create_library_preparation_obj(
            self._get_random_name(), self.user, 2
        )
        library_prep_obj2 = create_library_preparation_obj(
            self._get_random_name(), self.user, -1
        )

        response = self.client.get(reverse('library-preparation-list'))
        data = response.json()
        objects = [x['name'] for x in data]
        self.assertEqual(response.status_code, 200)
        self.assertIn(library_prep_obj1.sample.name, objects)
        self.assertNotIn(library_prep_obj2.sample.name, objects)

    def test_library_preparation_list_non_staff(self):
        """Ensure error is thrown if a non-staff user tries to get the list."""
        self.create_user('non-staff@test.io', 'test', False)
        self.client.login(email='non-staff@test.io', password='test')
        response = self.client.get(reverse('library-preparation-list'))
        self.assertTrue(response.status_code, 403)

    def test_update_library_preparation_object(self):
        """ Ensure update library preparation object behaves correctly. """
        self.client.login(email='test@test.io', password='foo-bar')

        obj = create_library_preparation_obj(
            self._get_random_name(), self.user, 2
        )

        response = self.client.post(reverse('library-preparation-edit'), {
            'data': json.dumps([{
                'pk': obj.pk,
                'starting_amount': 1.0,
                'spike_in_description': 'blah',
            }])
        })
        updated_obj = LibraryPreparation.objects.get(pk=obj.pk)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(updated_obj.starting_amount, 1.0)
        self.assertEqual(updated_obj.spike_in_description, 'blah')

    def test_update_converted_sample(self):
        """ Ensure update converted sample's field behaves correctly. """
        self.client.login(email='test@test.io', password='foo-bar')

        obj = create_library_preparation_obj(
            self._get_random_name(), self.user, 2
        )

        response = self.client.post(reverse('library-preparation-edit'), {
            'data': json.dumps([{
                'pk': obj.pk,
                'concentration_sample': 2.0,
                'comments_facility': 'blah',
            }])
        })
        updated_sample = LibraryPreparation.objects.get(pk=obj.pk).sample
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(updated_sample.concentration_facility, 2.0)
        self.assertEqual(updated_sample.comments_facility, 'blah')

    def test_contains_invalid_objects(self):
        """
        Ensure update library preparation objects containing invalid objects
        behaves correctly.
        """
        self.client.login(email='test@test.io', password='foo-bar')

        obj1 = create_library_preparation_obj(
            self._get_random_name(), self.user, 2
        )

        obj2 = create_library_preparation_obj(
            self._get_random_name(), self.user, 2
        )

        response = self.client.post(reverse('library-preparation-edit'), {
            'data': json.dumps([{
                'pk': obj1.pk,
                'starting_amount': 1.0,
            }, {
                'pk': obj2.pk,
                'pcr_cycles': 'blah',
            }])
        })
        data = response.json()
        updated_obj = LibraryPreparation.objects.get(pk=obj1.pk)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Some records cannot be updated.')
        self.assertEqual(updated_obj.starting_amount, 1.0)

    def test_update_invalid_library_preparation_object(self):
        """
        Ensure update invalid library preparation objects behaves correctly.
        """
        self.client.login(email='test@test.io', password='foo-bar')

        obj = create_library_preparation_obj(
            self._get_random_name(), self.user, 2
        )

        response = self.client.post(reverse('library-preparation-edit'), {
            'data': json.dumps([{
                'pk': obj.pk,
                'starting_amount': 'blah',
            }])
        })
        data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Invalid payload.')

    def test_contains_invalid_id(self):
        """
        Ensure update library preparation object containing records with
        invalid ids bahaves correctly.
        """
        self.client.login(email='test@test.io', password='foo-bar')

        obj = create_library_preparation_obj(
            self._get_random_name(), self.user, 2
        )

        response = self.client.post(reverse('library-preparation-edit'), {
            'data': json.dumps([{
                'pk': obj.pk,
                'starting_amount': 1.0,
            }, {
                'pk': 'blah',
                'pcr_cycles': 2,
            }])
        })
        data = response.json()
        updated_obj = LibraryPreparation.objects.get(pk=obj.pk)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(updated_obj.starting_amount, 1.0)

    def test_quality_check_passed(self):
        """ Ensure quality check has passed behaves correctly. """
        self.client.login(email='test@test.io', password='foo-bar')

        obj = create_library_preparation_obj(
            self._get_random_name(), self.user, 2
        )

        response = self.client.post(reverse('library-preparation-edit'), {
            'data': json.dumps([{
                'pk': obj.pk,
                'quality_check': 'passed',
            }])
        })
        updated_sample = LibraryPreparation.objects.get(pk=obj.pk).sample
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(updated_sample.status, 3)

        # Ensure a Pooling objects is created
        # self.assertEqual(
        #     Pooling.objects.filter(sample=updated_sample).count(), 1)

    def test_quality_check_failed(self):
        """ Ensure quality check has failed behaves correctly. """
        self.client.login(email='test@test.io', password='foo-bar')

        obj = create_library_preparation_obj(
            self._get_random_name(), self.user, 2
        )

        response = self.client.post(reverse('library-preparation-edit'), {
            'data': json.dumps([{
                'pk': obj.pk,
                'quality_check': 'failed',
            }])
        })
        updated_obj = LibraryPreparation.objects.get(pk=obj.pk)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(updated_obj.sample.status, -1)

    def test_invalid_json(self):
        """ Ensure error is thrown if the JSON object is empty. """
        self.client.login(email='test@test.io', password='foo-bar')
        response = self.client.post(reverse('library-preparation-edit'), {})
        data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data['success'])
        self.assertIn('Invalid payload.', data['message'])
