import json

from common.tests import BaseTestCase
from common.utils import get_random_name
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from library_sample_shared.models import (
    BarcodeCounter,
    ConcentrationMethod,
    LibraryProtocol,
    LibraryType,
    Organism,
    ReadLength,
)
from request.models import Request

from .models import NucleicAcidType, Sample

User = get_user_model()


def create_sample(name, status=0, save=True, read_length=None, index_type=None):
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

    nat = NucleicAcidType(name="Nucleic Acid Type")
    nat.save()

    sample = Sample(
        name=name,
        status=status,
        organism_id=organism.pk,
        concentration=1.0,
        read_length_id=read_length.pk,
        sequencing_depth=1,
        library_protocol_id=library_protocol.pk,
        library_type_id=library_type.pk,
        nucleic_acid_type_id=nat.pk,
    )

    if index_type:
        sample.index_type = index_type

    if save:
        sample.save()

    return sample


# Models


class TestSampleModel(TestCase):
    def setUp(self):
        self.sample = create_sample(get_random_name(), save=False)

    def test_barcode_generation(self):
        """
        Ensure the barcode counter is incremented and is assigned to a
        new sample.
        """
        prev_counter = BarcodeCounter.load().last_id
        self.assertEqual(self.sample.barcode, "")
        self.sample.save()

        new_counter = BarcodeCounter.load().last_id
        self.assertEqual(new_counter, prev_counter + 1)

        barcode = timezone.now().strftime("%y") + "S"
        barcode += "0" * (6 - len(str(new_counter))) + str(new_counter)

        updated_sample = Sample.objects.get(pk=self.sample.pk)
        self.assertEqual(updated_sample.barcode, barcode)


class NucleicAcidTypeTest(TestCase):
    def setUp(self):
        self.nucleic_acid_type = NucleicAcidType(name="NAT")

    def test_nucleic_acid_type_name(self):
        self.assertTrue(isinstance(self.nucleic_acid_type, NucleicAcidType))
        self.assertEqual(
            self.nucleic_acid_type.__str__(),
            self.nucleic_acid_type.name,
        )


# Views


class TestNucleicAcidTypes(BaseTestCase):
    def setUp(self):
        self.create_user("foo@bar.io", "foo-foo")
        self.client.login(email="foo@bar.io", password="foo-foo")
        self.na_type = NucleicAcidType(name=self._get_random_name())
        self.na_type.save()

    def test_nucleic_acid_type_list(self):
        """Ensure get nucleic acid types behaves correctly."""
        response = self.client.get(reverse("nucleic-acid-type-list"))
        data = response.json()
        na_types = [x["name"] for x in data]
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.na_type.name, na_types)


class TestSamples(BaseTestCase):
    """Tests for samples."""

    def setUp(self):
        self.user = self.create_user("foo@bar.io", "foo-foo")
        self.client.login(email="foo@bar.io", password="foo-foo")

        self.sample = create_sample(self._get_random_name())
        self.request = Request(user=self.user)
        self.request.save()
        self.request.samples.add(self.sample)

    def test_single_sample(self):
        """Ensure get single sample behaves correctly."""
        response = self.client.get(
            reverse(
                "samples-detail",
                kwargs={"pk": self.sample.pk},
            )
        )
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.sample.name, data["name"])

    def test_single_sample_invalid_id(self):
        """Ensure error is thrown if the id does not exist."""
        response = self.client.get(
            reverse(
                "samples-detail",
                kwargs={"pk": -1},
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_multiple_samples(self):
        """Ensure get multiple samples behaves correctly."""
        sample1 = create_sample(get_random_name())
        sample2 = create_sample(get_random_name())
        sample3 = create_sample(get_random_name())

        request = Request(user=self.user)
        request.save()
        request.samples.add(*[sample1.pk, sample2.pk, sample3.pk])

        response = self.client.get(
            reverse("samples-list"),
            {"request_id": request.pk, "ids": json.dumps([sample1.pk, sample2.pk])},
        )
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        samples = [x["name"] for x in data["data"]]
        self.assertIn(sample1.name, samples)
        self.assertIn(sample2.name, samples)
        self.assertNotIn(sample3.name, samples)

    def test_multiple_sample_contains_invalid(self):
        """
        Ensure get multiple samples containing invalid ids behaves correctly.
        """
        sample = create_sample(get_random_name())

        request = Request(user=self.user)
        request.save()
        request.samples.add(sample)

        response = self.client.get(
            reverse("samples-list"),
            {"request_id": request.pk, "ids": json.dumps([sample.pk, "blah"])},
        )
        data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "Invalid payload.")

    def test_add_sample(self):
        """Ensure add sample behaves correctly."""
        name = self._get_random_name()
        response = self.client.post(
            reverse("samples-list"),
            {
                "data": json.dumps(
                    [
                        {
                            "name": name,
                            "organism": self.sample.organism.pk,
                            "concentration": 1.0,
                            "read_length": self.sample.read_length.pk,
                            "sequencing_depth": 1,
                            "library_protocol": self.sample.library_protocol.pk,
                            "library_type": self.sample.library_type.pk,
                            "nucleic_acid_type": self.sample.nucleic_acid_type.pk,
                        }
                    ]
                )
            },
        )
        data = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertTrue(data["success"])
        self.assertEqual(name, data["data"][0]["name"])
        self.assertEqual("Sample", data["data"][0]["record_type"])

    def test_add_sample_contains_invalid(self):
        """Ensure add sample containing invalid data behaves correctly."""
        name = self._get_random_name()
        response = self.client.post(
            reverse("samples-list"),
            {
                "data": json.dumps(
                    [
                        {
                            "name": name,
                            "organism": self.sample.organism.pk,
                            "concentration": 1.0,
                            "read_length": self.sample.read_length.pk,
                            "sequencing_depth": 1,
                            "library_protocol": self.sample.library_protocol.pk,
                            "library_type": self.sample.library_type.pk,
                            "nucleic_acid_type": self.sample.nucleic_acid_type.pk,
                        },
                        {
                            "name": self._get_random_name(),
                            "concentration": 1.0,
                            "sequencing_depth": 1,
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

    def test_add_sample_invalid_json(self):
        """Ensure error is thrown if the JSON object is empty."""
        response = self.client.post(reverse("samples-list"), {})
        data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data["success"])
        self.assertIn("Invalid payload.", data["message"])

    def test_add_sample_invalid_data(self):
        """Ensure error is thrown if the JSON object contains invalid data."""
        response = self.client.post(
            reverse("samples-list"),
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

    def test_update_sample(self):
        """Ensure update sample behaves correctly."""
        sample = create_sample(self._get_random_name())
        new_name = self._get_random_name()

        response = self.client.post(
            reverse("samples-edit"),
            {
                "data": json.dumps(
                    [
                        {
                            "pk": sample.pk,
                            "name": new_name,
                            "organism": sample.organism.pk,
                            "concentration": 1.0,
                            "read_length": sample.read_length.pk,
                            "sequencing_depth": 1,
                            "library_protocol": sample.library_protocol.pk,
                            "library_type": sample.library_type.pk,
                            "nucleic_acid_type": sample.nucleic_acid_type.pk,
                        }
                    ]
                )
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(Sample.objects.get(pk=sample.pk).name, new_name)

    def test_update_sample_contains_invalid(self):
        """Ensure update sample containing invalid data behaves correctly."""
        sample1 = create_sample(self._get_random_name())
        sample2 = create_sample(self._get_random_name())
        new_name1 = self._get_random_name()
        new_name2 = self._get_random_name()

        response = self.client.post(
            reverse("samples-edit"),
            {
                "data": json.dumps(
                    [
                        {
                            "pk": sample1.pk,
                            "name": new_name1,
                            "organism": sample1.organism.pk,
                            "concentration": 1.0,
                            "read_length": sample1.read_length.pk,
                            "sequencing_depth": 1,
                            "library_protocol": sample1.library_protocol.pk,
                            "library_type": sample1.library_type.pk,
                            "nucleic_acid_type": sample1.nucleic_acid_type.pk,
                        },
                        {
                            "pk": sample2.pk,
                            "name": new_name2,
                            "sample_id": sample2.pk,
                            "concentration": 1.0,
                            "sequencing_depth": 1,
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
        self.assertEqual(Sample.objects.get(pk=sample1.pk).name, new_name1)
        self.assertEqual(Sample.objects.get(pk=sample2.pk).name, sample2.name)

    def test_delete_sample(self):
        """Ensure delete sample behaves correctly."""
        sample = create_sample(self._get_random_name())
        response = self.client.delete(
            reverse(
                "samples-detail",
                kwargs={"pk": sample.pk},
            )
        )
        self.assertEqual(response.status_code, 204)

    def test_delete_sample_incorrect_id(self):
        """Ensure error is thrown if the id does not exist."""
        response = self.client.delete(
            reverse(
                "samples-detail",
                kwargs={"pk": -1},
            )
        )
        self.assertEqual(response.status_code, 404)
