from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from common.models import Organization, PrincipalInvestigator

User = get_user_model()


class TestInternalPIsAPI(APITestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            email="staff@test.io", password="foo-bar", is_staff=True
        )
        self.non_staff_user = User.objects.create_user(
            email="nonstaff@test.io", password="foo-bar", is_staff=False
        )
        self.internal_org = Organization.objects.create(name="MPI-IE")
        self.external_org = Organization.objects.create(name="External University")
        PrincipalInvestigator.objects.create(
            name="Cabezas-Wallscheid",
            organization=self.internal_org,
            deliver_to="cabezas",
        )
        PrincipalInvestigator.objects.create(
            name="Manke", organization=self.internal_org
        )
        PrincipalInvestigator.objects.create(
            name="Archived Internal PI",
            organization=self.internal_org,
            archived=True,
        )
        PrincipalInvestigator.objects.create(
            name="External Collaborator", organization=self.external_org
        )

    def test_returns_lowercased_names_for_requested_organizations(self):
        self.client.login(email="staff@test.io", password="foo-bar")
        response = self.client.get(reverse("internal-pis"), {"organizations": "MPI-IE"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            sorted(response.data["pis"]),
            ["cabezas-wallscheid", "manke"],
        )

    def test_pis_is_dict_mapping_name_to_deliver_to(self):
        self.client.login(email="staff@test.io", password="foo-bar")
        response = self.client.get(reverse("internal-pis"), {"organizations": "MPI-IE"})
        self.assertEqual(
            response.data["pis"],
            {"cabezas-wallscheid": "cabezas", "manke": None},
        )

    def test_excludes_archived_pis(self):
        self.client.login(email="staff@test.io", password="foo-bar")
        response = self.client.get(reverse("internal-pis"), {"organizations": "MPI-IE"})
        self.assertNotIn("archived internal pi", response.data["pis"])

    def test_excludes_pis_from_unlisted_organizations(self):
        self.client.login(email="staff@test.io", password="foo-bar")
        response = self.client.get(reverse("internal-pis"), {"organizations": "MPI-IE"})
        self.assertNotIn("external collaborator", response.data["pis"])

    def test_accepts_multiple_comma_separated_organizations(self):
        self.client.login(email="staff@test.io", password="foo-bar")
        response = self.client.get(
            reverse("internal-pis"),
            {"organizations": "MPI-IE,External University"},
        )
        self.assertEqual(
            sorted(response.data["pis"]),
            ["cabezas-wallscheid", "externalcollaborator", "manke"],
        )

    def test_unknown_organization_name_returns_empty_list(self):
        self.client.login(email="staff@test.io", password="foo-bar")
        response = self.client.get(
            reverse("internal-pis"), {"organizations": "Nonexistent Org"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pis"], {})

    def test_missing_organizations_param_returns_400(self):
        self.client.login(email="staff@test.io", password="foo-bar")
        response = self.client.get(reverse("internal-pis"))
        self.assertEqual(response.status_code, 400)

    def test_empty_organizations_param_returns_400(self):
        self.client.login(email="staff@test.io", password="foo-bar")
        response = self.client.get(reverse("internal-pis"), {"organizations": ""})
        self.assertEqual(response.status_code, 400)

    def test_non_staff_user_is_forbidden(self):
        self.client.login(email="nonstaff@test.io", password="foo-bar")
        response = self.client.get(reverse("internal-pis"), {"organizations": "MPI-IE"})
        self.assertEqual(response.status_code, 403)


class TestInternalPIsAPITransliteration(APITestCase):
    """
    dissectBCL derives a PI's on-disk folder token by running the whole
    project name through `umlautDestroyer` (accents/umlauts stripped, spaces
    removed) before matching. This endpoint's keys must be transliterated the
    same way, or an accented/spaced PI name never matches and gets routed as
    external. See common.utils.transliterate_name.
    """

    def setUp(self):
        self.staff_user = User.objects.create_user(
            email="staff@test.io", password="foo-bar", is_staff=True
        )
        self.org = Organization.objects.create(name="MPI-IE")
        self.client.login(email="staff@test.io", password="foo-bar")

    def test_accented_name_is_transliterated(self):
        PrincipalInvestigator.objects.create(name="Cissé", organization=self.org)
        response = self.client.get(reverse("internal-pis"), {"organizations": "MPI-IE"})
        self.assertIn("cisse", response.data["pis"])

    def test_spaced_name_has_spaces_stripped(self):
        PrincipalInvestigator.objects.create(name="AlHaj Abed", organization=self.org)
        response = self.client.get(reverse("internal-pis"), {"organizations": "MPI-IE"})
        self.assertIn("alhajabed", response.data["pis"])

    def test_hyphenated_name_keeps_hyphen(self):
        PrincipalInvestigator.objects.create(
            name="Cabezas-Wallscheid", organization=self.org
        )
        response = self.client.get(reverse("internal-pis"), {"organizations": "MPI-IE"})
        self.assertIn("cabezas-wallscheid", response.data["pis"])
