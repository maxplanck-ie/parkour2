import json

import pytz
from common.tests import BaseAPITestCase, BaseTestCase
from common.utils import get_random_name
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from flowcell.tests import create_flowcell, create_sequencer
from library_sample_shared.tests import create_library_protocol, create_read_length
from index_generator.tests import create_pool_size
from month import Month
from rest_framework import status
from django.utils.http import urlencode

from .models import (
    FixedCosts,
    InvoicingReport,
    LibraryPreparationCosts,
    SequencingCosts,
    FixedPrice,
    LibraryPreparationPrice,
    SequencingPrice
)

from common.models import Organization


def create_fixed_cost(sequencer, price, organization):
    fixed_cost = FixedCosts(sequencer=sequencer)
    fixed_cost.save()
    fixed_cost.fixedprice_set.create(
        price=price,
        organization=organization
    )
    return fixed_cost


def create_preparation_cost(library_protocol, price, organization):
    preparation_cost = LibraryPreparationCosts(
        library_protocol=library_protocol
    )
    preparation_cost.save()
    preparation_cost.librarypreparationprice_set.create(
        price=price,
        organization=organization
    )
    return preparation_cost


def create_sequencing_cost(pool_size, price, organization):
    sequencing_cost = SequencingCosts(
        pool_size=pool_size
    )
    sequencing_cost.save()
    sequencing_cost.sequencingprice_set.create(
        price=price,
        organization=organization,
    )
    return sequencing_cost


def create_organization(name):
    organization = Organization(name=name)
    organization.save()
    return organization


# Models


class TestInvoicingReport(BaseTestCase):
    def setUp(self):
        self.now = timezone.now()
        self.report = InvoicingReport(
            month=Month(self.now.year, self.now.month),
            report=SimpleUploadedFile("file.txt", b"content"),
        )

    def test_name(self):
        self.assertEqual(str(self.report), self.now.strftime("%B %Y"))


class TestFixedCostsModel(BaseTestCase):
    def setUp(self):
        self.sequencer = create_sequencer(get_random_name())
        organization = create_organization(get_random_name())
        self.cost = create_fixed_cost(self.sequencer, 10, organization)

    def test_name(self):
        self.assertEqual(str(self.cost), self.sequencer.name)
        self.assertEqual(self.cost.fixedprice_set.first().price_amount, f"{self.cost.fixedprice_set.first().price} €")


class TestLibraryPreparationCostsModel(BaseTestCase):
    def setUp(self):
        self.library_protocol = create_library_protocol(get_random_name())
        organization = create_organization(get_random_name())
        self.cost = create_preparation_cost(self.library_protocol, 10, organization)

    def test_name(self):
        self.assertEqual(str(self.cost), self.library_protocol.name)
        self.assertEqual(self.cost.librarypreparationprice_set.first().price_amount, f"{self.cost.librarypreparationprice_set.first().price} €")


class TestSequencingCostsModel(BaseTestCase):
    def setUp(self):
        self.pool_size = create_pool_size()
        organization = create_organization(get_random_name())
        self.cost = create_sequencing_cost(self.pool_size, 10, organization)

    def test_name(self):
        self.assertEqual(
            str(self.cost), f"{self.pool_size.sequencer.name} - {self.pool_size.lanes}×{self.pool_size.size}M, {self.pool_size.cycles}c"
        )
        self.assertEqual(self.cost.sequencingprice_set.first().price_amount, f"{self.sequencingprice_set.first().price} €")


# Views


class TestFixedCostsViewSet(BaseAPITestCase):
    def setUp(self):
        self.create_user()
        self.login()

        sequencer = create_sequencer(get_random_name())
        self.organization = create_organization(get_random_name())
        self.cost = create_fixed_cost(sequencer, 10, self.organization)

    def test_costs_list(self):
        """Ensure get fixed costs list behaves correctly."""
        query_kwargs = {"organization": self.organization.pk}
        response = self.client.get(f'{reverse("fixed-costs-list")}?{urlencode(query_kwargs)}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        costs = [x["name"] for x in response.data]
        self.assertIn(str(self.cost), costs)

    def test_update_price(self):
        """Ensure update price behaves correctly."""
        query_kwargs = {"organization": self.organization.pk}
        url = f'{reverse("fixed-costs-detail", kwargs={"pk": self.cost.pk})}?{urlencode(query_kwargs)}'
        response = self.client.put(
            path=url,
            data=json.dumps(
                {
                    "id": self.cost.pk,
                    "price": 15
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        updated_cost = FixedCosts.objects.get(pk=self.cost.pk)
        self.assertEqual(updated_cost.fixedprice_set.first().price, 15)

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
        self.organization = create_organization(get_random_name())
        self.cost = create_preparation_cost(library_protocol, 10, self.organization)

    def test_costs_list(self):
        """Ensure get library preparation costs list behaves correctly."""
        query_kwargs = {"organization": self.organization.pk}
        response = self.client.get(f'{reverse("library-preparation-costs-list")}?{urlencode(query_kwargs)}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        costs = [x["name"] for x in response.data]
        self.assertIn(str(self.cost), costs)

    def test_update_price(self):
        """Ensure update price behaves correctly."""
        query_kwargs = {"organization": self.organization.pk}
        url = f'{reverse("library-preparation-costs-detail", kwargs={"pk": self.cost.pk})}?{urlencode(query_kwargs)}'
        response = self.client.put(
            path=url,
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
        self.assertEqual(updated_cost.librarypreparationprice_set.first().price, 15)

    def test_non_staff(self):
        self.create_user("non-staff@test.io", "test", False)
        self.login("non-staff@test.io", "test")
        response = self.client.get(reverse("library-preparation-costs-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestSequencingCostsViewSet(BaseAPITestCase):
    def setUp(self):
        self.create_user()
        self.login()

        pool_size = create_pool_size()
        self.organization = create_organization(get_random_name())
        self.cost = create_sequencing_cost(pool_size, 10, self.organization)

    def test_costs_list(self):
        """Ensure get sequencing costs list behaves correctly."""
        query_kwargs = {"organization": self.organization.pk}
        response = self.client.get(f'{reverse("sequencing-costs-list")}?{urlencode(query_kwargs)}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        costs = [x["name"] for x in response.data]
        self.assertIn(str(self.cost), costs)

    def test_update_price(self):
        """Ensure update price behaves correctly."""
        query_kwargs = {"organization": self.organization.pk}
        url = f'{reverse("sequencing-costs-detail", kwargs={"pk": self.cost.pk})}?{urlencode(query_kwargs)}'
        response = self.client.put(
            path=url,
            data=json.dumps(
                {
                    "id": self.cost.pk,
                    "price": 15,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        updated_cost = SequencingCosts.objects.get(pk=self.cost.pk)
        self.assertEqual(updated_cost.sequencingprice_set.first().price, 15)

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

    # def tearDown(self):
    #     InvoicingReport.objects.all().delete()

    def test_billing_periods_list(self):
        pool_size = create_pool_size()

        flowcell1 = create_flowcell(get_random_name(), pool_size)
        flowcell1.create_time = timezone.datetime(2017, 11, 1, 0, 0, 0, tzinfo=pytz.UTC)
        flowcell1.save()

        flowcell2 = create_flowcell(get_random_name(), pool_size)
        flowcell2.create_time = timezone.datetime(2017, 12, 1, 0, 0, 0, tzinfo=pytz.UTC)
        flowcell2.save()

        response = self.client.get(reverse("invoicing-billing-periods"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            [
                {"name": "November 2017", "value": [2017, 11], "report_urls": []},
                {"name": "December 2017", "value": [2017, 12], "report_urls": []},
            ],
        )

    def test_report_upload(self):

        organization = create_organization(get_random_name())

        month = timezone.now().strftime("%Y-%m")
        response = self.client.post(
            reverse("invoicing-upload"),
            {
                "month": month,
                "organization": str(organization.id),
                "report": SimpleUploadedFile("file.txt", b"content"),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(InvoicingReport.objects.filter(month=month).count(), 1)
