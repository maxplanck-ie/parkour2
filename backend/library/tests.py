import json
from io import BytesIO
from zipfile import ZipFile
from unittest.mock import patch
from django.core.files.base import ContentFile
from request.models import FileRequest

from common.tests import BaseAPITestCase, BaseTestCase
from common.utils import get_random_name, timezone
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from library.models import CompleteLibraryData, Library
from library_preparation.models import LibraryPreparation
from library_sample_shared.models import (
    BarcodeCounter,
    IndexType,
    LibraryProtocol,
    LibraryType,
    Organism,
    ReadLength,
)
from pooling.models import Pooling
from request.models import Request
from sample.models import CompleteSampleData
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
        measured_value=1.0,
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


class _MockQuerySet(list):
    def filter(self, *args, **kwargs):
        return self


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
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertTrue(payload.get("success"))
        self.assertIn("children", payload)
        self.assertIsInstance(payload["children"], list)

        if payload["children"]:
            record = payload["children"][0]
            self.assertIn("record_type", record)
            self.assertIn(record["record_type"], {"Library", "Sample"})
            self.assertIn("barcode", record)
            self.assertIn("measuring_unit_facility", record)
            self.assertIn("measured_value_facility", record)


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
                            "measured_value": 1.0,
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
                            "measured_value": 1.0,
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
                            "measured_value": -3,
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
                            "measured_value": 1.0,
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
                            "measured_value": 1.0,
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
                            "measured_value": -3,
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


class TestGenerateROCrateAPI(BaseAPITestCase):
    """Tests for the RO-Crate export endpoint."""

    def setUp(self):
        super().setUp()
        self.user = self.create_user("rocrate@test.io", "foo-bar")
        self.user.first_name = "Test"
        self.user.last_name = "User"
        self.user.save()
        self.client.login(email="rocrate@test.io", password="foo-bar")
        self.request = Request.objects.create(user=self.user)
        self.request.refresh_from_db()

    def _parse_payload(self, response):
        if hasattr(response, "data"):
            return response.data
        return json.loads(response.content.decode("utf-8"))

    def _graph_entry(self, payload, entity_id):
        return next(
            (entry for entry in payload["@graph"] if entry.get("@id") == entity_id),
            {},
        )

    def _comment_names(self, entry):
        names = {comment.get("name") for comment in entry.get("comments", [])}
        names.update(
            {
                prop.get("name")
                for prop in entry.get("additionalProperty", [])
                if isinstance(prop, dict)
            }
        )
        names.update(
            {
                prop.get("name")
                for prop in entry.get("parameterValue", [])
                if isinstance(prop, dict)
            }
        )
        return names

    def _ref_ids(self, value):
        if isinstance(value, list):
            return {item.get("@id") for item in value if isinstance(item, dict)}
        if isinstance(value, dict):
            return {value.get("@id")}
        return set()

    def _extract_zip_payload(self, response):
        self.assertEqual(response["Content-Type"], "application/zip")
        zip_buffer = BytesIO(response.content)
        with ZipFile(zip_buffer, "r") as zip_file:
            payload = json.loads(zip_file.read("ro-crate-metadata.json").decode("utf-8"))
            archive_names = set(zip_file.namelist())
        return payload, archive_names

    def test_requires_identifier_parameters(self):
        """Request must provide barcodes or request names."""
        response = self.client.get(reverse("generate-ro-crate-list"))
        self.assertEqual(response.status_code, 400)
        payload = self._parse_payload(response)
        self.assertIn("error", payload)

    @patch("library.ro_crate.CompleteSampleData.objects")
    @patch("library.ro_crate.CompleteLibraryData.objects")
    def test_returns_placeholder_when_no_matches(
        self, mock_library_objects, mock_sample_objects
    ):
        """Unknown identifiers should return an empty crate with a helpful message."""
        mock_library_objects.filter.return_value = _MockQuerySet()
        mock_sample_objects.filter.return_value = _MockQuerySet()

        response = self.client.get(
            reverse("generate-ro-crate-list"), {"barcodes": "UNKNOWN123"}
        )
        self.assertEqual(response.status_code, 200)
        payload, archive_names = self._extract_zip_payload(response)
        self.assertIn("@graph", payload)
        self.assertIn("ro-crate-metadata.json", archive_names)

        dataset_entry = next(
            (entry for entry in payload["@graph"] if entry.get("@id") == "./"), {}
        )
        self.assertEqual(
            dataset_entry.get("description"),
            "No matching barcodes or requests were found.",
        )

    @patch("library.ro_crate.CompleteSampleData.objects")
    @patch("library.ro_crate.CompleteLibraryData.objects")
    def test_generates_ro_crate_for_request_name(
        self, mock_library_objects, mock_sample_objects
    ):
        """Exporting by request name should yield a structured RO-Crate."""
        mock_library_objects.filter.return_value = _MockQuerySet()
        mock_sample_objects.filter.return_value = _MockQuerySet()

        response = self.client.get(
            reverse("generate-ro-crate-list"), {"requests": self.request.name}
        )
        self.assertEqual(response.status_code, 200)
        payload, archive_names = self._extract_zip_payload(response)
        self.assertIn("@graph", payload)
        self.assertIn("ro-crate-metadata.json", archive_names)

        graph_ids = {entry.get("@id") for entry in payload["@graph"]}
        self.assertIn("./", graph_ids)
        self.assertIn(f"#study-{self.request.id}", graph_ids)

        dataset_entry = next(
            (entry for entry in payload["@graph"] if entry.get("@id") == "./"), {}
        )
        self.assertEqual(dataset_entry.get("name"), self.request.name)
        self.assertEqual(
            dataset_entry.get("conformsTo"),
            [
                {
                    "@id": "https://github.com/nfdi4plants/isa-ro-crate-profile/tree/release/profile"
                }
            ],
        )
        self.assertIn(
            {"@id": f"#study-{self.request.id}"},
            dataset_entry.get("hasPart", []),
        )
        self.assertEqual(dataset_entry.get("creator"), {"@id": f"#person-{self.user.id}"})
        self.assertEqual(dataset_entry.get("publisher"), {"@id": "#parkour-organization"})
        self.assertIn(
            "https://github.com/nfdi4plants/isa-ro-crate-profile/tree/release/profile",
            graph_ids,
        )
        self.assertIn("#ro-crate-export-action", {entry.get("@id") for entry in payload["@graph"]})

    @patch("library.ro_crate.CompleteSampleData.objects")
    @patch("library.ro_crate.CompleteLibraryData.objects")
    def test_sample_export_keeps_model_and_mv_fields(self, mock_library_objects, mock_sample_objects):
        mock_library_objects.filter.return_value = _MockQuerySet()
        sample = create_sample("crate-sample")
        self.request.samples.add(sample)
        request_file = FileRequest.objects.create(name="req.txt")
        request_file.file.save("req.txt", ContentFile(b"ro-crate test file"), save=True)
        self.request.files.add(request_file)
        LibraryPreparation.objects.create(
            sample=sample,
            starting_amount=12.5,
            pcr_cycles=9,
            concentration_library=3.2,
            mean_fragment_size=280,
        )
        Pooling.objects.create(sample=sample, concentration_c1=4.4, comment="sample pool")

        sample_mv = CompleteSampleData(
            sample_id=sample.pk,
            barcode=sample.barcode,
            name=sample.name,
            status=sample.status,
            sequencing_depth=sample.sequencing_depth,
            nucleic_acid_type_id=sample.nucleic_acid_type_id,
            nucleic_acid_type_name=sample.nucleic_acid_type.name,
            measuring_unit=sample.measuring_unit or "",
            measured_value=sample.measured_value or 0,
            measuring_unit_facility=sample.measuring_unit_facility or "",
            measured_value_facility=sample.measured_value_facility or 0,
            concentration_library=1.5,
            gmo=False,
            library_protocol_id=sample.library_protocol_id,
            library_protocol_name=sample.library_protocol.name,
            analysis_type_id=1,
            analysis_type_name="RNA-seq",
            read_length_id=sample.read_length_id,
            read_length_name=sample.read_length.name,
            average_fragment_size=250.0,
            starting_amount=5.0,
            pcr_cycles=8,
            index_type_name=sample.index_type.name if sample.index_type else None,
            coordinate="A1",
            index_i7="ACGT",
            i7_id="IDX7",
            index_i5="TGCA",
            i5_id="IDX5",
            request_id=self.request.id,
            request_name=self.request.name,
            create_time=self.request.create_time,
            pool_names=["Pool1"],
            flowcell_ids=["FC1"],
            sequencer_ids=[1],
            sequencer_names=["Seq1"],
        )
        mock_sample_objects.filter.return_value = _MockQuerySet([sample_mv])

        response = self.client.get(
            reverse("generate-ro-crate-list"), {"barcodes": sample.barcode}
        )
        self.assertEqual(response.status_code, 200)
        payload, archive_names = self._extract_zip_payload(response)

        sample_entry = self._graph_entry(payload, f"#sample-material-{sample.pk}")
        self.assertEqual(sample_entry.get("identifier"), sample.barcode)
        self.assertIn({"@id": f"#source-sample-{sample.pk}"}, sample_entry.get("derivedFrom", []))
        comment_names = self._comment_names(sample_entry)
        self.assertIn("sample_db_name", comment_names)
        self.assertIn("sample_db_barcode", comment_names)
        self.assertIn("sample_mv_analysis_type_name", comment_names)
        self.assertIn("sample_mv_pool_names", comment_names)
        self.assertIn("sample_mv_sequencer_names", comment_names)
        self.assertIn("sample_mv_flowcell_ids", comment_names)
        self.assertIn("sample_mv_starting_amount", comment_names)
        self.assertIn("sample_mv_pcr_cycles", comment_names)
        self.assertIn("library_preparation_starting_amount", comment_names)
        self.assertEqual(
            sample_entry.get("nucleicAcidType"),
            {"@id": f"#nucleic-acid-type-{sample.nucleic_acid_type_id}"},
        )
        self.assertEqual(
            sample_entry.get("organism"),
            {"@id": f"#organism-{sample.organism_id}"},
        )
        self.assertEqual(
            sample_entry.get("libraryType"),
            {"@id": f"#library-type-{sample.library_type_id}"},
        )
        process_entry = self._graph_entry(payload, f"#sample-process-{sample.pk}")
        self.assertEqual(
            process_entry.get("executesLabProtocol"),
            {"@id": f"#protocol-{sample.library_protocol_id}"},
        )
        request_file_entity_id = next(
            (
                entry.get("@id")
                for entry in payload["@graph"]
                if entry.get("identifier") == f"urn:parkour:request-file:{request_file.pk}"
            ),
            None,
        )
        self.assertIsNotNone(request_file_entity_id)
        request_file_entry = self._graph_entry(payload, request_file_entity_id)
        self.assertEqual(request_file_entry.get("@type"), "MediaObject")
        self.assertEqual(
            request_file_entry.get("isPartOf"),
            {"@id": "./"},
        )
        self.assertIn(request_file_entity_id, archive_names)
        dataset_entry = self._graph_entry(payload, "./")
        self.assertIn(
            {"@id": request_file_entity_id},
            dataset_entry.get("hasPart", []),
        )

    @patch("library.ro_crate.CompleteSampleData.objects")
    @patch("library.ro_crate.CompleteLibraryData.objects")
    def test_rejects_multi_request_selection(
        self, mock_library_objects, mock_sample_objects
    ):
        other_request = Request.objects.create(user=self.user)
        mock_library_objects.filter.return_value = _MockQuerySet()
        mock_sample_objects.filter.return_value = _MockQuerySet()

        response = self.client.get(
            reverse("generate-ro-crate-list"),
            {"requests": f"{self.request.name},{other_request.name}"},
        )
        self.assertEqual(response.status_code, 400)
        payload = self._parse_payload(response)
        self.assertIn("exactly one request", payload.get("error", ""))

    @patch("library.ro_crate.CompleteSampleData.objects")
    @patch("library.ro_crate.CompleteLibraryData.objects")
    def test_library_export_keeps_model_and_mv_fields(self, mock_library_objects, mock_sample_objects):
        mock_sample_objects.filter.return_value = _MockQuerySet()
        library = create_library("crate-library")
        self.request.libraries.add(library)
        Pooling.objects.create(library=library, concentration_c1=6.6, comment="library pool")

        library_mv = CompleteLibraryData(
            library_id=library.pk,
            barcode=library.barcode,
            name=library.name,
            status=library.status,
            sequencing_depth=library.sequencing_depth,
            measuring_unit=library.measuring_unit or "",
            measured_value=library.measured_value or 0,
            measuring_unit_facility=library.measuring_unit_facility or "",
            measured_value_facility=library.measured_value_facility or 0,
            concentration_library=2.5,
            percent_total=library.percent_total,
            library_protocol_id=library.library_protocol_id,
            library_protocol_name=library.library_protocol.name,
            analysis_type_id=2,
            analysis_type_name="WGS",
            read_length_id=library.read_length_id,
            read_length_name=library.read_length.name,
            average_fragment_size=300.0,
            index_type_name=library.index_type.name if library.index_type else None,
            coordinate="B2",
            index_i7="AAAA",
            i7_id="LIDX7",
            index_i5="CCCC",
            i5_id="LIDX5",
            request_id=self.request.id,
            request_name=self.request.name,
            create_time=self.request.create_time,
            pool_names=["PoolA"],
            flowcell_ids=["FC9"],
            sequencer_ids=[9],
            sequencer_names=["NovaSeq"],
        )
        mock_library_objects.filter.return_value = _MockQuerySet([library_mv])

        response = self.client.get(
            reverse("generate-ro-crate-list"), {"barcodes": library.barcode}
        )
        self.assertEqual(response.status_code, 200)
        payload, _ = self._extract_zip_payload(response)

        library_entry = self._graph_entry(payload, f"#library-material-{library.pk}")
        self.assertEqual(library_entry.get("identifier"), library.barcode)
        self.assertIn("library_db_name", self._comment_names(library_entry))

        process_entry = self._graph_entry(payload, f"#library-process-{library.pk}")
        process_comment_names = self._comment_names(process_entry)
        self.assertIn("library_mv_status", process_comment_names)
        self.assertIn("library_mv_analysis_type_name", process_comment_names)
        self.assertIn("library_mv_pool_names", process_comment_names)
        self.assertIn("library_mv_flowcell_ids", process_comment_names)
        self.assertIn("library_mv_sequencer_names", process_comment_names)
        self.assertIn("library_mv_percent_total", process_comment_names)
        self.assertIn("library_mv_coordinate", process_comment_names)
        self.assertIn("library_mv_i7_id", process_comment_names)
        self.assertIn("library_mv_i5_id", process_comment_names)
        self.assertIn("executesLabProtocol", process_entry)
        self.assertEqual(
            library_entry.get("organism"),
            {"@id": f"#organism-{library.organism_id}"},
        )
        self.assertEqual(
            library_entry.get("libraryType"),
            {"@id": f"#library-type-{library.library_type_id}"},
        )
        self.assertEqual(
            library_entry.get("readLength"),
            {"@id": f"#read-length-{library.read_length_id}"},
        )
        self.assertEqual(
            library_entry.get("indexType"),
            {"@id": f"#index-type-{library.index_type_id}"},
        )
