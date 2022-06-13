import json
import tempfile

from django.contrib.auth import get_user_model
# from django.core.files.base import ContentFile
from django.test import TestCase

from common.models import Organization, PrincipalInvestigator
from common.tests import BaseTestCase
from common.utils import get_random_name

from .models import Request, FileRequest
from library.tests import create_library
from sample.tests import create_sample

User = get_user_model()


def create_request(user, save=True):
    request = Request(user=user, description=get_random_name())
    if save:
        request.save()
    return request


# Models

class TestRequestModel(TestCase):
    def setUp(self):
        self.org = Organization(name=get_random_name())
        self.org.save()

        self.pi = PrincipalInvestigator(
            name=get_random_name(),
            organization=self.org,
        )
        self.pi.save()

        self.user = User.objects.create_user(
            first_name='Foo',
            last_name='Bar',
            email='foo@bar.io',
            password='foo-foo',
            organization=self.org,
            pi=self.pi,
        )

    def test_create_request(self):
        request = create_request(self.user)
        self.assertEqual(str(request), request.name)
        self.assertEqual(request.name, '{}_{}_{}'.format(
            request.pk, self.user.last_name, self.user.pi.name,
        ))

    def test_delete_request(self):
        """
        Ensure all dependent libraries,
        samples and uploaded files are deleted, too.
        """
        request = Request(user=self.user)
        request.save()

        library = create_library(get_random_name())
        sample = create_sample(get_random_name())
        Library = library.__class__
        Sample = sample.__class__

        request.libraries.add(library)
        request.samples.add(sample)
        request.delete()

        # TODO: create and delete files

        self.assertEqual(Library.objects.filter(pk=library.pk).count(), 0)
        self.assertEqual(Sample.objects.filter(pk=sample.pk).count(), 0)

    def test_total_records_count(self):
        request = Request(user=self.user)
        request.save()

        library = create_library(get_random_name())
        sample = create_sample(get_random_name())

        request.libraries.add(library)
        request.samples.add(sample)

        request = Request.objects.get(pk=request.pk)
        self.assertEqual(request.total_records_count, 2)


class FileRequestTest(TestCase):
    def setUp(self):
        tmp_file = tempfile.NamedTemporaryFile()
        self.file = FileRequest(name='File', file=tmp_file)
        tmp_file.close()

    def test_file_name(self):
        self.assertTrue(isinstance(self.file, FileRequest))
        self.assertEqual(self.file.__str__(), self.file.name)


# Views

class TestRequests(BaseTestCase):
    def setUp(self):
        self.user = self.create_user()
        self.non_staff = self.create_user('non-staff@test.io', 'test', False)
        self.login()

    def test_request_list(self):
        """ Ensure get request list behaves correctly. """
        request1 = create_request(self.user)
        request2 = create_request(self.non_staff)
        response = self.client.get('/api/requests/')
        self.assertEqual(response.status_code, 200)
        requests = [x['name'] for x in response.json()['results']]
        self.assertIn(request1.name, requests)
        self.assertIn(request2.name, requests)

    def test_request_list_non_existing_page(self):
        request = create_request(self.user)
        response = self.client.get('/api/requests/', {'page': -1})
        self.assertEqual(response.status_code, 200)
        requests = [x['name'] for x in response.json()]
        self.assertIn(request.name, requests)

    def test_request_list_non_staff(self):
        """ Ensure a non-staff user gets only their requests. """
        self.login('non-staff@test.io', 'test')
        request1 = create_request(self.non_staff)
        request2 = create_request(self.user)

        response = self.client.get('/api/requests/')
        requests = [x['name'] for x in response.json()['results']]
        self.assertEqual(response.status_code, 200)
        self.assertIn(request1.name, requests)
        self.assertNotIn(request2.name, requests)

    def test_search(self):
        """ Ensure search behaves correctly. """
        request1 = create_request(self.user)
        request2 = create_request(self.user)
        request3 = create_request(self.user)
        name1 = get_random_name()
        name2 = get_random_name()
        request1.name = name1
        request2.description = name1
        request3.description = name2
        request1.save()
        request2.save()
        request3.save()

        response = self.client.get('/api/requests/', {'query': name1})
        self.assertEqual(response.status_code, 200)

        requests = [x['name'] for x in response.json()['results']]
        self.assertIn(request1.name, requests)
        self.assertIn(request2.name, requests)
        self.assertNotIn(request3.name, requests)

    def test_single_request(self):
        """ Ensure get single request behaves correctly. """
        request = create_request(self.user)
        response = self.client.get(f'/api/requests/{request.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(request.name, response.json()['name'])

    def test_single_request_invalid_id(self):
        """ Ensure error is thrown if the id does not exist. """
        response = self.client.get('/api/requests/-1/')
        self.assertEqual(response.status_code, 404)

    def test_create_request(self):
        """ Ensure create request behaves correctly. """
        library = create_library(get_random_name())
        sample = create_sample(get_random_name())
        Library = library.__class__
        response = self.client.post('/api/requests/', {
            'data': json.dumps({
                'description': get_random_name(),
                'records': [{
                    'pk': library.pk,
                    'record_type': 'Library',
                }, {
                    'pk': sample.pk,
                    'record_type': 'Sample',
                }],
                # 'files': [],
            })
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()['success'])
        self.assertEqual(
            Library.objects.get(pk=library.pk).request.filter().count(), 1)

    def test_create_request_no_records(self):
        """
        Ensure error is thrown if no records are provided when
        creating a new request.
        """
        response = self.client.post('/api/requests/', {
            'data': json.dumps({
                'description': get_random_name(),
                'records': [],
                # 'files': [],
            })
        })
        data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Invalid payload.')

    def test_update_request(self):
        """ Ensure update request behaves correctly. """
        request = create_request(self.user)
        new_description = get_random_name()
        library = create_library(get_random_name())
        sample = create_sample(get_random_name())
        request.libraries.add(library)
        self.assertNotIn(sample, request.samples.all())

        response = self.client.post(f'/api/requests/{request.pk}/edit/', {
            'data': json.dumps({
                'description': new_description,
                'records': [{
                    'pk': library.pk,
                    'record_type': 'Library',
                }, {
                    'pk': sample.pk,
                    'record_type': 'Sample',
                }],
                # 'files': [],
            }),
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        updated_request = Request.objects.get(pk=request.pk)
        self.assertEqual(updated_request.description, new_description)
        self.assertIn(sample, updated_request.samples.all())

    def test_update_request_no_records(self):
        """
        Ensure error is thrown if no records are provided when
        updating a request.
        """
        request = create_request(self.user)
        library = create_library(get_random_name())
        request.libraries.add(library)

        response = self.client.post(f'/api/requests/{request.pk}/edit/', {
            'data': json.dumps({
                'description': get_random_name(),
                'records': [],
                # 'files': [],
            }),
        })
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])

    def test_update_request_invalid_id(self):
        """ Ensure error is thrown if the id does not exist. """
        response = self.client.post('/api/requests/-1/edit/', {
            'data': json.dumps({})
        })
        self.assertEqual(response.status_code, 404)

    def test_samples_submitted(self):
        """ Ensure set samples_submitted behaves correctly. """
        request = create_request(self.user)
        response = self.client.post(
            f'/api/requests/{request.pk}/samples_submitted/', {
                'data': json.dumps({'result': True})
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        request = Request.objects.get(pk=request.pk)
        self.assertTrue(request.samples_submitted)

    def test_delete_request(self):
        """ Ensure delete request behaves correctly. """
        request = create_request(self.user)
        response = self.client.delete(f'/api/requests/{request.pk}/')
        self.assertEqual(response.status_code, 204)

    def test_delete_request_invalid_id(self):
        """ Ensure error is thrown if the id does not exist. """
        response = self.client.delete('/api/requests/-1/')
        self.assertEqual(response.status_code, 404)

    def test_get_records(self):
        """ Ensure get request's records behaves correctly. """
        request = create_request(self.user)
        library = create_library(get_random_name())
        sample = create_sample(get_random_name())
        request.libraries.add(library)
        request.samples.add(sample)

        response = self.client.get(f'/api/requests/{request.pk}/get_records/')
        self.assertEqual(response.status_code, 200)
        records = [x['name'] for x in response.json()]
        self.assertIn(library.name, records)
        self.assertIn(sample.name, records)

    def test_get_files(self):
        """ Ensure get request's files behaves correctly. """
        pass


# class GenerateDeepSeqRequestTest(TestCase):
#     def setUp(self):
#         user = User.objects.create_user(email='foo@bar.io', password='foo-foo')
#         user.save()

#         library = Library.get_test_library('Library')
#         sample = Sample.get_test_sample('Sample')
#         library.save()
#         sample.save()

#         self.request = Request(user=user)
#         self.request.save()

#         self.request.libraries.add(library)
#         self.request.samples.add(sample)

#     def test_generate(self):
#         self.client.login(email='foo@bar.io', password='foo-foo')
#         response = self.client.post(
#             reverse('generate_deep_sequencing_request'), {
#                 'request_id': self.request.pk,
#             },
#         )
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(
#             response.get('Content-Disposition'),
#             'attachment; filename="%s_Deep_Sequencing_Request.pdf"' %
#             self.request.name,
#         )

#     def test_missing_or_empty_request_id(self):
#         self.client.login(email='foo@bar.io', password='foo-foo')
#         response = self.client.post(reverse('generate_deep_sequencing_request'))
#         self.assertEqual(response.status_code, 200)
#         self.assertJSONEqual(
#             str(response.content, encoding='utf-8'),
#             {'success': False},
#         )


# class UploadDeepSeqRequestTest(TestCase):
#     def setUp(self):
#         user = User.objects.create_user(email='foo@bar.io', password='foo-foo')
#         user.save()

#         library = Library.get_test_library('Library')
#         sample = Sample.get_test_sample('Sample')
#         library.save()
#         sample.save()

#         self.request = Request(user=user)
#         self.request.save()

#         self.request.libraries.add(library)
#         self.request.samples.add(sample)

#     def test_upload(self):
#         self.client.login(email='foo@bar.io', password='foo-foo')
#         tmp_file = tempfile.NamedTemporaryFile()
#         with open(tmp_file.name, 'rb') as fp:
#             response = self.client.post(
#                 reverse('upload_deep_sequencing_request'),
#                 {'request_id': self.request.pk, 'file': fp},
#                 format='multipart'
#             )
#         tmp_file.close()
#         self.assertEqual(response.status_code, 200)

#     def test_missing_file(self):
#         self.client.login(email='foo@bar.io', password='foo-foo')
#         response = self.client.post(reverse('upload_deep_sequencing_request'), {
#             'request_id': self.request.pk
#         }, format='multipart')
#         self.assertEqual(response.status_code, 200)

#     def test_exception(self):
#         """ Empty or non-existing request_id. """
#         self.client.login(email='foo@bar.io', password='foo-foo')

#         tmp_file = tempfile.NamedTemporaryFile()
#         with open(tmp_file.name, 'rb') as fp:
#             response = self.client.post(
#                 reverse('upload_deep_sequencing_request'),
#                 {'request_id': '', 'file': fp},
#                 format='multipart'
#             )
#         tmp_file.close()
#         self.assertEqual(response.status_code, 200)


# class GeneratePDFTest(TestCase):
#     def setUp(self):
#         user = User.objects.create_user(email='foo@bar.io', password='foo-foo')
#         user.save()

#         self.request = Request(user=user)
#         self.request.save()

#     def test_generate_deep_sequencing_request(self):
#         self.client.login(email='foo@bar.io', password='foo-foo')
#         response = self.client.get(
#             reverse('generate_deep_sequencing_request'), {
#                 'request_id': self.request.pk
#             }
#         )
#         self.assertEqual(response.status_code, 200)
