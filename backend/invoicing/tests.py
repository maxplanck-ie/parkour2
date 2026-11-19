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
from .pricing import PriceBook


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


# Historical pricing


class TestPriceBook(BaseTestCase):
    """PriceBook reads prices from simple_history as of a given date."""

    def setUp(self):
        from datetime import datetime, timezone as dt_timezone
        from invoicing.pricing import PriceBook

        self.sequencer = create_sequencer("NovaSeq SP (XP)")
        self.read_length = create_read_length("2x150")
        self.protocol = create_library_protocol("TruSeq Stranded mRNA")
        self.qc_protocol = create_library_protocol("Quality Control")

        # Initial prices
        self.fixed_cost = create_fixed_cost(self.sequencer, "340.00")
        self.seq_cost = create_sequencing_cost(
            self.sequencer, self.read_length, "1415.39"
        )
        self.prep_cost = create_preparation_cost(self.protocol, "124.35")
        self.qc_cost = create_preparation_cost(self.qc_protocol, "86.32")

        self.price_book = PriceBook()
        self.base_date = datetime(2026, 1, 1, tzinfo=dt_timezone.utc)

    def test_fixed_price_current(self):
        price = self.price_book.fixed(self.sequencer.pk, self.base_date)
        self.assertEqual(str(price), "340.00")

    def test_sequencing_price_current(self):
        price = self.price_book.sequencing(
            self.sequencer.pk, self.read_length.pk, self.base_date
        )
        self.assertEqual(str(price), "1415.39")

    def test_preparation_price_current(self):
        price = self.price_book.preparation(self.protocol.pk, self.base_date)
        self.assertEqual(str(price), "124.35")

    def test_qc_price_by_name(self):
        price = self.price_book.preparation_by_name("Quality Control", self.base_date)
        self.assertEqual(str(price), "86.32")

    def test_price_history_updates(self):
        """Changing a price records a history row and PriceBook uses the right one by date."""
        from datetime import datetime, timezone as dt_timezone

        # Price change via save() records history
        old_price = str(self.fixed_cost.price)
        self.fixed_cost.price = "400.00"
        self.fixed_cost.save()
        self.price_book = PriceBook()

        before_change = datetime(2026, 1, 1, tzinfo=dt_timezone.utc)
        after_change = datetime(2026, 12, 31, tzinfo=dt_timezone.utc)

        # Before change -> old price
        self.assertEqual(str(self.price_book.fixed(self.sequencer.pk, before_change)), old_price)
        # After change -> new price
        self.assertEqual(str(self.price_book.fixed(self.sequencer.pk, after_change)), "400.00")

    def test_sequencing_price_history_updates(self):
        from datetime import datetime, timezone as dt_timezone

        old_price = str(self.seq_cost.price)
        self.seq_cost.price = "1500.00"
        self.seq_cost.save()
        self.price_book = PriceBook()

        before_change = datetime(2026, 1, 1, tzinfo=dt_timezone.utc)
        after_change = datetime(2026, 12, 31, tzinfo=dt_timezone.utc)

        self.assertEqual(
            str(
                self.price_book.sequencing(
                    self.sequencer.pk, self.read_length.pk, before_change
                )
            ),
            old_price,
        )
        self.assertEqual(
            str(
                self.price_book.sequencing(
                    self.sequencer.pk, self.read_length.pk, after_change
                )
            ),
            "1500.00",
        )

    def test_preparation_price_history_updates(self):
        from datetime import datetime, timezone as dt_timezone

        old_price = str(self.prep_cost.price)
        self.prep_cost.price = "130.00"
        self.prep_cost.save()
        self.price_book = PriceBook()

        before_change = datetime(2026, 1, 1, tzinfo=dt_timezone.utc)
        after_change = datetime(2026, 12, 31, tzinfo=dt_timezone.utc)

        self.assertEqual(
            str(self.price_book.preparation(self.protocol.pk, before_change)), old_price
        )
        self.assertEqual(
            str(self.price_book.preparation(self.protocol.pk, after_change)), "130.00"
        )

    def test_missing_key_returns_zero(self):
        other_sequencer = create_sequencer("Other")
        self.assertEqual(self.price_book.fixed(other_sequencer.pk, self.base_date), 0)
        self.assertEqual(
            self.price_book.sequencing(
                self.sequencer.pk, create_read_length("2x75").pk, self.base_date
            ),
            0,
        )
        self.assertEqual(
            self.price_book.preparation(create_library_protocol("Other").pk, self.base_date),
            0,
        )

    def test_archived_price_returns_zero(self):
        """Archiving a price means it was not billable in that period."""
        from datetime import datetime, timezone as dt_timezone

        self.fixed_cost.archived = True
        self.fixed_cost.save()
        self.price_book = PriceBook()

        after_archive = datetime(2026, 12, 31, tzinfo=dt_timezone.utc)
        price = self.price_book.fixed(self.sequencer.pk, after_archive)
        self.assertEqual(str(price), "0")


class TestInvoicingHistoricalPrices(BaseAPITestCase):
    """Invoicing serializer uses PriceBook for historical cost calculation."""

    def setUp(self):
        from datetime import datetime, timezone as dt_timezone
        from django.contrib.auth import get_user_model
        from flowcell.models import Flowcell
        from index_generator.tests import create_pool
        from library.models import Library
        from request.models import Request
        from request.tests import create_request

        self.create_user()
        self.login()
        User = get_user_model()
        self.user = User.objects.first()
        self.sequencer = create_sequencer("NovaSeq SP (XP)")
        self.read_length = create_read_length("2x150")
        self.protocol = create_library_protocol("TruSeq Stranded mRNA")
        self.qc_protocol = create_library_protocol("Quality Control")

        # Prices
        create_fixed_cost(self.sequencer, "340.00")
        create_sequencing_cost(self.sequencer, self.read_length, "1415.39")
        create_preparation_cost(self.protocol, "124.35")
        create_preparation_cost(self.qc_protocol, "86.32")

        # Request with flowcell in January 2026
        self.request = create_request(self.user)
        self.request.sequenced = True
        self.request.save()

        self.flowcell = Flowcell.objects.create(
            flowcell_id="HISTFC001",
            sequencer=self.sequencer,
        )
        Flowcell.objects.filter(pk=self.flowcell.pk).update(
            create_time=datetime(2026, 1, 15, tzinfo=dt_timezone.utc)
        )
        self.flowcell.refresh_from_db()
        self.flowcell.requests.add(self.request)

        self.pool = create_pool(self.user)
        self.flowcell.lanes.create(name="1", pool=self.pool)

        self.library = Library.objects.create(
            library_protocol=self.protocol,
            read_length=self.read_length,
            sequencing_depth=100,
        )
        self.request.libraries.add(self.library)
        self.pool.libraries.add(self.library)

    def test_invoicing_uses_price_at_flowcell_date(self):
        """Invoice for Jan 2026 uses prices in force on flowcell date, not today."""
        from django.urls import reverse

        # Change price AFTER the flowcell date (records history via save)
        fixed = FixedCosts.objects.get(sequencer=self.sequencer)
        fixed.price = "500.00"
        fixed.save()

        # Query Jan 2026
        response = self.client.get(
            reverse("invoicing-list"),
            {"start": "2026-01", "end": "2026-01"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0, f"no rows: {response.data}")

        row = next(r for r in response.data if r["request"] == self.request.name)
        # Fixed cost should be old price (340), not new (500)
        self.assertEqual(row["fixed_costs"], 340.00)
        # Total reflects old fixed cost
        self.assertIn("total_costs", row)


class TestCostAdminArchivalRemoved(BaseAPITestCase):
    """Archival actions removed from cost admins; history replaces archival."""

    def setUp(self):
        from django.contrib.admin.sites import site
        from invoicing.models import FixedCosts, LibraryPreparationCosts, SequencingCosts

        self.create_user()
        self.login()

        self.sequencer = create_sequencer("TestSeq")
        self.read_length = create_read_length("2x150")
        self.protocol = create_library_protocol("TestProtocol")

        self.fixed = create_fixed_cost(self.sequencer, 100)
        self.seq = create_sequencing_cost(self.sequencer, self.read_length, 200)
        self.prep = create_preparation_cost(self.protocol, 50)

    def test_fixed_cost_admin_no_archive_actions(self):
        from django.contrib.admin.sites import site
        from invoicing.models import FixedCosts

        admin_class = site._registry[FixedCosts]
        # No archived in list_display
        self.assertNotIn("archived", admin_class.list_display)
        # No mark_as_archived action
        self.assertNotIn("mark_as_archived", admin_class.actions)
        self.assertNotIn("mark_as_non_archived", admin_class.actions)

    def test_prep_cost_admin_no_archive_actions(self):
        from django.contrib.admin.sites import site
        from invoicing.models import LibraryPreparationCosts

        admin_class = site._registry[LibraryPreparationCosts]
        self.assertNotIn("archived", admin_class.list_display)
        self.assertNotIn("mark_as_archived", admin_class.actions)
        self.assertNotIn("mark_as_non_archived", admin_class.actions)

    def test_seq_cost_admin_no_archive_actions(self):
        from django.contrib.admin.sites import site
        from invoicing.models import SequencingCosts

        admin_class = site._registry[SequencingCosts]
        self.assertNotIn("archived", admin_class.list_display)
        self.assertNotIn("mark_as_archived", admin_class.actions)
        self.assertNotIn("mark_as_non_archived", admin_class.actions)

    def test_cost_api_returns_all_prices_not_filtered_by_archived(self):
        """API endpoints now return all prices; archiving is not a filter."""
        from django.urls import reverse

        # Archive them in DB directly (simulate legacy data)
        FixedCosts.objects.filter(pk=self.fixed.pk).update(archived=True)
        SequencingCosts.objects.filter(pk=self.seq.pk).update(archived=True)
        LibraryPreparationCosts.objects.filter(pk=self.prep.pk).update(archived=True)

        # All three endpoints should still return them
        for url_name in (
            "fixed-costs-list",
            "sequencing-costs-list",
            "library-preparation-costs-list",
        ):
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200)
            self.assertGreaterEqual(len(response.data), 1)
