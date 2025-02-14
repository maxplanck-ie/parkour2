import json

from common.tests import BaseTestCase
from common.utils import get_random_name, timezone
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from library.models import Library
from library_sample_shared.models import (
    BarcodeCounter,
    ConcentrationMethod,
    IndexType,
    LibraryProtocol,
    LibraryType,
    Organism,
    ReadLength,
)
from request.models import Request
from sample.tests import create_sample

User = get_user_model()


def create_library(name, status=0, save=True, read_length=None, index_type=None):
    organism = Organism(name="Organism")
    organism.save()

    if read_length is None:
        read_length = ReadLength(name="Read Length")
        read_length.save()

    library_protocol = LibraryProtocol(
        name="Protocol",
        type="DNA",
        provider="-",
        catalog="-",
        explanation="-",
        input_requirements="-",
        typical_application="-",
    )
    library_protocol.save()

    library_type = LibraryType(name="Library Type")
    library_type.save()
    library_type.library_protocol.add(library_protocol)

    if index_type is None:
        index_type = IndexType(name="Index Type")
        index_type.save()

    library = Library(
        name=name,
        status=status,
        organism_id=organism.pk,
        concentration=1.0,
        read_length_id=read_length.pk,
        sequencing_depth=1,
        library_protocol_id=library_protocol.pk,
        library_type_id=library_type.pk,
        index_type_id=index_type.pk,
        index_reads=0,
        mean_fragment_size=1,
    )

    if save:
        library.save()

    return library


# Models


class TestLibraryModel(TestCase):
    def setUp(self):
        self.library = create_library(get_random_name(), save=False)

    def test_barcode_generation(self):
        """
        Ensure the barcode counter is incremented and is assigned to a
        new library.
        """
        prev_counter = BarcodeCounter.load().last_id
        self.assertEqual(self.library.barcode, "")
        self.library.save()

        new_counter = BarcodeCounter.load().last_id
        self.assertEqual(new_counter, prev_counter + 1)

        barcode = timezone.now().strftime("%y") + "L"
        barcode += "0" * (6 - len(str(new_counter))) + str(new_counter)

        updated_library = Library.objects.get(pk=self.library.pk)
        self.assertEqual(updated_library.barcode, barcode)


# Views


class TestLibrarySampleTree(BaseTestCase):
    """Tests for the libraries and samples tree."""

    def setUp(self):
        user = self.create_user("foo@bar.io", "foo-foo")
        self.client.login(email="foo@bar.io", password="foo-foo")

        library = create_library(self._get_random_name())
        sample = create_sample(self._get_random_name())

        self.request = Request(user=user)
        self.request.save()
        self.request.libraries.add(library)
        self.request.samples.add(sample)

    def test_libraries_and_samples_list(self):
        """Ensure get all libraries and samples works correctly."""
        response = self.client.get(reverse("libraries-and-samples-list"))
        data = response.json()["children"][0]
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.request.name, data["name"])


class TestLibraries(BaseTestCase):
    """Tests for libraries."""

    def setUp(self):
        self.user = self.create_user("foo@bar.io", "foo-foo")
        self.client.login(email="foo@bar.io", password="foo-foo")

        self.library = create_library(self._get_random_name())
        self.request = Request(user=self.user)
        self.request.save()
        self.request.libraries.add(self.library)

    def test_single_library(self):
        """Ensure get single library behaves correctly."""
        response = self.client.get(
            reverse(
                "libraries-detail",
                kwargs={"pk": self.library.pk},
            )
        )
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.library.name, data["name"])

    def test_single_library_invalid_id(self):
        """Ensure error is thrown if the id does not exist."""
        response = self.client.get(
            reverse(
                "libraries-detail",
                kwargs={"pk": -1},
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_multiple_libraries(self):
        """Ensure get multiple libraries behaves correctly."""
        library1 = create_library(get_random_name())
        library2 = create_library(get_random_name())
        library3 = create_library(get_random_name())

        request = Request(user=self.user)
        request.save()
        request.libraries.add(*[library1.pk, library2.pk, library3.pk])

        response = self.client.get(
            reverse("libraries-list"),
            {"request_id": request.pk, "ids": json.dumps([library1.pk, library2.pk])},
        )
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        libraries = [x["name"] for x in data["data"]]
        self.assertIn(library1.name, libraries)
        self.assertIn(library2.name, libraries)
        self.assertNotIn(library3.name, libraries)

    def test_multiple_libraries_contains_invalid(self):
        """
        Ensure get multiple libraries containing invalid ids behaves correctly.
        """
        library = create_library(get_random_name())

        request = Request(user=self.user)
        request.save()
        request.libraries.add(library)

        response = self.client.get(
            reverse("libraries-list"),
            {"request_id": request.pk, "ids": json.dumps([library.pk, "blah"])},
        )
        data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "Invalid payload.")

    def test_add_library(self):
        """Ensure add library behaves correctly."""
        library = create_library(self._get_random_name())
        name = self._get_random_name()

        response = self.client.post(
            reverse("libraries-list"),
            {
                "data": json.dumps(
                    [
                        {
                            "name": name,
                            "organism": library.organism.pk,
                            "concentration": 1.0,
                            "read_length": library.read_length.pk,
                            "sequencing_depth": 1,
                            "library_protocol": library.library_protocol.pk,
                            "library_type": library.library_type.pk,
                            "index_type": library.index_type.pk,
                            "index_reads": 0,
                            "mean_fragment_size": 1,
                        }
                    ]
                )
            },
        )
        data = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertTrue(data["success"])
        self.assertEqual(name, data["data"][0]["name"])
        self.assertEqual("Library", data["data"][0]["record_type"])

    def test_add_library_contains_invalid(self):
        """Ensure add library containing invalid data behaves correctly."""
        name = self._get_random_name()
        response = self.client.post(
            reverse("libraries-list"),
            {
                "data": json.dumps(
                    [
                        {
                            "name": name,
                            "organism": self.library.organism.pk,
                            "concentration": 1.0,
                            "read_length": self.library.read_length.pk,
                            "sequencing_depth": 1,
                            "library_protocol": self.library.library_protocol.pk,
                            "library_type": self.library.library_type.pk,
                            "index_type": self.library.index_type.pk,
                            "index_reads": 0,
                            "mean_fragment_size": 1,
                        },
                        {
                            "name": self._get_random_name(),
                            "concentration": 1.0,
                            "sequencing_depth": 1,
                            "index_reads": 0,
                            "mean_fragment_size": 1,
                        },
                    ]
                )
            },
        )
        data = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertTrue(data["success"])
        self.assertIn("Invalid payload. Some records cannot be added.", data["message"])
        self.assertEqual(len(data["data"]), 1)
        self.assertEqual(name, data["data"][0]["name"])

    def test_add_library_invalid_json(self):
        """Ensure error is thrown if the JSON object is empty."""
        response = self.client.post(reverse("libraries-list"), {})
        data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data["success"])
        self.assertIn("Invalid payload.", data["message"])

    def test_add_library_invalid_data(self):
        """Ensure error is thrown if the JSON object contains invalid data."""
        response = self.client.post(
            reverse("libraries-list"),
            {
                "data": json.dumps(
                    [
                        {
                            "name": self._get_random_name(),
                        }
                    ]
                )
            },
        )
        data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data["success"])
        self.assertIn("Invalid payload.", data["message"])

    def test_update_library(self):
        """Ensure update library behaves correctly."""
        library = create_library(self._get_random_name())
        new_name = self._get_random_name()

        response = self.client.post(
            reverse("libraries-edit"),
            {
                "data": json.dumps(
                    [
                        {
                            "pk": library.pk,
                            "name": new_name,
                            "organism": library.organism.pk,
                            "concentration": 1.0,
                            "read_length": library.read_length.pk,
                            "sequencing_depth": 1,
                            "library_protocol": library.library_protocol.pk,
                            "library_type": library.library_type.pk,
                            "index_type": library.index_type.pk,
                            "index_reads": 0,
                            "mean_fragment_size": 1,
                        }
                    ]
                )
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(Library.objects.get(pk=library.pk).name, new_name)

    def test_update_library_contains_invalid(self):
        """Ensure update library containing invalid data behaves correctly."""
        library1 = create_library(self._get_random_name())
        library2 = create_library(self._get_random_name())
        new_name1 = self._get_random_name()
        new_name2 = self._get_random_name()

        response = self.client.post(
            reverse("libraries-edit"),
            {
                "data": json.dumps(
                    [
                        {
                            "pk": library1.pk,
                            "name": new_name1,
                            "organism": library1.organism.pk,
                            "concentration": 1.0,
                            "read_length": library1.read_length.pk,
                            "sequencing_depth": 1,
                            "library_protocol": library1.library_protocol.pk,
                            "library_type": library1.library_type.pk,
                            "index_type": library1.index_type.pk,
                            "index_reads": 0,
                            "mean_fragment_size": 1,
                        },
                        {
                            "pk": library2.pk,
                            "name": new_name2,
                            "concentration": 2.0,
                            "sequencing_depth": 2,
                            "index_reads": 0,
                            "mean_fragment_size": 2,
                        },
                    ]
                )
            },
        )
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        self.assertIn(
            "Invalid payload. Some records cannot be updated.", data["message"]
        )
        self.assertEqual(Library.objects.get(pk=library1.pk).name, new_name1)
        self.assertEqual(Library.objects.get(pk=library2.pk).name, library2.name)

    # def test_update_library_non_staff(self):
    #     """
    #     Ensure a non-staff user cannot update a library created by
    #     another user.
    #     """
    #     self.create_user('test_user@test.com', 'foo-foo', False)
    #     self.client.login(email='test_user@test.com', password='foo-foo')
    #     pass

    def test_delete_library(self):
        """Ensure delete library behaves correctly."""
        library = create_library(self._get_random_name())
        response = self.client.delete(
            reverse(
                "libraries-detail",
                kwargs={"pk": library.pk},
            )
        )
        self.assertEqual(response.status_code, 204)

    def test_delete_library_incorrect_id(self):
        """Ensure error is thrown if the id does not exist."""
        response = self.client.delete(
            reverse(
                "libraries-detail",
                kwargs={"pk": -1},
            )
        )
        self.assertEqual(response.status_code, 404)
