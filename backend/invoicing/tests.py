import json

from common.tests import BaseAPITestCase, BaseTestCase
from common.utils import get_random_name
from django.urls import reverse
from flowcell.tests import create_sequencer
from library_sample_shared.tests import create_library_protocol, create_read_length
from rest_framework import status

from .models import (
    FixedCosts,
    LibraryPreparationCosts,
    SequencingCosts,
)


def create_fixed_cost(sequencer, price):
    fixed_cost = FixedCosts(sequencer=sequencer, price=price)
    fixed_cost.save()
    return fixed_cost


def create_preparation_cost(library_protocol, price):
    preparation_cost = LibraryPreparationCosts(
        library_protocol=library_protocol,
        price=price,
    )
    preparation_cost.save()
    return preparation_cost


def create_sequencing_cost(sequencer, read_length, price):
    sequencing_cost = SequencingCosts(
        sequencer=sequencer,
        read_length=read_length,
        price=price,
    )
    sequencing_cost.save()
    return sequencing_cost


# Models


class TestFixedCostsModel(BaseTestCase):
    def setUp(self):
        self.sequencer = create_sequencer(get_random_name())
        self.cost = create_fixed_cost(self.sequencer, 10)

    def test_name(self):
        self.assertEqual(str(self.cost), self.sequencer.name)
        self.assertEqual(self.cost.price_amount, f"{self.cost.price} €")


class TestLibraryPreparationCostsModel(BaseTestCase):
    def setUp(self):
        self.library_protocol = create_library_protocol(get_random_name())
        self.cost = create_preparation_cost(self.library_protocol, 10)

    def test_name(self):
        self.assertEqual(str(self.cost), self.library_protocol.name)
        self.assertEqual(self.cost.price_amount, f"{self.cost.price} €")


class TestSequencingCostsModel(BaseTestCase):
    def setUp(self):
        self.sequencer = create_sequencer(get_random_name())
        self.read_length = create_read_length(get_random_name())
        self.cost = create_sequencing_cost(self.sequencer, self.read_length, 10)

    def test_name(self):
        self.assertEqual(
            str(self.cost), f"{self.sequencer.name} {self.read_length.name}"
        )
        self.assertEqual(self.cost.price_amount, f"{self.cost.price} €")


# Views


class TestFixedCostsViewSet(BaseAPITestCase):
    def setUp(self):
        self.create_user()
        self.login()

        sequencer = create_sequencer(get_random_name())
        self.cost = create_fixed_cost(sequencer, 10)

    def test_costs_list(self):
        """Ensure get fixed costs list behaves correctly."""
        response = self.client.get(reverse("fixed-costs-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        costs = [x["name"] for x in response.data]
        self.assertIn(str(self.cost), costs)

    def test_update_price(self):
        """Ensure update price behaves correctly."""
        response = self.client.patch(
            path=reverse("fixed-costs-detail", kwargs={"pk": self.cost.pk}),
            data=json.dumps({"price": 15}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        updated_cost = FixedCosts.objects.get(pk=self.cost.pk)
        self.assertEqual(updated_cost.price, 15)

    def test_non_staff(self):
        self.create_user("non-staff@test.io", "test", False)
        self.login("non-staff@test.io", "test")
        response = self.client.get(reverse("fixed-costs-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestLibraryPreparationCostsViewSet(BaseAPITestCase):
    def setUp(self):
        self.create_user()
        self.login()

        library_protocol = create_library_protocol(get_random_name())
        self.cost = create_preparation_cost(library_protocol, 10)

    def test_costs_list(self):
        """Ensure get library preparation costs list behaves correctly."""
        response = self.client.get(reverse("library-preparation-costs-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        costs = [x["name"] for x in response.data]
        self.assertIn(str(self.cost), costs)

    def test_update_price(self):
        """Ensure update price behaves correctly."""
        response = self.client.put(
            path=reverse(
                "library-preparation-costs-detail", kwargs={"pk": self.cost.pk}
            ),
            data=json.dumps(
                {
                    "id": self.cost.pk,
                    "price": 15,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        updated_cost = LibraryPreparationCosts.objects.get(pk=self.cost.pk)
        self.assertEqual(updated_cost.price, 15)

    def test_non_staff(self):
        self.create_user("non-staff@test.io", "test", False)
        self.login("non-staff@test.io", "test")
        response = self.client.get(reverse("library-preparation-costs-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestSequencingCostsViewSet(BaseAPITestCase):
    def setUp(self):
        self.create_user()
        self.login()

        sequencer = create_sequencer(get_random_name())
        read_length = create_read_length(get_random_name())
        self.cost = create_sequencing_cost(sequencer, read_length, 10)

    def test_costs_list(self):
        """Ensure get sequencing costs list behaves correctly."""
        response = self.client.get(reverse("sequencing-costs-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        costs = [x["name"] for x in response.data]
        self.assertIn(str(self.cost), costs)

    def test_update_price(self):
        """Ensure update price behaves correctly."""
        response = self.client.patch(
            path=reverse("sequencing-costs-detail", kwargs={"pk": self.cost.pk}),
            data=json.dumps({"price": 15}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        updated_cost = SequencingCosts.objects.get(pk=self.cost.pk)
        self.assertEqual(updated_cost.price, 15)

    def test_non_staff(self):
        self.create_user("non-staff@test.io", "test", False)
        self.login("non-staff@test.io", "test")
        response = self.client.get(reverse("sequencing-costs-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestInvoicingViewSet(BaseAPITestCase):
    """Tests for the main Invoicing ViewSet."""

    def setUp(self):
        self.create_user()
        self.login()

    def test_list(self):
        response = self.client.get(reverse("invoicing-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
