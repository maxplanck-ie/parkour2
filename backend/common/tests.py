import json
import random
import string

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import AttachmentFileType, CostUnit, Organization, PrincipalInvestigator
from .utils import transliterate_name

User = get_user_model()


class BaseTestCase(TestCase):
    def create_user(self, email="test@test.io", password="foo-bar", is_staff=True):
        user = User.objects.create_user(
            email=email, password=password, is_staff=is_staff
        )
        user.save()
        return user

    def login(self, email="test@test.io", password="foo-bar"):
        self.client.login(email=email, password=password)

    def _get_random_name(self, len=10):
        return "".join(
            random.SystemRandom().choice(string.ascii_lowercase + string.digits)
            for _ in range(len)
        )


class BaseAPITestCase(APITestCase):
    def create_user(self, email="test@test.io", password="foo-bar", is_staff=True):
        user = User.objects.create_user(
            email=email, password=password, is_staff=is_staff
        )
        user.save()
        return user

    def login(self, email="test@test.io", password="foo-bar"):
        self.client.login(email=email, password=password)


# Models


class OrganizationTest(TestCase):
    def setUp(self):
        self.organization = Organization(name="Apple")

    def test_organization_name(self):
        self.assertTrue(isinstance(self.organization, Organization))
        self.assertEqual(self.organization.__str__(), self.organization.name)


class PrincipalInvestigatorTest(TestCase):
    def setUp(self):
        self.org = Organization(name="Apple")
        self.pi = PrincipalInvestigator(name="Tim Cook", organization=self.org)

    def test_pi_name(self):
        self.assertTrue(isinstance(self.org, Organization))
        self.assertTrue(isinstance(self.pi, PrincipalInvestigator))
        self.assertEqual(self.pi.__str__(), f"{self.pi.name} ({self.org.name})")


class CostUnitTest(TestCase):
    def setUp(self):
        self.org = Organization(name="Apple")
        self.pi = PrincipalInvestigator(name="Tim Cook", organization=self.org)
        self.cost_unit = CostUnit(name="K", pi=self.pi)

    def test_cost_unit_name(self):
        self.assertTrue(isinstance(self.org, Organization))
        self.assertTrue(isinstance(self.pi, PrincipalInvestigator))
        self.assertTrue(isinstance(self.cost_unit, CostUnit))
        self.assertEqual(
            self.cost_unit.__str__(),
            "%s (%s: %s)"
            % (self.cost_unit.name, self.pi.organization.name, self.pi.name),
        )


# Views


class IndexViewTest(TestCase):
    def setUp(self):
        User.objects.create_user(email="foo@bar.io", password="foo-foo")

    def test_get_redirects_to_vue_app(self):
        self.client.login(email="foo@bar.io", password="foo-foo")
        response = self.client.get(reverse("index"))
        self.assertRedirects(response, "/vue/", fetch_redirect_response=False)

    def test_get_requires_login(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))


class AttachmentFileTypeViewTest(BaseAPITestCase):
    def setUp(self):
        self.create_user()
        self.login()

    def test_only_active_file_types_are_returned(self):
        AttachmentFileType.objects.create(name="Active_Report")
        AttachmentFileType.objects.create(name="Archived_Report", archived=True)

        response = self.client.get(reverse("attachment-file-types-list"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("Active_Report", [item["name"] for item in response.data])
        self.assertNotIn("Archived_Report", [item["name"] for item in response.data])


class NavigationTreeTest(TestCase):
    def setUp(self):
        User.objects.create_user(
            email="admin@bar.io",
            password="foo-foo",
            is_staff=True,
        )

        User.objects.create_user(
            email="user@bar.io",
            password="foo-foo",
            is_staff=False,
        )

    def test_navigation_tree_admin(self):
        self.client.login(email="admin@bar.io", password="foo-foo")
        response = self.client.get(reverse("get_navigation_tree"))
        children = json.loads(str(response.content, "utf-8"))["children"]
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(children), 2)
        statistics = next(item for item in children if item["text"] == "Statistics")
        self.assertEqual(
            [item["viewType"] for item in statistics["children"]],
            ["run-statistics-vue", "sequences-statistics-vue"],
        )

    def test_navigation_tree_user(self):
        self.client.login(email="user@bar.io", password="foo-foo")
        response = self.client.get(reverse("get_navigation_tree"))
        tabs = [
            t["text"] for t in json.loads(str(response.content, "utf-8"))["children"]
        ]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(tabs, ["Libraries & Samples"])


class UserDetailsViewTest(TestCase):
    def setUp(self):
        User.objects.create_user(
            email="admin@bar.io",
            password="foo-foo",
            is_staff=True,
        )

    def test_includes_instance_version(self):
        from django.conf import settings

        self.client.login(email="admin@bar.io", password="foo-foo")
        response = self.client.get(reverse("user_details"))

        self.assertEqual(response.status_code, 200)
        data = json.loads(str(response.content, "utf-8"))
        self.assertEqual(data["INSTANCE_VERSION"], settings.INSTANCE_VERSION)


class PrincipalInvestigatorDeliverToTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="MPI-IE")

    def _pi(self, deliver_to):
        return PrincipalInvestigator(
            name="Cabezas-Wallscheid",
            organization=self.org,
            email="cabezas@test.io",
            deliver_to=deliver_to,
        )

    def test_empty_deliver_to_is_valid(self):
        self._pi("").full_clean()  # should not raise

    def test_lowercase_alpha_deliver_to_is_valid(self):
        self._pi("cabezas").full_clean()  # should not raise

    def test_invalid_deliver_to_values_are_rejected(self):
        for bad in ("Cabezas", "cabezas wallscheid", "cabezas-wallscheid", "cisse1"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValidationError) as ctx:
                    self._pi(bad).full_clean()
                self.assertIn("deliver_to", ctx.exception.error_dict)


class TransliterateNameTest(TestCase):
    """
    Must stay byte-for-byte in sync with dissectBCL's `umlautDestroyer`, since
    it's used to build cross-system-matchable tokens (see internal_pis).
    """

    def test_accents_and_umlauts_are_stripped(self):
        cases = {
            "Cissé": "Cisse",
            "Förtsch": "Fortsch",
            "Müller-Öztürk": "Muller-Ozturk",
            "Weiß": "Weiss",
        }
        for original, expected in cases.items():
            with self.subTest(original=original):
                self.assertEqual(transliterate_name(original), expected)

    def test_spaces_are_removed(self):
        self.assertEqual(transliterate_name("AlHaj Abed"), "AlHajAbed")

    def test_apostrophes_are_removed(self):
        self.assertEqual(transliterate_name("Cisse'"), "Cisse")

    def test_hyphens_are_kept(self):
        self.assertEqual(transliterate_name("Cabezas-Wallscheid"), "Cabezas-Wallscheid")

    def test_plain_ascii_is_unchanged(self):
        self.assertEqual(transliterate_name("Manke"), "Manke")
