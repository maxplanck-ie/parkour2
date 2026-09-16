from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from common.models import Organization, PrincipalInvestigator
from library.models import Library
from library_sample_shared.models import AnalysisType
from request.models import Request

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


class TestTurnaroundTimeUsageAPI(APITestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            email="staff@test.io", password="foo-bar", is_staff=True
        )
        self.client.login(email="staff@test.io", password="foo-bar")

        self.org = Organization.objects.create(name="MPI-IE")
        self.pi_a = PrincipalInvestigator.objects.create(
            name="PI A", organization=self.org
        )
        self.pi_b = PrincipalInvestigator.objects.create(
            name="PI B", organization=self.org
        )

        self.now = timezone.now()
        self._requester_count = 0

    def _requester(self, pi):
        self._requester_count += 1
        slug = pi.name.lower().replace(" ", "")
        return User.objects.create_user(
            email=f"{slug}{self._requester_count}@test.io",
            password="foo-bar",
            pi=pi,
        )

    def _make_request(self, pi, approved_days_ago, loaded_days_ago):
        req = Request.objects.create(
            user=self._requester(pi),
            approval={
                "TIMESTAMP": (self.now - timedelta(days=approved_days_ago)).isoformat(),
            },
        )
        req.flowcell_loaded_at = self.now - timedelta(days=loaded_days_ago)
        req.save()
        return req

    def _date_range_params(self, group_by=None):
        params = {
            "start": (self.now - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S"),
            "end": (self.now + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S"),
        }
        if group_by:
            params["group_by"] = group_by
        return params

    def test_returns_box_values_per_pi(self):
        # PI A: turnaround of 10 and 20 days.
        self._make_request(self.pi_a, approved_days_ago=30, loaded_days_ago=20)
        self._make_request(self.pi_a, approved_days_ago=30, loaded_days_ago=10)

        response = self.client.get(
            reverse("turnaround-time-usage"), self._date_range_params()
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        row = response.data[0]
        self.assertEqual(row["name"], "PI A")
        low, q1, median, q3, high = row["data"]
        self.assertEqual(low, 10)
        self.assertEqual(median, 15)
        self.assertEqual(high, 20)

    def test_skips_requests_without_approval_timestamp(self):
        req = Request.objects.create(user=self._requester(self.pi_a))
        req.flowcell_loaded_at = self.now
        req.save()

        response = self.client.get(
            reverse("turnaround-time-usage"), self._date_range_params()
        )
        self.assertEqual(response.data, [])

    def test_skips_negative_turnaround(self):
        self._make_request(self.pi_a, approved_days_ago=5, loaded_days_ago=10)

        response = self.client.get(
            reverse("turnaround-time-usage"), self._date_range_params()
        )
        self.assertEqual(response.data, [])

    def test_excludes_requests_outside_date_range(self):
        self._make_request(self.pi_a, approved_days_ago=500, loaded_days_ago=400)

        response = self.client.get(
            reverse("turnaround-time-usage"), self._date_range_params()
        )
        self.assertEqual(response.data, [])

    def test_groups_by_analysis_type(self):
        analysis_type = AnalysisType.objects.create(name="RNA-seq")
        req = self._make_request(self.pi_a, approved_days_ago=30, loaded_days_ago=20)
        library = Library.objects.create(
            name="Library1",
            sequencing_depth=1,
            barcode="L0001",
            analysis_type=analysis_type,
        )
        req.libraries.add(library)

        response = self.client.get(
            reverse("turnaround-time-usage"),
            self._date_range_params(group_by="analysis_type"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "RNA-seq")
        self.assertEqual(response.data[0]["data"][2], 10)

    def test_non_staff_user_is_forbidden(self):
        self.client.logout()
        User.objects.create_user(
            email="nonstaff@test.io", password="foo-bar", is_staff=False
        )
        self.client.login(email="nonstaff@test.io", password="foo-bar")
        response = self.client.get(reverse("turnaround-time-usage"))
        self.assertEqual(response.status_code, 403)
