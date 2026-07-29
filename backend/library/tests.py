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
from flowcell.models import Flowcell, Lane, Sequencer
from index_generator.models import Pool, PoolSize
from library.models import CompleteLibraryData, Library
from library.ro_crate import (
    ROCratePdfRenderer,
    _ro_crate_archive_name,
    _ro_crate_pdf_name,
)
from library_preparation.models import LibraryPreparation
from library_sample_shared.models import (
    BarcodeCounter,
    IndexI5,
    IndexI7,
    IndexPair,
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
            self.assertIn("comment_input", record)
            self.assertIn("organism_name", record)
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

    def test_add_library_rejects_name_ending_with_special_character(self):
        """Ensure add library rejects names ending with special characters."""
        response = self.client.post(
            reverse("libraries-list"),
            {
                "data": json.dumps(
                    [
                        {
                            "name": "260429_04_SM_CnT_T180_utx1_H3K27me3_rep1_",
                            "organism": self.library.organism.pk,
                            "measured_value": 1.0,
                            "read_length": self.library.read_length.pk,
                            "sequencing_depth": 1,
                            "library_protocol": self.library.library_protocol.pk,
                            "library_type": self.library.library_type.pk,
                            "index_type": self.library.index_type.pk,
                            "index_reads": 0,
                            "mean_fragment_size": 1,
                        }
                    ]
                )
            },
        )
        data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "Invalid payload.")

    def test_update_library_rejects_name_ending_with_special_character(self):
        """Ensure update library rejects names ending with special characters."""
        library = create_library(self._get_random_name())

        response = self.client.post(
            reverse("libraries-edit"),
            {
                "data": json.dumps(
                    [
                        {
                            "pk": library.pk,
                            "name": "260429_04_SM_CnT_T180_utx1_H3K27me3_rep1_",
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
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "Invalid payload.")
        self.assertEqual(Library.objects.get(pk=library.pk).name, library.name)

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

    def _comment_names(self, entry, payload=None):
        return {
            prop.get("name")
            for property_name in ("additionalProperty", "parameterValue")
            for prop in self._property_entries(entry, payload, property_name)
            if isinstance(prop, dict) and prop.get("name")
        }

    def _property_entries(
        self, entry, payload=None, property_name="additionalProperty"
    ):
        properties = entry.get(property_name, [])
        if isinstance(properties, dict):
            properties = [properties]
        resolved_properties = []
        for prop in properties:
            if not isinstance(prop, dict):
                continue
            prop_id = prop.get("@id")
            if prop_id and payload:
                resolved = self._graph_entry(payload, prop_id)
                if resolved:
                    resolved_properties.append(resolved)
                    continue
            resolved_properties.append(prop)
        return resolved_properties

    def _extract_zip_payload(self, response):
        self.assertEqual(response["Content-Type"], "application/zip")
        zip_buffer = BytesIO(response.content)
        with ZipFile(zip_buffer, "r") as zip_file:
            payload = json.loads(
                zip_file.read("ro-crate-metadata.json").decode("utf-8")
            )
            archive_names = set(zip_file.namelist())
        return payload, archive_names

    def _set_ro_crate_complete_data_rows(
        self, mock_library_objects, mock_sample_objects, libraries=None, samples=None
    ):
        mock_library_objects.filter.return_value = _MockQuerySet(libraries or [])
        mock_sample_objects.filter.return_value = _MockQuerySet(samples or [])

    def _extract_preview_payload(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "no-store")
        payload = self._parse_payload(response)
        self.assertIn("ro_crate", payload)
        self.assertIn("@graph", payload["ro_crate"])
        return payload

    def _assert_pdf_response(self, response, filename):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertIn(filename, response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF"))

    def _pdf_renderer_for_graph(self, graph):
        return ROCratePdfRenderer(
            {"@context": ["https://w3id.org/ro/crate/1.1/context"], "@graph": graph},
            "test_ro_crate.zip",
        )

    def _graph_ids(self, payload):
        return {entry.get("@id") for entry in payload["@graph"]}

    def _additional_type_ids(self, entry):
        values = entry.get("additionalType", [])
        if isinstance(values, dict):
            values = [values]
        return {
            value.get("@id")
            for value in values
            if isinstance(value, dict) and value.get("@id")
        }

    def _additional_type_values(self, entry):
        values = entry.get("additionalType", [])
        if isinstance(values, dict):
            values = [values]
        elif not isinstance(values, list):
            values = [values]
        return values

    def _assert_comment_names_include(self, entry, names, payload=None):
        comment_names = self._comment_names(entry, payload)
        for name in names:
            self.assertIn(name, comment_names)

    def _assert_comment_names_exclude(self, entry, names, payload=None):
        comment_names = self._comment_names(entry, payload)
        for name in names:
            self.assertNotIn(name, comment_names)

    def _comment_value(self, entry, name, payload=None):
        for property_name in ("additionalProperty", "parameterValue"):
            for prop in self._property_entries(entry, payload, property_name):
                if isinstance(prop, dict) and prop.get("name") == name:
                    return prop.get("value")
        return None

    def _sample_view_row(self, sample, **overrides):
        data = {
            "sample_id": sample.pk,
            "barcode": sample.barcode,
            "name": sample.name,
            "status": sample.status,
            "sequencing_depth": sample.sequencing_depth,
            "nucleic_acid_type_id": sample.nucleic_acid_type_id,
            "nucleic_acid_type_name": sample.nucleic_acid_type.name,
            "measuring_unit": sample.measuring_unit or "",
            "measured_value": sample.measured_value or 0,
            "measuring_unit_facility": sample.measuring_unit_facility or "",
            "measured_value_facility": sample.measured_value_facility or 0,
            "concentration_library": 1.5,
            "gmo": False,
            "library_protocol_id": sample.library_protocol_id,
            "library_protocol_name": sample.library_protocol.name,
            "analysis_type_id": 1,
            "analysis_type_name": "RNA-seq",
            "read_length_id": sample.read_length_id,
            "read_length_name": sample.read_length.name,
            "average_fragment_size": 250.0,
            "starting_amount": 5.0,
            "pcr_cycles": 8,
            "index_type_name": sample.index_type.name if sample.index_type else None,
            "coordinate": "A1",
            "index_i7": "ACGT",
            "i7_id": "IDX7",
            "index_i5": "TGCA",
            "i5_id": "IDX5",
            "request_id": self.request.id,
            "request_name": self.request.name,
            "create_time": self.request.create_time,
            "pool_names": ["Pool1"],
            "flowcell_ids": ["FC1"],
            "sequencer_ids": [1],
            "sequencer_names": ["Seq1"],
        }
        data.update(overrides)
        return CompleteSampleData(**data)

    def _library_view_row(self, library, **overrides):
        data = {
            "library_id": library.pk,
            "barcode": library.barcode,
            "name": library.name,
            "status": library.status,
            "sequencing_depth": library.sequencing_depth,
            "measuring_unit": library.measuring_unit or "",
            "measured_value": library.measured_value or 0,
            "measuring_unit_facility": library.measuring_unit_facility or "",
            "measured_value_facility": library.measured_value_facility or 0,
            "concentration_library": 2.5,
            "percent_total": library.percent_total,
            "library_protocol_id": library.library_protocol_id,
            "library_protocol_name": library.library_protocol.name,
            "analysis_type_id": 2,
            "analysis_type_name": "WGS",
            "read_length_id": library.read_length_id,
            "read_length_name": library.read_length.name,
            "average_fragment_size": 300.0,
            "index_type_name": library.index_type.name if library.index_type else None,
            "coordinate": "B2",
            "index_i7": "AAAA",
            "i7_id": "LIDX7",
            "index_i5": "CCCC",
            "i5_id": "LIDX5",
            "request_id": self.request.id,
            "request_name": self.request.name,
            "create_time": self.request.create_time,
            "pool_names": ["PoolA"],
            "flowcell_ids": ["FC9"],
            "sequencer_ids": [9],
            "sequencer_names": ["NovaSeq"],
        }
        data.update(overrides)
        return CompleteLibraryData(**data)

    def test_requires_identifier_parameters(self):
        """Request must provide barcodes or request names."""
        response = self.client.get(reverse("generate-ro-crate-list"))
        self.assertEqual(response.status_code, 400)
        payload = self._parse_payload(response)
        self.assertIn("error", payload)

    def test_rejects_unknown_boolean_export_flag_values(self):
        for query_name in ("preview", "pdf"):
            with self.subTest(query_name=query_name):
                response = self.client.get(
                    reverse("generate-ro-crate-list"),
                    {"requests": self.request.name, query_name: "yes"},
                )
                self.assertEqual(response.status_code, 400)
                payload = self._parse_payload(response)
                self.assertIn(query_name, payload["error"])

    @patch("library.ro_crate.CompleteSampleData.objects")
    @patch("library.ro_crate.CompleteLibraryData.objects")
    def test_legacy_sections_parameter_is_ignored(
        self, mock_library_objects, mock_sample_objects
    ):
        sample = create_sample("all-sections-sample", status=6)
        self.request.samples.add(sample)
        self._set_ro_crate_complete_data_rows(
            mock_library_objects,
            mock_sample_objects,
            samples=[self._sample_view_row(sample)],
        )

        response = self.client.get(
            reverse("generate-ro-crate-list"),
            {"barcodes": sample.barcode, "sections": "samples"},
        )

        self.assertEqual(response.status_code, 200)
        payload, _ = self._extract_zip_payload(response)
        graph_ids = self._graph_ids(payload)
        self.assertIn(f"#sample-material-{sample.pk}", graph_ids)
        self.assertIn(f"#protocol-{sample.library_protocol_id}", graph_ids)
        self.assertIn(f"#organism-{sample.organism_id}", graph_ids)
        self.assertIn(f"#index-type-{sample.index_type_id}", graph_ids)

    @patch("library.ro_crate.CompleteSampleData.objects")
    @patch("library.ro_crate.CompleteLibraryData.objects")
    def test_returns_placeholder_when_no_matches(
        self, mock_library_objects, mock_sample_objects
    ):
        """Unknown identifiers should return an empty crate with a helpful message."""
        self._set_ro_crate_complete_data_rows(mock_library_objects, mock_sample_objects)

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
    def test_request_name_export_returns_zip_with_root_dataset_and_isa_profile(
        self, mock_library_objects, mock_sample_objects
    ):
        """Exporting by request name should yield a structured RO-Crate."""
        self._set_ro_crate_complete_data_rows(mock_library_objects, mock_sample_objects)

        response = self.client.get(
            reverse("generate-ro-crate-list"), {"requests": self.request.name}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            f"{self.request.pk}_ro_crate.zip",
            response["Content-Disposition"],
        )
        payload, archive_names = self._extract_zip_payload(response)
        self.assertIn("@graph", payload)
        self.assertIn("ro-crate-metadata.json", archive_names)
        pdf_name = "ro-crate-preview.pdf"
        self.assertIn(pdf_name, archive_names)
        with ZipFile(BytesIO(response.content), "r") as zip_file:
            self.assertTrue(zip_file.read(pdf_name).startswith(b"%PDF"))

        graph_ids = self._graph_ids(payload)
        self.assertIn("./", graph_ids)
        self.assertIn(f"#study-{self.request.id}", graph_ids)
        self.assertFalse(any("comments" in entry for entry in payload["@graph"]))

        dataset_entry = next(
            (entry for entry in payload["@graph"] if entry.get("@id") == "./"), {}
        )
        self.assertEqual(dataset_entry.get("name"), self.request.name)
        self.assertIn(
            "https://w3id.org/isa/Investigation",
            self._additional_type_ids(dataset_entry),
        )
        self.assertIn("Investigation", self._additional_type_values(dataset_entry))
        self.assertIn(
            {"@id": "https://w3id.org/ro/crate/1.1"},
            dataset_entry.get("conformsTo", []),
        )
        self.assertIn(
            {"@id": f"#study-{self.request.id}"},
            dataset_entry.get("hasPart", []),
        )
        self.assertEqual(dataset_entry.get("creator"), {"@id": "#parkour-software"})
        self.assertEqual(
            dataset_entry.get("publisher"), {"@id": "#parkour-organization"}
        )
        self.assertIn(
            "https://github.com/nfdi4plants/isa-ro-crate-profile/tree/release/profile",
            graph_ids,
        )
        self.assertNotIn(f"#person-{self.user.id}", graph_ids)
        self.assertNotIn("#role-request-submitter", graph_ids)
        self.assertFalse(
            any(str(entity_id).startswith("#organization-") for entity_id in graph_ids)
        )
        self.assertFalse(
            any(
                str(entity_id).startswith("#principal-investigator-")
                for entity_id in graph_ids
            )
        )
        self.assertFalse(
            any(str(entity_id).startswith("#cost-unit-") for entity_id in graph_ids)
        )
        self.assertIn("#ro-crate-export-action", graph_ids)

    @patch("library.ro_crate.CompleteSampleData.objects")
    @patch("library.ro_crate.CompleteLibraryData.objects")
    def test_request_path_metadata_preserves_optional_md5_without_packaging_paths(
        self, mock_library_objects, mock_sample_objects
    ):
        self.request.filepaths = {
            "data": {
                "path": "/data/project/huge.fastq.gz",
                "md5": "d41d8cd98f00b204e9800998ecf8427e",
                "contentUrl": "/ignored/alias.fastq.gz",
                "extra": "ignored",
            },
            "metadata": "/data/project/report.html",
            "legacy_alias": {
                "filepath": "/data/project/legacy.fastq.gz",
                "MD5": "0cc175b9c0f1b6a831c399e269772662",
            },
        }
        self.request.metapaths = {
            "analysis": {
                "path": "/data/project/analysis.tsv",
                "md5": "0cc175b9c0f1b6a831c399e269772661",
            }
        }
        self.request.save(update_fields=["filepaths", "metapaths"])
        self._set_ro_crate_complete_data_rows(mock_library_objects, mock_sample_objects)

        response = self.client.get(
            reverse("generate-ro-crate-list"), {"requests": self.request.name}
        )
        self.assertEqual(response.status_code, 200)
        payload, archive_names = self._extract_zip_payload(response)

        dataset_entry = self._graph_entry(payload, "./")
        filepaths = json.loads(
            self._comment_value(dataset_entry, "request_filepaths", payload)
        )
        metapaths = json.loads(
            self._comment_value(dataset_entry, "request_metapaths", payload)
        )

        self.assertEqual(filepaths["data"]["md5"], "d41d8cd98f00b204e9800998ecf8427e")
        self.assertEqual(
            filepaths["data"],
            {
                "path": "/data/project/huge.fastq.gz",
                "md5": "d41d8cd98f00b204e9800998ecf8427e",
            },
        )
        self.assertEqual(filepaths["metadata"], "/data/project/report.html")
        self.assertNotIn("legacy_alias", filepaths)
        self.assertEqual(
            metapaths["analysis"]["md5"], "0cc175b9c0f1b6a831c399e269772661"
        )
        self.assertNotIn("data/project/huge.fastq.gz", archive_names)
        self.assertEqual(
            archive_names,
            {"ro-crate-metadata.json", "ro-crate-preview.pdf"},
        )

    @patch("library.ro_crate.CompleteSampleData.objects")
    @patch("library.ro_crate.CompleteLibraryData.objects")
    def test_sample_barcode_export_includes_sample_relationships_metadata_and_attachments(
        self, mock_library_objects, mock_sample_objects
    ):
        self.request.name = f"{self.request.id}_Kim_Denboba"
        self.request.save(update_fields=["name"])
        sample = create_sample("crate-sample", status=6)
        sample.removed_amplification_cycles = 11
        sample.removed_equal_representation_nucleotides = True
        sample.removed_rna_quality = 7.3
        sample.save()
        self.request.samples.add(sample)
        request_file = FileRequest.objects.create(
            name="req.txt",
            file_type="Experimental_Design",
        )
        request_file.file.save("req.txt", ContentFile(b"ro-crate test file"), save=True)
        self.request.files.add(request_file)
        LibraryPreparation.objects.create(
            sample=sample,
            starting_amount=12.5,
            pcr_cycles=9,
            concentration_library=3.2,
            mean_fragment_size=280,
        )
        Pooling.objects.create(
            sample=sample, concentration_c1=4.4, comment="sample pool"
        )

        self._set_ro_crate_complete_data_rows(
            mock_library_objects,
            mock_sample_objects,
            samples=[self._sample_view_row(sample)],
        )

        response = self.client.get(
            reverse("generate-ro-crate-list"), {"barcodes": sample.barcode}
        )
        self.assertEqual(response.status_code, 200)
        payload, archive_names = self._extract_zip_payload(response)

        sample_entry = self._graph_entry(payload, f"#sample-material-{sample.pk}")
        self.assertEqual(sample_entry.get("identifier"), sample.barcode)
        self.assertIn(
            {"@id": f"#source-sample-{sample.pk}"},
            sample_entry.get("derivedFrom", []),
        )
        self._assert_comment_names_include(
            sample_entry,
            [
                "sample_db_name",
                "sample_db_barcode",
                "sample_db_amplification_cycles",
                "sample_db_equal_representation_nucleotides",
                "sample_db_rna_quality",
                "library_preparation_starting_amount",
            ],
            payload,
        )
        self._assert_comment_names_exclude(
            sample_entry,
            [
                "sample_db_removed_amplification_cycles",
                "sample_db_removed_equal_representation_nucleotides",
                "sample_db_removed_rna_quality",
                "sample_mv_analysis_type_name",
                "sample_mv_create_time",
                "sample_mv_pool_names",
                "sample_mv_sequencer_names",
                "sample_mv_flowcell_ids",
                "sample_mv_starting_amount",
                "sample_mv_pcr_cycles",
            ],
            payload,
        )
        self.assertEqual(
            sample_entry.get("nucleicAcidType"),
            {"@id": f"#nucleic-acid-type-{sample.nucleic_acid_type_id}"},
        )
        nucleic_acid_type_entry = self._graph_entry(
            payload, f"#nucleic-acid-type-{sample.nucleic_acid_type_id}"
        )
        self._assert_comment_names_exclude(
            nucleic_acid_type_entry,
            ["nucleic_acid_type_type"],
            payload,
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
        self._assert_comment_names_include(
            process_entry,
            [
                "sample_mv_analysis_type_name",
                "sample_mv_pool_names",
                "sample_mv_sequencer_names",
                "sample_mv_flowcell_ids",
                "sample_mv_starting_amount",
                "sample_mv_pcr_cycles",
            ],
            payload,
        )
        self.assertEqual(
            process_entry.get("executesLabProtocol"),
            {"@id": f"#protocol-{sample.library_protocol_id}"},
        )
        request_file_entity_id = next(
            (
                entry.get("@id")
                for entry in payload["@graph"]
                if entry.get("identifier")
                == f"urn:parkour:request-file:{request_file.pk}"
            ),
            None,
        )
        self.assertIsNotNone(request_file_entity_id)
        request_file_entry = self._graph_entry(payload, request_file_entity_id)
        self.assertIn("MediaObject", request_file_entry.get("@type", []))
        self.assertEqual(
            request_file_entry.get("fileType"),
            "Experimental_Design",
        )
        self.assertEqual(
            request_file_entry.get("isPartOf"),
            {"@id": "./"},
        )
        self.assertTrue(
            request_file_entry.get("contentUrl", "").startswith(
                f"request-files/{self.request.id}_Kim_Denboba/"
            )
        )
        self.assertNotIn(
            f"request-{self.request.id}_{self.request.id}_",
            request_file_entry.get("contentUrl", ""),
        )
        self.assertIn(request_file_entry.get("contentUrl"), archive_names)
        dataset_entry = self._graph_entry(payload, "./")
        self.assertIn(
            {"@id": request_file_entity_id},
            dataset_entry.get("hasPart", []),
        )
        study_entry = self._graph_entry(payload, f"#study-{self.request.pk}")
        self.assertIn(
            {"@id": f"#source-sample-{sample.pk}"},
            study_entry.get("materials", {}).get("sources", []),
        )
        self.assertIn(
            {"@id": f"#sample-material-{sample.pk}"},
            study_entry.get("materials", {}).get("samples", []),
        )
        self.assertIn(
            {"@id": f"#sample-assay-{sample.pk}"},
            study_entry.get("assays", []),
        )
        self.assertIn(
            {"@id": f"#sample-process-{sample.pk}"},
            study_entry.get("processSequence", []),
        )
        self.assertIn(
            {"@id": f"#sample-data-{sample.pk}"},
            study_entry.get("dataFiles", []),
        )

    @patch("library.ro_crate.CompleteSampleData.objects")
    @patch("library.ro_crate.CompleteLibraryData.objects")
    def test_multi_request_export_creates_one_isa_study_per_request(
        self, mock_library_objects, mock_sample_objects
    ):
        other_request = Request.objects.create(user=self.user)
        other_request.refresh_from_db()
        self._set_ro_crate_complete_data_rows(mock_library_objects, mock_sample_objects)

        response = self.client.get(
            reverse("generate-ro-crate-list"),
            {"requests": f"{self.request.name},{other_request.name}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            f"{self.request.pk}_{other_request.pk}_ro_crate.zip",
            response["Content-Disposition"],
        )
        payload, archive_names = self._extract_zip_payload(response)
        self.assertIn("ro-crate-metadata.json", archive_names)
        dataset_entry = self._graph_entry(payload, "./")
        self.assertIn("2 requests", dataset_entry.get("name", ""))
        self.assertIn(
            {"@id": f"#study-{self.request.pk}"},
            dataset_entry.get("hasPart", []),
        )
        self.assertIn(
            {"@id": f"#study-{other_request.pk}"},
            dataset_entry.get("hasPart", []),
        )
        self.assertIn(
            {"@id": f"#request-context-{self.request.pk}"},
            dataset_entry.get("hasPart", []),
        )
        self.assertIn(
            {"@id": f"#request-context-{other_request.pk}"},
            dataset_entry.get("hasPart", []),
        )
        first_study = self._graph_entry(payload, f"#study-{self.request.pk}")
        second_study = self._graph_entry(payload, f"#study-{other_request.pk}")
        self.assertIn(
            "https://w3id.org/isa/Study",
            self._additional_type_ids(first_study),
        )
        self.assertIn(
            "https://w3id.org/isa/Study",
            self._additional_type_ids(second_study),
        )

    @patch("library.ro_crate.CompleteSampleData.objects")
    @patch("library.ro_crate.CompleteLibraryData.objects")
    def test_barcode_export_counts_related_record_request_memberships(
        self, mock_library_objects, mock_sample_objects
    ):
        other_request = Request.objects.create(user=self.user)
        other_request.refresh_from_db()
        library = create_library("shared-request-library", status=6)
        self.request.libraries.add(library)
        other_request.libraries.add(library)
        self._set_ro_crate_complete_data_rows(
            mock_library_objects,
            mock_sample_objects,
            libraries=[self._library_view_row(library)],
        )

        response = self.client.get(
            reverse("generate-ro-crate-list"), {"barcodes": library.barcode}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            f"{self.request.pk}_{other_request.pk}_ro_crate.zip",
            response["Content-Disposition"],
        )
        payload, _ = self._extract_zip_payload(response)

        dataset_entry = self._graph_entry(payload, "./")
        library_entry = self._graph_entry(payload, f"#library-material-{library.pk}")
        self.assertIn("2 requests", dataset_entry.get("name", ""))
        self.assertIn(
            {"@id": f"#request-context-{self.request.pk}"},
            library_entry.get("requestContext", []),
        )
        self.assertIn(
            {"@id": f"#request-context-{other_request.pk}"},
            library_entry.get("requestContext", []),
        )
        self.assertIn(
            {"@id": f"#study-{other_request.pk}"},
            dataset_entry.get("hasPart", []),
        )

    @patch("library.ro_crate.CompleteSampleData.objects")
    @patch("library.ro_crate.CompleteLibraryData.objects")
    def test_preview_mode_returns_json_payload_and_disables_cache(
        self, mock_library_objects, mock_sample_objects
    ):
        self._set_ro_crate_complete_data_rows(mock_library_objects, mock_sample_objects)

        response = self.client.get(
            reverse("generate-ro-crate-list"),
            {"requests": self.request.name, "preview": "true"},
        )
        self._extract_preview_payload(response)

    @patch("library.ro_crate.CompleteSampleData.objects")
    @patch("library.ro_crate.CompleteLibraryData.objects")
    def test_pdf_mode_returns_pdf_attachment_and_disables_cache(
        self, mock_library_objects, mock_sample_objects
    ):
        self._set_ro_crate_complete_data_rows(mock_library_objects, mock_sample_objects)

        response = self.client.get(
            reverse("generate-ro-crate-list"),
            {"requests": self.request.name, "pdf": "true"},
        )

        self._assert_pdf_response(
            response,
            f"{self.request.pk}_ro_crate_preview.pdf",
        )

    def test_pdf_preview_uses_formatted_preparation_and_sequencing_sections(self):
        graph = [
            {
                "@id": "#library-material-501",
                "@type": "Thing",
                "name": "Preview library",
                "identifier": "26L000501",
            },
            {
                "@id": "#library-process-501",
                "@type": "CreateAction",
                "object": [{"@id": "#library-material-501"}],
                "parameterValue": [
                    {"@id": "#library-input-value"},
                    {"@id": "#library-input-unit"},
                    {"@id": "#library-concentration"},
                    {"@id": "#library-depth"},
                ],
            },
            {
                "@id": "#library-input-value",
                "@type": "PropertyValue",
                "name": "library_mv_measured_value",
                "value": 2,
            },
            {
                "@id": "#library-input-unit",
                "@type": "PropertyValue",
                "name": "library_mv_measuring_unit",
                "value": "ng/µl",
            },
            {
                "@id": "#library-concentration",
                "@type": "PropertyValue",
                "name": "library_mv_concentration_library",
                "value": 1.5,
            },
            {
                "@id": "#library-depth",
                "@type": "PropertyValue",
                "name": "library_mv_sequencing_depth",
                "value": 24.6,
            },
        ]
        renderer = self._pdf_renderer_for_graph(graph)

        record = renderer._build_record("#library-material-501")
        sections = {section["title"]: section["rows"] for section in record["sections"]}
        preparation = {row["key"]: row["value"] for row in sections["Preparation"]}
        sequencing = {row["key"]: row["value"] for row in sections["Sequencing"]}

        self.assertEqual(set(sections), {"Preparation", "Sequencing"})
        self.assertEqual(
            list(preparation)[:3],
            ["Name", "Barcode", "Plate Coord"],
        )
        self.assertNotIn("Status", preparation)
        self.assertNotIn("S/L", preparation)
        self.assertEqual(preparation["Input"], "2 ng/µl")
        self.assertEqual(preparation["ng/µl Library"], "1.500")
        self.assertEqual(sequencing["Depth (M)"], "25")
        self.assertEqual(renderer._input_card_value(-1, "Unknown"), "Unknown")
        self.assertEqual(
            renderer._formatted_barcode("26L000502", "Sample"),
            "26L000502*",
        )
        self.assertEqual(
            renderer._formatted_barcode("26L000501", "Library"),
            "26L000501",
        )
        self.assertEqual(renderer._fixed_card_number(1.25, 1), "1.3")
        self.assertEqual(
            renderer._date_card_value("2026-01-30T23:30:00-05:00"),
            "30.01.2026",
        )
        self.assertTrue(renderer.render().startswith(b"%PDF"))
        self.assertEqual(len(renderer.pdf.links), 1)
        self.assertGreaterEqual(
            sum(len(page.annots) for page in renderer.pdf.pages.values()),
            1,
        )

    def test_pdf_request_details_use_preview_allowlist(self):
        graph = [
            {
                "@id": "#request-context-101",
                "@type": "Dataset",
                "name": "Preview request",
                "description": "Request description",
                "additionalProperty": [
                    {"@id": "#request-filepaths"},
                    {"@id": "#request-metapaths"},
                    {"@id": "#request-qc-completed-at"},
                ],
            },
            {
                "@id": "#request-filepaths",
                "@type": "PropertyValue",
                "name": "request_filepaths",
                "value": {"data": "/data/request"},
            },
            {
                "@id": "#request-metapaths",
                "@type": "PropertyValue",
                "name": "request_metapaths",
                "value": {"metadata": "/data/request/metadata"},
            },
            {
                "@id": "#request-qc-completed-at",
                "@type": "PropertyValue",
                "name": "request_qc_completed_at",
                "value": "2026-04-02T12:00:00Z",
            },
        ]
        renderer = self._pdf_renderer_for_graph(graph)

        rows = renderer.request_detail_rows(
            renderer.entity_by_id("#request-context-101")
        )

        self.assertEqual(
            [row["key"] for row in rows],
            [
                "Name",
                "Description",
                "External File Paths",
                "External Metadata Paths",
            ],
        )

    def test_export_filenames_are_limited_to_50_characters(self):
        archive_name = _ro_crate_archive_name(
            "101_102_103_104_105_106_107_108_109_110_111_112"
        )
        pdf_name = _ro_crate_pdf_name(archive_name)

        self.assertLessEqual(len(archive_name), 50)
        self.assertLessEqual(len(pdf_name), 50)
        self.assertTrue(archive_name.endswith(".zip"))
        self.assertTrue(pdf_name.endswith("_ro_crate_preview.pdf"))

    @patch("library.ro_crate.CompleteSampleData.objects")
    @patch("library.ro_crate.CompleteLibraryData.objects")
    def test_rejects_selection_when_no_selected_record_is_exportable(
        self, mock_library_objects, mock_sample_objects
    ):
        library = create_library("crate-library", status=4)
        self.request.libraries.add(library)
        self._set_ro_crate_complete_data_rows(
            mock_library_objects,
            mock_sample_objects,
            libraries=[self._library_view_row(library)],
        )

        response = self.client.get(
            reverse("generate-ro-crate-list"), {"barcodes": library.barcode}
        )
        self.assertEqual(response.status_code, 400)
        payload = self._parse_payload(response)
        self.assertIn("Sequencing or Delivered status", payload.get("error", ""))
        self.assertEqual(payload["skipped_records"], [library.barcode])

    @patch("library.ro_crate.CompleteSampleData.objects")
    @patch("library.ro_crate.CompleteLibraryData.objects")
    def test_sequencing_records_are_exported_while_other_status_is_skipped(
        self, mock_library_objects, mock_sample_objects
    ):
        sequencing_library = create_library("sequencing-crate-library", status=5)
        pooled_library = create_library("pooled-crate-library", status=4)
        sequencing_sample = create_sample("sequencing-crate-sample", status=5)
        self.request.libraries.add(sequencing_library, pooled_library)
        self.request.samples.add(sequencing_sample)
        self._set_ro_crate_complete_data_rows(
            mock_library_objects,
            mock_sample_objects,
            libraries=[
                self._library_view_row(sequencing_library),
                self._library_view_row(pooled_library),
            ],
            samples=[self._sample_view_row(sequencing_sample)],
        )

        response = self.client.get(
            reverse("generate-ro-crate-list"),
            {
                "barcodes": (
                    f"{sequencing_library.barcode},{pooled_library.barcode},"
                    f"{sequencing_sample.barcode}"
                ),
                "preview": "true",
            },
        )
        payload = self._extract_preview_payload(response)
        self.assertEqual(payload["skipped_records"], [pooled_library.barcode])
        graph_ids = self._graph_ids(payload["ro_crate"])
        self.assertIn(f"#library-material-{sequencing_library.pk}", graph_ids)
        self.assertNotIn(f"#library-material-{pooled_library.pk}", graph_ids)
        self.assertIn(f"#sample-material-{sequencing_sample.pk}", graph_ids)

    @patch("library.ro_crate.CompleteSampleData.objects")
    @patch("library.ro_crate.CompleteLibraryData.objects")
    def test_library_barcode_export_includes_library_relationships_and_hides_non_export_fields(
        self, mock_library_objects, mock_sample_objects
    ):
        library = create_library("crate-library", status=6)
        library.removed_amplification_cycles = 6
        library.removed_equal_representation_nucleotides = True
        library.removed_qpcr_result = 1.2
        library.removed_qpcr_result_facility = 2.4
        index_i7 = IndexI7.objects.create(prefix="IDX", number="7", index="AAAA")
        index_i5 = IndexI5.objects.create(prefix="IDX", number="5", index="CCCC")
        library.index_type.indices_i7.add(index_i7)
        library.index_type.indices_i5.add(index_i5)
        index_pair = IndexPair.objects.create(
            index_type=library.index_type,
            index1=index_i7,
            index2=index_i5,
            char_coord="B",
            num_coord=2,
        )
        library.index_i7 = index_i7.index
        library.index_i5 = index_i5.index
        library.save()
        self.request.libraries.add(library)
        Pooling.objects.create(
            library=library, concentration_c1=6.6, comment="library pool"
        )
        pool_size = PoolSize.objects.create(multiplier=1, size=400)
        pool = Pool.objects.create(user=self.user, size=pool_size)
        pool.libraries.add(library)
        lane = Lane.objects.create(
            name="L1",
            pool=pool,
            loading_concentration=1.8,
            phix=2.5,
            completed=True,
        )
        sequencer = Sequencer.objects.create(
            name="NovaSeq 6000", lanes=2, lane_capacity=400
        )
        flowcell = Flowcell.objects.create(
            flowcell_id="FC_RO_CRATE",
            sequencer=sequencer,
            matrix={"lane": "L1", "library": library.barcode},
            sequences={"read1": "ACGT", "read2": "TGCA"},
        )
        flowcell.lanes.add(lane)
        flowcell.requests.add(self.request)

        self._set_ro_crate_complete_data_rows(
            mock_library_objects,
            mock_sample_objects,
            libraries=[self._library_view_row(library)],
        )

        response = self.client.get(
            reverse("generate-ro-crate-list"), {"barcodes": library.barcode}
        )
        self.assertEqual(response.status_code, 200)
        payload, _ = self._extract_zip_payload(response)

        library_entry = self._graph_entry(payload, f"#library-material-{library.pk}")
        self.assertEqual(library_entry.get("identifier"), library.barcode)
        self._assert_comment_names_include(
            library_entry,
            [
                "library_db_name",
                "library_db_amplification_cycles",
                "library_db_equal_representation_nucleotides",
                "library_db_qpcr_result",
                "library_db_qpcr_result_facility",
            ],
            payload,
        )
        self._assert_comment_names_exclude(
            library_entry,
            [
                "library_db_removed_amplification_cycles",
                "library_db_removed_equal_representation_nucleotides",
                "library_db_removed_qpcr_result",
                "library_db_removed_qpcr_result_facility",
                "pooling_comment",
                "pooling_library",
            ],
            payload,
        )
        self.assertEqual(
            self._comment_value(library_entry, "library_db_library_protocol", payload),
            library.library_protocol.name,
        )
        self.assertEqual(
            self._comment_value(library_entry, "library_db_library_type", payload),
            library.library_type.name,
        )
        self.assertEqual(
            self._comment_value(library_entry, "library_db_organism", payload),
            library.organism.name,
        )
        self.assertEqual(
            self._comment_value(library_entry, "library_db_read_length", payload),
            library.read_length.name,
        )
        self.assertEqual(
            self._comment_value(library_entry, "library_db_index_type", payload),
            library.index_type.name,
        )
        self.assertEqual(
            self._comment_value(library_entry, "library_db_index_i7_id", payload),
            index_i7.index_id,
        )
        self.assertEqual(
            self._comment_value(library_entry, "library_db_index_i5_id", payload),
            index_i5.index_id,
        )
        self.assertEqual(
            library_entry.get("indexI7"), {"@id": f"#index-i7-{index_i7.id}"}
        )
        self.assertEqual(
            library_entry.get("indexI5"), {"@id": f"#index-i5-{index_i5.id}"}
        )
        self.assertEqual(
            library_entry.get("selectedIndexPair"),
            {"@id": f"#index-pair-{index_pair.id}"},
        )
        self.assertEqual(
            library_entry.get("sequencedOn"),
            [{"@id": f"#flowcell-assay-{flowcell.id}"}],
        )

        library_type_entry = self._graph_entry(
            payload, f"#library-type-{library.library_type_id}"
        )
        self.assertIn(
            {"@id": f"#protocol-{library.library_protocol_id}"},
            library_type_entry.get("availableProtocols", []),
        )
        index_type_entry = self._graph_entry(
            payload, f"#index-type-{library.index_type_id}"
        )
        self.assertNotIn("indicesI7", index_type_entry)
        self.assertNotIn("indicesI5", index_type_entry)
        index_pair_entry = self._graph_entry(payload, f"#index-pair-{index_pair.id}")
        self.assertEqual(index_pair_entry.get("coordinate"), "B2")
        flowcell_entry = self._graph_entry(payload, f"#flowcell-assay-{flowcell.id}")
        self.assertEqual(
            flowcell_entry.get("hasInstrument"), {"@id": f"#sequencer-{sequencer.id}"}
        )
        self.assertIn({"@id": f"#lane-{lane.id}"}, flowcell_entry.get("hasLane", []))
        self.assertIn(
            {"@id": f"#flowcell-matrix-data-{flowcell.id}"},
            flowcell_entry.get("hasPart", []),
        )
        self.assertIn(
            {"@id": f"#flowcell-sequences-data-{flowcell.id}"},
            flowcell_entry.get("hasPart", []),
        )
        flowcell_data_entry = self._graph_entry(
            payload, f"#flowcell-data-{flowcell.id}"
        )
        self._assert_comment_names_exclude(
            flowcell_data_entry,
            ["flowcell_matrix", "flowcell_sequences"],
            payload,
        )
        sequencer_entry = self._graph_entry(payload, f"#sequencer-{sequencer.id}")
        self.assertEqual(
            self._comment_value(sequencer_entry, "sequencer_lane_capacity", payload),
            sequencer.lane_capacity,
        )
        lane_entry = self._graph_entry(payload, f"#lane-{lane.id}")
        self.assertEqual(
            self._comment_value(lane_entry, "lane_loading_concentration", payload),
            lane.loading_concentration,
        )
        matrix_entry = self._graph_entry(
            payload, f"#flowcell-matrix-data-{flowcell.id}"
        )
        self.assertIn(
            library.barcode,
            self._comment_value(matrix_entry, "flowcell_matrix", payload),
        )
        sequences_entry = self._graph_entry(
            payload, f"#flowcell-sequences-data-{flowcell.id}"
        )
        self.assertIn(
            "ACGT",
            self._comment_value(sequences_entry, "flowcell_sequences", payload),
        )

        process_entry = self._graph_entry(payload, f"#library-process-{library.pk}")
        self._assert_comment_names_include(
            process_entry,
            [
                "library_mv_analysis_type_name",
                "library_mv_create_time",
                "library_mv_pool_names",
                "library_mv_flowcell_ids",
                "library_mv_sequencer_names",
                "library_mv_percent_total",
                "library_mv_coordinate",
                "library_mv_i7_id",
                "library_mv_i5_id",
            ],
            payload,
        )
        self._assert_comment_names_exclude(
            process_entry, ["library_mv_status"], payload
        )
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
