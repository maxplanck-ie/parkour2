import json

from common.tests import BaseTestCase
from common.utils import get_random_name
from django.urls import reverse
from index_generator.tests import create_pool
from request.models import Request
from sample.tests import create_sample

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
        self.assertEqual(
            str(self.library_prep_obj),
            "{} ({})".format(
                self.library_prep_obj.sample.name,
                self.library_prep_obj.sample.barcode,
            ),
        )

    def test_create_library_preparation_object(self):
        """
        Ensure a Library Preparation object is created when a sample
        is added to a pool.
        """
        sample = create_sample(get_random_name(), 2)
        pool = create_pool(self.user)
        pool.samples.add(sample)
        self.assertEqual(LibraryPreparation.objects.filter(sample=sample).count(), 1)


# Signals (characterization tests for library_preparation/signals.py)


class TestLibraryPreparationSignals(BaseTestCase):
    """
    Pins down current behavior of library_preparation/signals.py before
    any cross-domain signal cleanup (issue #346). These describe what the
    signal does today, not what it should do.
    """

    def setUp(self):
        self.user = self.create_user()

    def test_adding_sample_sets_is_pooled_and_is_converted_for_every_sample_in_pool(
        self,
    ):
        sample1 = create_sample(get_random_name(), status=2)
        sample2 = create_sample(get_random_name(), status=2)
        pool = create_pool(self.user)

        pool.samples.add(sample1)
        pool.samples.add(sample2)

        sample1.refresh_from_db()
        sample2.refresh_from_db()
        self.assertTrue(sample1.is_pooled)
        self.assertTrue(sample1.is_converted)
        self.assertTrue(sample2.is_pooled)
        self.assertTrue(sample2.is_converted)

    def test_adding_sample_rewrites_barcode_prefix_from_s_to_l(self):
        sample = create_sample(get_random_name(), status=2)
        original_barcode = sample.barcode
        pool = create_pool(self.user)

        pool.samples.add(sample)

        sample.refresh_from_db()
        self.assertEqual(sample.barcode, original_barcode.replace("S", "L"))

    def test_adding_sample_is_idempotent_for_library_preparation_object(self):
        """Re-adding the same sample to the pool doesn't duplicate LibraryPreparation."""
        sample = create_sample(get_random_name(), status=2)
        pool = create_pool(self.user)

        pool.samples.add(sample)
        pool.samples.remove(sample)
        pool.samples.add(sample)

        self.assertEqual(LibraryPreparation.objects.filter(sample=sample).count(), 1)


# Views


class TestLibraryPreparation(BaseTestCase):
    def setUp(self):
        self.user = self.create_user()

    def test_library_preparation_list(self):
        """Ensure get library preparation list behaves correctly."""
        self.login()

        library_prep_obj1 = create_library_preparation_obj(
            self._get_random_name(), self.user, 2
        )
        library_prep_obj2 = create_library_preparation_obj(
            self._get_random_name(), self.user, -1
        )

        response = self.client.get(reverse("library-preparation-list"))
        data = response.json()
        objects = [x["name"] for x in data]
        self.assertEqual(response.status_code, 200)
        self.assertIn(library_prep_obj1.sample.name, objects)
        self.assertNotIn(library_prep_obj2.sample.name, objects)

    def test_library_preparation_list_non_staff(self):
        """Ensure error is thrown if a non-staff user tries to get the list."""
        self.create_user("non-staff@test.io", "test", False)
        self.client.login(email="non-staff@test.io", password="test")
        response = self.client.get(reverse("library-preparation-list"))
        self.assertTrue(response.status_code, 403)

    def test_update_library_preparation_object(self):
        """Ensure update library preparation object behaves correctly."""
        self.client.login(email="test@test.io", password="foo-bar")

        obj = create_library_preparation_obj(self._get_random_name(), self.user, 2)

        response = self.client.post(
            reverse("library-preparation-edit"),
            {
                "data": json.dumps(
                    [
                        {
                            "pk": obj.pk,
                            "starting_amount": 1.0,
                        }
                    ]
                )
            },
        )
        updated_obj = LibraryPreparation.objects.get(pk=obj.pk)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(updated_obj.starting_amount, 1.0)

    def test_update_converted_sample(self):
        """Ensure update converted sample's field behaves correctly."""
        self.client.login(email="test@test.io", password="foo-bar")

        obj = create_library_preparation_obj(self._get_random_name(), self.user, 2)

        response = self.client.post(
            reverse("library-preparation-edit"),
            {
                "data": json.dumps(
                    [
                        {
                            "pk": obj.pk,
                            "concentration_sample": 2.0,
                            "comments_facility": "blah",
                        }
                    ]
                )
            },
        )
        updated_sample = LibraryPreparation.objects.get(pk=obj.pk).sample
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(updated_sample.measured_value_facility, 2.0)
        self.assertEqual(updated_sample.comments_facility, "blah")

    def test_contains_invalid_objects(self):
        """
        Ensure update library preparation objects containing invalid objects
        behaves correctly.
        """
        self.client.login(email="test@test.io", password="foo-bar")

        obj1 = create_library_preparation_obj(self._get_random_name(), self.user, 2)

        obj2 = create_library_preparation_obj(self._get_random_name(), self.user, 2)

        response = self.client.post(
            reverse("library-preparation-edit"),
            {
                "data": json.dumps(
                    [
                        {
                            "pk": obj1.pk,
                            "starting_amount": 1.0,
                        },
                        {
                            "pk": obj2.pk,
                            "pcr_cycles": "blah",
                        },
                    ]
                )
            },
        )
        data = response.json()
        updated_obj = LibraryPreparation.objects.get(pk=obj1.pk)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "Some records cannot be updated.")
        self.assertEqual(updated_obj.starting_amount, 1.0)

    def test_update_invalid_library_preparation_object(self):
        """
        Ensure update invalid library preparation objects behaves correctly.
        """
        self.client.login(email="test@test.io", password="foo-bar")

        obj = create_library_preparation_obj(self._get_random_name(), self.user, 2)

        response = self.client.post(
            reverse("library-preparation-edit"),
            {
                "data": json.dumps(
                    [
                        {
                            "pk": obj.pk,
                            "starting_amount": "blah",
                        }
                    ]
                )
            },
        )
        data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "Invalid payload.")

    def test_contains_invalid_id(self):
        """
        Ensure update library preparation object containing records with
        invalid ids bahaves correctly.
        """
        self.client.login(email="test@test.io", password="foo-bar")

        obj = create_library_preparation_obj(self._get_random_name(), self.user, 2)

        response = self.client.post(
            reverse("library-preparation-edit"),
            {
                "data": json.dumps(
                    [
                        {
                            "pk": obj.pk,
                            "starting_amount": 1.0,
                        },
                        {
                            "pk": "blah",
                            "pcr_cycles": 2,
                        },
                    ]
                )
            },
        )
        data = response.json()
        updated_obj = LibraryPreparation.objects.get(pk=obj.pk)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        self.assertEqual(updated_obj.starting_amount, 1.0)

    def test_quality_check_passed(self):
        """Ensure quality check has passed behaves correctly."""
        self.client.login(email="test@test.io", password="foo-bar")

        obj = create_library_preparation_obj(self._get_random_name(), self.user, 2)

        response = self.client.post(
            reverse("library-preparation-edit"),
            {
                "data": json.dumps(
                    [
                        {
                            "pk": obj.pk,
                            "quality_check": "passed",
                        }
                    ]
                )
            },
        )
        updated_sample = LibraryPreparation.objects.get(pk=obj.pk).sample
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(updated_sample.status, 3)

        # Ensure a Pooling objects is created
        # self.assertEqual(
        #     Pooling.objects.filter(sample=updated_sample).count(), 1)

    def test_quality_check_failed(self):
        """Ensure quality check has failed behaves correctly."""
        self.client.login(email="test@test.io", password="foo-bar")

        obj = create_library_preparation_obj(self._get_random_name(), self.user, 2)

        response = self.client.post(
            reverse("library-preparation-edit"),
            {
                "data": json.dumps(
                    [
                        {
                            "pk": obj.pk,
                            "quality_check": "failed",
                            "starting_amount": 8.0,
                            "pcr_cycles": 10,
                            "concentration_library": 3.25,
                            "mean_fragment_size": 280,
                        }
                    ]
                )
            },
        )
        updated_obj = LibraryPreparation.objects.get(pk=obj.pk)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(updated_obj.sample.status, -1)
        self.assertEqual(updated_obj.starting_amount, 8.0)
        self.assertEqual(updated_obj.pcr_cycles, 10)
        self.assertEqual(updated_obj.concentration_library, 3.25)
        self.assertEqual(updated_obj.mean_fragment_size, 280)

    def test_invalid_json(self):
        """Ensure error is thrown if the JSON object is empty."""
        self.client.login(email="test@test.io", password="foo-bar")
        response = self.client.post(reverse("library-preparation-edit"), {})
        data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data["success"])
        self.assertIn("Invalid payload.", data["message"])

    def test_quality_check_passed_appears_in_pooling(self):
        """
        Ensure a sample that passes quality check in Library Preparation
        (status=3) is properly tracked when transitioning through the workflow.
        """
        self.client.login(email="test@test.io", password="foo-bar")

        # Create a sample with status=2 and a pool
        obj = create_library_preparation_obj(self._get_random_name(), self.user, 2)

        # Verify sample already appears in pooling with status=2
        response = self.client.get(reverse("pooling-list"))
        data = response.json()
        sample_names_before = [
            x["name"] for x in data if x.get("record_type") == "Sample"
        ]
        self.assertIn(obj.sample.name, sample_names_before)
        initial_sample_count = len(sample_names_before)

        # Update quality check to passed (should transition from status=2 to status=3)
        response = self.client.post(
            reverse("library-preparation-edit"),
            {
                "data": json.dumps(
                    [
                        {
                            "pk": obj.pk,
                            "quality_check": "passed",
                        }
                    ]
                )
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        # Verify sample status is now 3
        updated_sample = LibraryPreparation.objects.get(pk=obj.pk).sample
        self.assertEqual(updated_sample.status, 3)

        # Verify sample still appears in pooling list with new status
        response = self.client.get(reverse("pooling-list"))
        data = response.json()
        sample_names_after = [
            x["name"] for x in data if x.get("record_type") == "Sample"
        ]
        self.assertIn(updated_sample.name, sample_names_after)
