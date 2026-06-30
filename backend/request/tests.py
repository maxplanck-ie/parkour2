import json
import tempfile
from datetime import timedelta
from unittest.mock import patch

from common.models import Organization, PrincipalInvestigator
from common.tests import BaseTestCase
from common.utils import get_random_name
from django.contrib.auth import get_user_model

# from django.core.files.base import ContentFile
from django.test import TestCase
from django.utils import timezone
from library.tests import create_library
from sample.tests import create_sample

from .models import FileRequest, Request

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
            first_name="Foo",
            last_name="Bar",
            email="foo@bar.io",
            password="foo-foo",
            organization=self.org,
            pi=self.pi,
        )

    def test_create_request(self):
        request = create_request(self.user)
        self.assertEqual(str(request), request.name)
        self.assertEqual(
            request.name,
            "{}_{}_{}".format(
                request.pk,
                self.user.last_name,
                self.user.pi.name,
            ),
        )

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
        self.file = FileRequest(name="File", file=tmp_file)
        tmp_file.close()

    def test_file_name(self):
        self.assertTrue(isinstance(self.file, FileRequest))
        self.assertEqual(self.file.__str__(), self.file.name)


class RequestMilestoneSignalsTest(TestCase):
    def setUp(self):
        self.org = Organization(name=get_random_name())
        self.org.save()

        self.pi = PrincipalInvestigator(
            name=get_random_name(),
            organization=self.org,
        )
        self.pi.save()

        self.user = User.objects.create_user(
            first_name="Foo",
            last_name="Bar",
            email="foo@bar.io",
            password="foo-foo",
            organization=self.org,
            pi=self.pi,
        )

        self.request = Request(user=self.user)
        self.request.save()

        self.library = create_library(get_random_name())
        self.sample = create_sample(get_random_name())
        self.request.libraries.add(self.library)
        self.request.samples.add(self.sample)

    def test_qc_timestamp_set_once(self):
        first_event_time = timezone.now()

        with patch("request.signals.timezone.now", return_value=first_event_time):
            self.library.status = 2
            self.library.save()

        self.request.refresh_from_db()
        self.assertEqual(self.request.qc_completed_at, first_event_time)

        later_event_time = first_event_time + timedelta(hours=1)
        with patch("request.signals.timezone.now", return_value=later_event_time):
            self.sample.status = 2
            self.sample.save()

        self.request.refresh_from_db()
        self.assertEqual(
            self.request.qc_completed_at,
            first_event_time,
            "QC milestone should only be set by the first record reaching status 2",
        )

    def test_flowcell_timestamp_from_status_five(self):
        sequencing_time = timezone.now()

        with patch("request.signals.timezone.now", return_value=sequencing_time):
            self.sample.status = 5
            self.sample.save()

        self.request.refresh_from_db()
        self.assertEqual(self.request.flowcell_loaded_at, sequencing_time)


class RequestRelatedRequestsHistoryTest(TestCase):
    def setUp(self):
        self.org = Organization(name=get_random_name())
        self.org.save()

        self.pi = PrincipalInvestigator(
            name=get_random_name(),
            organization=self.org,
        )
        self.pi.save()

        self.user = User.objects.create_user(
            first_name="Foo",
            last_name="Bar",
            email="foo-history@bar.io",
            password="foo-foo",
            organization=self.org,
            pi=self.pi,
        )

        self.request_a = create_request(self.user)
        self.request_b = create_request(self.user)

    def test_related_requests_add_appears_in_history(self):
        self.request_a.related_requests.add(self.request_b)

        newest, previous = self.request_a.history.all()[:2]
        delta = newest.diff_against(previous)

        self.assertIn("related_requests", delta.changed_fields)

    def test_related_requests_remove_appears_in_history(self):
        self.request_a.related_requests.add(self.request_b)
        self.request_a.related_requests.remove(self.request_b)

        newest, previous = self.request_a.history.all()[:2]
        delta = newest.diff_against(previous)

        self.assertIn("related_requests", delta.changed_fields)

    def test_target_request_add_appears_in_history(self):
        self.request_a.related_requests.add(self.request_b)

        newest, previous = self.request_b.history.all()[:2]
        delta = newest.diff_against(previous)

        self.assertIn("related_requests", delta.changed_fields)

    def test_target_request_remove_appears_in_history(self):
        self.request_a.related_requests.add(self.request_b)
        self.request_a.related_requests.remove(self.request_b)

        newest, previous = self.request_b.history.all()[:2]
        delta = newest.diff_against(previous)

        self.assertIn("related_requests", delta.changed_fields)


# Views


class TestRequests(BaseTestCase):
    def setUp(self):
        self.user = self.create_user()
        self.non_staff = self.create_user("non-staff@test.io", "test", False)
        self.login()

    def test_request_list(self):
        """Ensure get request list behaves correctly."""
        request1 = create_request(self.user)
        request2 = create_request(self.non_staff)
        response = self.client.get("/api/requests/")
        self.assertEqual(response.status_code, 200)
        requests = [x["name"] for x in response.json()["results"]]
        self.assertIn(request1.name, requests)
        self.assertIn(request2.name, requests)

    def test_request_list_non_existing_page(self):
        request = create_request(self.user)
        response = self.client.get("/api/requests/", {"page": -1})
        self.assertEqual(response.status_code, 200)
        requests = [x["name"] for x in response.json()]
        self.assertIn(request.name, requests)

    def test_request_list_non_staff(self):
        """Ensure a non-staff user gets only their requests."""
        self.login("non-staff@test.io", "test")
        request1 = create_request(self.non_staff)
        request2 = create_request(self.user)

        response = self.client.get("/api/requests/")
        requests = [x["name"] for x in response.json()["results"]]
        self.assertEqual(response.status_code, 200)
        self.assertIn(request1.name, requests)
        self.assertNotIn(request2.name, requests)

    def test_search(self):
        """Ensure search behaves correctly."""
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

        response = self.client.get("/api/requests/", {"query": name1})
        self.assertEqual(response.status_code, 200)

        requests = [x["name"] for x in response.json()["results"]]
        self.assertIn(request1.name, requests)
        self.assertIn(request2.name, requests)
        self.assertNotIn(request3.name, requests)

    def test_single_request(self):
        """Ensure get single request behaves correctly."""
        request = create_request(self.user)
        response = self.client.get(f"/api/requests/{request.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(request.name, response.json()["name"])

    def test_single_request_invalid_id(self):
        """Ensure error is thrown if the id does not exist."""
        response = self.client.get("/api/requests/-1/")
        self.assertEqual(response.status_code, 404)

    def test_create_request(self):
        """Ensure create request behaves correctly."""
        library = create_library(get_random_name())
        sample = create_sample(get_random_name())
        Library = library.__class__
        response = self.client.post(
            "/api/requests/",
            {
                "data": json.dumps(
                    {
                        "description": get_random_name(),
                        "records": [
                            {
                                "pk": library.pk,
                                "record_type": "Library",
                            },
                            {
                                "pk": sample.pk,
                                "record_type": "Sample",
                            },
                        ],
                        # 'files': [],
                    }
                )
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()["success"])
        self.assertEqual(Library.objects.get(pk=library.pk).request.filter().count(), 1)

    def test_create_request_no_records(self):
        """
        Ensure error is thrown if no records are provided when
        creating a new request.
        """
        response = self.client.post(
            "/api/requests/",
            {
                "data": json.dumps(
                    {
                        "description": get_random_name(),
                        "records": [],
                        # 'files': [],
                    }
                )
            },
        )
        data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "Invalid payload.")

    def test_update_request(self):
        """Ensure update request behaves correctly."""
        request = create_request(self.user)
        new_description = get_random_name()
        library = create_library(get_random_name())
        sample = create_sample(get_random_name())
        request.libraries.add(library)
        self.assertNotIn(sample, request.samples.all())

        response = self.client.post(
            f"/api/requests/{request.pk}/edit/",
            {
                "data": json.dumps(
                    {
                        "description": new_description,
                        "records": [
                            {
                                "pk": library.pk,
                                "record_type": "Library",
                            },
                            {
                                "pk": sample.pk,
                                "record_type": "Sample",
                            },
                        ],
                        # 'files': [],
                    }
                ),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        updated_request = Request.objects.get(pk=request.pk)
        self.assertEqual(updated_request.description, new_description)
        self.assertIn(sample, updated_request.samples.all())

    def test_update_request_reassign_user_as_staff(self):
        """Ensure staff can reassign request ownership and PI."""
        org = Organization(name=get_random_name())
        org.save()
        pi_original = PrincipalInvestigator(name="Deepseq", organization=org)
        pi_original.save()
        user_original = User.objects.create_user(
            email="sarah@test.io",
            password="foo-foo",
            first_name="Sarah",
            last_name="Deepseq",
            organization=org,
            pi=pi_original,
            is_staff=False,
        )
        user_original.save()

        pi_new = PrincipalInvestigator(name="Cisse", organization=org)
        pi_new.save()
        user_new = User.objects.create_user(
            email="ahmed@test.io",
            password="foo-foo",
            first_name="Ahmed",
            last_name="Cisse",
            organization=org,
            pi=pi_new,
            is_staff=False,
        )
        user_new.save()

        request = Request(user=user_original)
        request.save()
        library = create_library(get_random_name())
        sample = create_sample(get_random_name())
        request.libraries.add(library)
        request.samples.add(sample)

        response = self.client.post(
            f"/api/requests/{request.pk}/edit/",
            {
                "data": json.dumps(
                    {
                        "description": get_random_name(),
                        "records": [
                            {
                                "pk": library.pk,
                                "record_type": "Library",
                            },
                            {
                                "pk": sample.pk,
                                "record_type": "Sample",
                            },
                        ],
                        "user": user_new.pk,
                    }
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        updated_request = Request.objects.get(pk=request.pk)
        self.assertEqual(updated_request.user.pk, user_new.pk)
        self.assertEqual(
            updated_request.name,
            f"{request.pk}_{user_new.last_name}_{user_new.pi.name}",
        )

    def test_search_users_staff(self):
        """Ensure staff can search users for reassignment."""
        org = Organization(name=get_random_name())
        org.save()
        pi = PrincipalInvestigator(name="Cisse", organization=org)
        pi.save()
        User.objects.create_user(
            email="ahmed@test.io",
            password="foo-foo",
            first_name="Ahmed",
            last_name="Cisse",
            organization=org,
            pi=pi,
            is_staff=False,
        )

        response = self.client.get("/api/requests/search_users/", {"query": "Ahmed"})
        self.assertEqual(response.status_code, 200)
        results = response.json()
        self.assertTrue(any(user["email"] == "ahmed@test.io" for user in results))

    def test_search_users_non_staff(self):
        """Ensure non-staff users cannot access the user search endpoint."""
        self.login("non-staff@test.io", "test")
        response = self.client.get("/api/requests/search_users/", {"query": "Ahmed"})
        self.assertEqual(response.status_code, 403)

    def test_update_request_no_records(self):
        """
        Ensure error is thrown if no records are provided when
        updating a request.
        """
        request = create_request(self.user)
        library = create_library(get_random_name())
        request.libraries.add(library)

        response = self.client.post(
            f"/api/requests/{request.pk}/edit/",
            {
                "data": json.dumps(
                    {
                        "description": get_random_name(),
                        "records": [],
                        # 'files': [],
                    }
                ),
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])

    def test_update_request_invalid_id(self):
        """Ensure error is thrown if the id does not exist."""
        response = self.client.post("/api/requests/-1/edit/", {"data": json.dumps({})})
        self.assertEqual(response.status_code, 404)

    def test_samples_submitted(self):
        """Ensure set samples_submitted behaves correctly."""
        request = create_request(self.user)
        response = self.client.post(
            f"/api/requests/{request.pk}/samples_submitted/",
            {"data": json.dumps({"result": True})},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        request = Request.objects.get(pk=request.pk)
        self.assertTrue(request.samples_submitted)

    def test_delete_request(self):
        """Ensure delete request behaves correctly."""
        request = create_request(self.user)
        response = self.client.delete(f"/api/requests/{request.pk}/")
        self.assertEqual(response.status_code, 204)

    def test_delete_request_invalid_id(self):
        """Ensure error is thrown if the id does not exist."""
        response = self.client.delete("/api/requests/-1/")
        self.assertEqual(response.status_code, 404)

    def test_get_records(self):
        """Ensure get request's records behaves correctly."""
        request = create_request(self.user)
        library = create_library(get_random_name())
        sample = create_sample(get_random_name())
        request.libraries.add(library)
        request.samples.add(sample)

        response = self.client.get(f"/api/requests/{request.pk}/get_records/")
        self.assertEqual(response.status_code, 200)
        records = [x["name"] for x in response.json()]
        self.assertIn(library.name, records)
        self.assertIn(sample.name, records)

    def test_get_files(self):
        """Ensure get request's files behaves correctly."""
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
