from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from common.models import Organization, PrincipalInvestigator
from library.models import Library
from sample.models import Sample
from flowcell.models import Flowcell, Sequencer
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
        self.sequencer = Sequencer.objects.create(
            name="Sequencer", lanes=1, lane_capacity=100
        )
        self._flowcell_count = 0
        self._record_count = 0

    def _requester(self, pi):
        self._requester_count += 1
        slug = pi.name.lower().replace(" ", "")
        return User.objects.create_user(
            email=f"{slug}{self._requester_count}@test.io",
            password="foo-bar",
            pi=pi,
        )

    def _add_flowcell(self, req, days_ago, archived=False, sequencer=None):
        """Attach a flowcell to req, with create_time set to days_ago."""
        self._flowcell_count += 1
        flowcell = Flowcell.objects.create(
            flowcell_id=f"FC{self._flowcell_count}",
            sequencer=sequencer or self.sequencer,
            archived=archived,
        )
        # create_time is auto_now_add, so backdate it with a queryset update.
        Flowcell.objects.filter(pk=flowcell.pk).update(
            create_time=self.now - timedelta(days=days_ago)
        )
        flowcell.requests.add(req)
        return flowcell

    def _make_request(self, pi, approved_days_ago, loaded_days_ago):
        """Create a request submitted approved_days_ago, on a flowcell loaded
        loaded_days_ago."""
        req = Request.objects.create(
            user=self._requester(pi),
            submitted_at=self.now - timedelta(days=approved_days_ago),
        )
        self._add_flowcell(req, loaded_days_ago)
        return req

    def _date_range_params(self, group_by=None, record_type=None):
        params = {
            "start": (self.now - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S"),
            "end": (self.now + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S"),
        }
        if group_by:
            params["group_by"] = group_by
        if record_type:
            params["record_type"] = record_type
        return params

    def test_returns_box_values_per_sequencer(self):
        # PI A: turnaround of 10 and 20 days.
        self._make_request(self.pi_a, approved_days_ago=30, loaded_days_ago=20)
        self._make_request(self.pi_a, approved_days_ago=30, loaded_days_ago=10)

        response = self.client.get(
            reverse("turnaround-time-usage"), self._date_range_params()
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        row = response.data[0]
        self.assertEqual(row["name"], "Sequencer")
        low, q1, median, q3, high = row["data"]
        self.assertEqual(low, 10)
        self.assertEqual(median, 15)
        self.assertEqual(high, 20)

    def test_skips_requests_without_submitted_at(self):
        req = Request.objects.create(user=self._requester(self.pi_a))
        self._add_flowcell(req, days_ago=0)

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

    def test_uses_earliest_flowcell(self):
        req = self._make_request(self.pi_a, approved_days_ago=30, loaded_days_ago=20)
        self._add_flowcell(req, days_ago=5)

        response = self.client.get(
            reverse("turnaround-time-usage"), self._date_range_params()
        )
        self.assertEqual(response.data[0]["data"][2], 10)

    def test_ignores_archived_flowcells(self):
        req = Request.objects.create(
            user=self._requester(self.pi_a),
            submitted_at=self.now - timedelta(days=30),
        )
        self._add_flowcell(req, days_ago=20, archived=True)
        self._add_flowcell(req, days_ago=10)

        response = self.client.get(
            reverse("turnaround-time-usage"), self._date_range_params()
        )
        self.assertEqual(response.data[0]["data"][2], 20)

    def test_skips_requests_without_flowcell(self):
        Request.objects.create(
            user=self._requester(self.pi_a),
            submitted_at=self.now - timedelta(days=30),
        )

        response = self.client.get(
            reverse("turnaround-time-usage"), self._date_range_params()
        )
        self.assertEqual(response.data, [])

    def test_non_staff_user_is_forbidden(self):
        self.client.logout()
        User.objects.create_user(
            email="nonstaff@test.io", password="foo-bar", is_staff=False
        )
        self.client.login(email="nonstaff@test.io", password="foo-bar")
        response = self.client.get(reverse("turnaround-time-usage"))
        self.assertEqual(response.status_code, 403)

    def _add_records(self, req, analysis_type, libraries=0, samples=0):
        for _ in range(libraries):
            self._record_count += 1
            req.libraries.add(
                Library.objects.create(
                    name=f"Library{self._record_count}",
                    sequencing_depth=1,
                    barcode=f"L{self._record_count:04d}",
                    analysis_type=analysis_type,
                )
            )
        for _ in range(samples):
            self._record_count += 1
            req.samples.add(
                Sample.objects.create(
                    name=f"Sample{self._record_count}",
                    sequencing_depth=1,
                    barcode=f"S{self._record_count:04d}",
                    analysis_type=analysis_type,
                )
            )

    def _names(self, response):
        return {row["name"]: row["data"] for row in response.data}

    def test_groups_by_first_flowcells_sequencer(self):
        other = Sequencer.objects.create(name="Other", lanes=1, lane_capacity=100)
        req = Request.objects.create(
            user=self._requester(self.pi_a),
            submitted_at=self.now - timedelta(days=30),
        )
        self._add_flowcell(req, days_ago=20, sequencer=other)
        self._add_flowcell(req, days_ago=10)
        # Archived earlier flowcell on the default sequencer is ignored.
        self._add_flowcell(req, days_ago=25, archived=True)

        response = self.client.get(
            reverse("turnaround-time-usage"),
            self._date_range_params(group_by="sequencer"),
        )
        self.assertEqual(list(self._names(response)), ["Other"])
        self.assertEqual(response.data[0]["data"][2], 10)

    def test_request_without_sequencer_grouped_as_none(self):
        req = Request.objects.create(
            user=self._requester(self.pi_a),
            submitted_at=self.now - timedelta(days=30),
        )
        flowcell = self._add_flowcell(req, days_ago=20)
        Flowcell.objects.filter(pk=flowcell.pk).update(sequencer=None)

        response = self.client.get(
            reverse("turnaround-time-usage"),
            self._date_range_params(group_by="sequencer"),
        )
        self.assertEqual(list(self._names(response)), ["None"])

    def test_record_type_limits_requests_to_selected_kind(self):
        analysis_type = AnalysisType.objects.create(name="RNA-seq")
        lib_req = self._make_request(self.pi_a, 30, 20)
        self._add_records(lib_req, analysis_type, libraries=2)
        sample_req = self._make_request(self.pi_a, 30, 10)
        self._add_records(sample_req, analysis_type, samples=2)
        self._make_request(self.pi_a, 30, 5)  # no records

        url = reverse("turnaround-time-usage")
        params = self._date_range_params()
        counts = {}
        for record_type in ("all", "libraries", "samples"):
            response = self.client.get(url, {**params, "record_type": record_type})
            counts[record_type] = response.data[0]["data"]
        self.assertEqual(counts["libraries"][2], 10)
        self.assertEqual(counts["libraries"][0], 10)
        self.assertEqual(counts["libraries"][4], 10)
        self.assertEqual(counts["samples"][2], 20)
        self.assertEqual(counts["all"][0], 10)
        self.assertEqual(counts["all"][4], 25)

    def test_request_with_multiple_records_counted_once(self):
        analysis_type = AnalysisType.objects.create(name="RNA-seq")
        req_a = self._make_request(self.pi_a, 30, 10)
        self._add_records(req_a, analysis_type, libraries=3)
        req_b = self._make_request(self.pi_a, 30, 20)
        self._add_records(req_b, analysis_type, libraries=1)

        response = self.client.get(
            reverse("turnaround-time-usage"),
            self._date_range_params(record_type="libraries"),
        )
        # Two requests -> values [20, 10]; duplicated joins would skew the median.
        self.assertEqual(response.data[0]["data"][2], 15)

    def test_analysis_type_grouping_only_includes_selected_kind(self):
        lib_type = AnalysisType.objects.create(name="Lib type")
        sample_type = AnalysisType.objects.create(name="Sample type")
        req = self._make_request(self.pi_a, 30, 20)
        self._add_records(req, lib_type, libraries=1)
        self._add_records(req, sample_type, samples=1)

        url = reverse("turnaround-time-usage")
        for record_type, expected in (
            ("libraries", {"Lib type"}),
            ("samples", {"Sample type"}),
            ("all", {"Lib type", "Sample type"}),
        ):
            response = self.client.get(
                url,
                self._date_range_params(
                    group_by="analysis_type", record_type=record_type
                ),
            )
            self.assertEqual(set(self._names(response)), expected, record_type)

    def test_invalid_record_type_defaults_to_all(self):
        self._make_request(self.pi_a, 30, 20)

        response = self.client.get(
            reverse("turnaround-time-usage"),
            self._date_range_params(record_type="bogus"),
        )
        self.assertEqual(len(response.data), 1)
