from common.tests import BaseTestCase
from common.utils import get_random_name
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import (
    BarcodeCounter,
    ConcentrationMethod,
    GenericIndex,
    GenericLibrarySample,
    IndexI5,
    IndexI7,
    IndexPair,
    IndexType,
    LibraryProtocol,
    AnalysisType,
    Organism,
    ReadLength,
)

User = get_user_model()


def create_read_length(name):
    read_length = ReadLength(name=name)
    read_length.save()
    return read_length


def create_library_protocol(name, type="DNA"):
    library_protocol = LibraryProtocol(
        name=name,
        type=type,
        provider="-",
        catalog="-",
        explanation="-",
        input_requirements="-",
        typical_application="-",
    )
    library_protocol.save()
    return library_protocol


def _create_index_type(name, save=True, is_dual=False, format="single"):
    index_type = IndexType(name=name, is_dual=is_dual, format=format)

    if save:
        index_type.save()

    return index_type


def create_index_type(name, save=True, is_dual=False, format="single"):
    index_type = IndexType(name=name, is_dual=is_dual, format=format)

    if save:
        index_type.save()

    return index_type


# Models


class OrganismTest(TestCase):
    def setUp(self):
        self.organism = Organism(name=get_random_name())

    def test_organism_name(self):
        self.assertTrue(isinstance(self.organism, Organism))
        self.assertEqual(self.organism.__str__(), self.organism.name)


class ReadLengthTest(TestCase):
    def setUp(self):
        self.read_length = ReadLength(name=get_random_name())

    def test_read_length_name(self):
        self.assertTrue(isinstance(self.read_length, ReadLength))
        self.assertEqual(self.read_length.__str__(), self.read_length.name)


class IndexTypeTest(TestCase):
    def setUp(self):
        self.index_type = IndexType(name=get_random_name())

    def test_index_type_name(self):
        self.assertTrue(isinstance(self.index_type, IndexType))
        self.assertEqual(self.index_type.__str__(), self.index_type.name)


class GenericIndexTest(TestCase):
    def setUp(self):
        self.index1 = IndexI7(prefix="I", number="001", index="ATCACG")
        # self.index2 = GenericIndex(prefix="I", number="002", index="ATCACG")
        self.index1.save()

        self.index_type = IndexType(name="Index Type")
        self.index_type.save()
        self.index_type.indices_i7.add(self.index1)

    def test_generic_index_id(self):
        self.assertEqual(str(self.index1), self.index1.index_id)
        self.assertEqual(self.index1.type(), self.index_type.name)

    # def test_no_index_type(self):
    #     self.assertEqual(self.index2.type(), "")


class BarcodeCounterTest(TestCase):
    def setUp(self):
        counter1 = BarcodeCounter.load(2017)
        counter1.save()

        counter2 = BarcodeCounter.load()
        counter2.increment()
        counter2.save()

    def test_increment(self):
        counter1 = BarcodeCounter.load(2017)
        counter2 = BarcodeCounter.load()

        self.assertEqual(counter1.last_id, 0)
        self.assertEqual(counter2.last_id, 1)

    def test_name(self):
        counter = BarcodeCounter.load()
        self.assertEqual(str(counter), str(counter.last_id))


class LibraryProtocolTest(TestCase):
    def setUp(self):
        self.library_protocol = LibraryProtocol(
            name=get_random_name(),
            provider="",
            catalog="",
            explanation="",
            input_requirements="",
            typical_application="",
        )
        self.library_protocol.save()

    def test_library_protocol_name(self):
        self.assertTrue(isinstance(self.library_protocol, LibraryProtocol))
        self.assertEqual(
            self.library_protocol.__str__(),
            self.library_protocol.name,
        )

    def test_library_protocol_in_analysis_type(self):
        """
        Ensure a new library protocol is added to the list of protocols of
        the library type 'Other'.
        """
        analysis_type = AnalysisType.objects.get(name="Other")
        library_protocols = analysis_type.library_protocol.all().values_list(
            "name", flat=True
        )
        self.assertIn(self.library_protocol.name, library_protocols)


class AnalysisTypeTest(TestCase):
    def setUp(self):
        self.analysis_type = AnalysisType(name=get_random_name())

    def test_analysis_type_name(self):
        self.assertTrue(isinstance(self.analysis_type, AnalysisType))
        self.assertEqual(self.analysis_type.__str__(), self.analysis_type.name)


# class GenericLibrarySampleTest(TestCase):
#     def setUp(self):
#         organism = Organism(name=get_random_name())
#         concentration_method = ConcentrationMethod(name=get_random_name())
#         read_length = ReadLength(name=get_random_name())
#
#         self.library = GenericLibrarySample(
#             name=get_random_name(),
#             organism=organism,
#             concentration=1.0,
#             concentration_method=concentration_method,
#             read_length=read_length,
#             sequencing_depth=1,
#         )
#
#     def test_generic_library_sample_name(self):
#         self.assertTrue(isinstance(self.library, GenericLibrarySample))
#         self.assertEqual(self.library.__str__(), self.library.name)


# Views


class TestOrganisms(BaseTestCase):
    def setUp(self):
        self.create_user("foo@bar.io", "foo-foo")
        self.client.login(email="foo@bar.io", password="foo-foo")

        self.organism = Organism(name=self._get_random_name())
        self.organism.save()

    def test_organisms_list(self):
        """Ensure get organisms behaves correctly."""
        response = self.client.get(reverse("organism-list"))
        data = response.json()
        organisms = [x["name"] for x in data]
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.organism.name, organisms)


class TestReadLengths(BaseTestCase):
    def setUp(self):
        self.create_user("foo@bar.io", "foo-foo")
        self.client.login(email="foo@bar.io", password="foo-foo")

        self.read_length = ReadLength(name=self._get_random_name())
        self.read_length.save()

    def test_organisms_list(self):
        """Ensure get read lengths behaves correctly."""
        response = self.client.get(reverse("read-length-list"))
        data = response.json()
        read_lengths = [x["name"] for x in data]
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.read_length.name, read_lengths)


class TestIndexTypes(BaseTestCase):
    def setUp(self):
        self.create_user("foo@bar.io", "foo-foo")
        self.client.login(email="foo@bar.io", password="foo-foo")

        self.index_type = IndexType(name=self._get_random_name())
        self.index_type.save()

    def test_index_type_list(self):
        """Ensure get index types behaves correctly."""
        response = self.client.get(reverse("index-type-list"))
        data = response.json()
        index_types = [x["name"] for x in data]
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.index_type.name, index_types)


class TestIndices(BaseTestCase):
    """Test indices I7 and I5."""

    def setUp(self):
        self.create_user("foo@bar.io", "foo-foo")
        self.client.login(email="foo@bar.io", password="foo-foo")

        self.index1 = IndexI7(prefix="I", number="1", index=self._get_random_name(8))
        self.index2 = IndexI7(prefix="I", number="2", index=self._get_random_name(8))
        self.index3 = IndexI5(prefix="I", number="3", index=self._get_random_name(8))
        self.index1.save()
        self.index2.save()
        self.index3.save()

        self.index_type1 = IndexType(name=self._get_random_name())
        self.index_type1.save()
        self.index_type1.indices_i7.add(self.index1)

        self.index_type2 = IndexType(name=self._get_random_name(), is_dual=True)
        self.index_type2.save()
        self.index_type2.indices_i5.add(self.index3)

    def test_indices_list(self):
        """Ensure get all indices behaves correctly."""
        response = self.client.get(reverse("index-list"))
        self.assertEqual(response.status_code, 200)
        indices = [x["index_id"] for x in response.json()]
        self.assertIn(self.index1.index_id, indices)
        self.assertIn(self.index2.index_id, indices)
        self.assertIn(self.index3.index_id, indices)

    def test_indices_i7_list(self):
        """Ensure get indices i7 behaves correctly."""
        response = self.client.get(reverse("index-i7"))
        self.assertEqual(response.status_code, 200)
        indices = [x["index_id"] for x in response.json()]
        self.assertIn(self.index1.index_id, indices)
        self.assertIn(self.index2.index_id, indices)
        self.assertNotIn(self.index3.index_id, indices)

    def test_indices_i5_list(self):
        """Ensure get indices i5 behaves correctly."""
        response = self.client.get(reverse("index-i5"))
        self.assertEqual(response.status_code, 200)
        indices = [x["index_id"] for x in response.json()]
        self.assertNotIn(self.index1.index_id, indices)
        self.assertNotIn(self.index2.index_id, indices)
        self.assertIn(self.index3.index_id, indices)

    def test_indices_i7_with_index_type(self):
        """Ensure get indices i7 given index type behaves correctly."""
        response = self.client.get(
            reverse("index-i7"),
            {
                "index_type_id": self.index_type1.pk,
            },
        )
        data = response.json()
        indices = [x["index_id"] for x in data]
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.index1.index_id, indices)
        self.assertNotIn(self.index2.index_id, indices)
        self.assertNotIn(self.index3.index_id, indices)

    def test_indices_i5_with_invalid_index_type(self):
        """
        Ensure get indices i5 given invalid index type behaves correctly.
        """
        response = self.client.get(
            reverse("index-i5"),
            {
                "index_type_id": "blah",
            },
        )
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, [])


class TestLibraryProtocols(BaseTestCase):
    """Tests for library protocols."""

    def setUp(self):
        self.create_user("foo@bar.io", "foo-foo")
        self.client.login(email="foo@bar.io", password="foo-foo")

        self.library_protocol1 = LibraryProtocol(
            name=self._get_random_name(),
            type="DNA",
            provider="-",
            catalog="-",
            explanation="-",
            input_requirements="-",
            typical_application="-",
        )
        self.library_protocol2 = LibraryProtocol(
            name=self._get_random_name(),
            type="RNA",
            provider="-",
            catalog="-",
            explanation="-",
            input_requirements="-",
            typical_application="-",
        )
        self.library_protocol1.save()
        self.library_protocol2.save()

    def test_library_protocol_list(self):
        """Ensure get library protocols behaves correctly."""
        response = self.client.get(reverse("library-protocol-list"))
        data = response.json()
        protocols = [x["name"] for x in data]
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.library_protocol1.name, protocols)
        self.assertIn(self.library_protocol2.name, protocols)

    def test_library_protocol_with_type_list(self):
        """
        Ensure get library protocols given nucleic acid type behaves correctly.
        """
        response = self.client.get(
            reverse("library-protocol-list"),
            {
                "type": "DNA",
            },
        )
        data = response.json()
        protocols = [x["name"] for x in data]
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.library_protocol1.name, protocols)
        self.assertNotIn(self.library_protocol2.name, protocols)
        self.client.get(reverse("library-protocol-list"), {type: "DNA"})


class TestAnalysisTypes(BaseTestCase):
    """Tests for library types."""

    def setUp(self):
        self.create_user("foo@bar.io", "foo-foo")
        self.client.login(email="foo@bar.io", password="foo-foo")

        self.library_protocol = LibraryProtocol(
            name=self._get_random_name(),
            type="DNA",
            provider="-",
            catalog="-",
            explanation="-",
            input_requirements="-",
            typical_application="-",
        )
        self.library_protocol.save()

        self.analysis_type = AnalysisType(name=self._get_random_name())
        self.analysis_type.save()
        self.analysis_type.library_protocol.add(self.library_protocol)

    def test_analysis_type_list(self):
        """Ensure get library types behaves correctly."""
        response = self.client.get(reverse("analysis-type-list"))
        data = response.json()
        analysis_types = [x["name"] for x in data]
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.analysis_type.name, analysis_types)

    def test_analysis_type_with_protocol_list(self):
        """
        Ensure get library types given library protocol behaves correctly.
        """
        response = self.client.get(
            reverse("analysis-type-list"),
            {
                "library_protocol_id": self.library_protocol.pk,
            },
        )
        data = response.json()
        analysis_types = [x["name"] for x in data]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(analysis_types), 2)  # +1 for 'Other'
        self.assertIn(self.analysis_type.name, analysis_types)

    def test_analysis_type_invalid_protocol(self):
        """
        Ensure get library types given invalid library protocol behaves
        correctly.
        """
        response = self.client.get(
            reverse("analysis-type-list"),
            {
                "library_protocol_id": "blah",
            },
        )
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, [])


class OrphanedIndexPairTest(BaseTestCase):
    """
    IndexPair.index_type is on_delete=SET_NULL, so deleting an IndexType
    leaves its pairs behind with index_type=None. __str__ must cope with
    that, otherwise the IndexPair admin changelist returns HTTP 500.
    """

    def setUp(self):
        index_type = create_index_type("ONT Native Barcoding 96", format="plate")
        index1 = IndexI7.objects.create(prefix="NB", number="01", index="ACGT")
        index_type.indices_i7.add(index1)
        IndexPair.objects.create(
            index_type=index_type, index1=index1, char_coord="A", num_coord=1
        )

        # Same sequence as in the admin: delete the index, then the type.
        index1.delete()
        index_type.delete()

        self.pair = IndexPair.objects.get()

    def test_str_without_index_type(self):
        self.assertIsNone(self.pair.index_type)
        self.assertEqual(str(self.pair), "")

    def test_admin_changelist_with_orphaned_pair(self):
        user = self.create_user(email="admin@test.io")
        user.is_superuser = True
        user.save()
        self.client.force_login(user)

        response = self.client.get(
            reverse("admin:library_sample_shared_indexpair_changelist")
        )
        self.assertEqual(response.status_code, 200)


class GuardedIndexDeleteTest(BaseTestCase):
    """
    Index records are never deleted while a Library/Sample at status >= 5
    (Sequencing) uses them; they are archived instead. Unused ones are archived
    unless the user explicitly confirms permanent deletion.
    """

    def setUp(self):
        user = self.create_user(email="admin@test.io")
        user.is_superuser = True
        user.save()
        self.client.force_login(user)

        self.index_type = create_index_type("Plate", is_dual=True, format="plate")
        self.i7 = IndexI7.objects.create(prefix="i7_", number="01", index="ACGT")
        self.i5 = IndexI5.objects.create(prefix="i5_", number="01", index="TTTT")
        self.index_type.indices_i7.add(self.i7)
        self.index_type.indices_i5.add(self.i5)
        self.pair = IndexPair.objects.create(
            index_type=self.index_type,
            index1=self.i7,
            index2=self.i5,
            char_coord="A",
            num_coord=1,
        )

    def _library(self, status, index_type=None, i7="", i5=""):
        from library.tests import create_library

        library = create_library(
            f"lib{status}", status=status, index_type=index_type or self.index_type
        )
        library.index_i7 = i7
        library.index_i5 = i5
        library.save()
        return library

    def _delete_type(self, confirm=True):
        data = {"post": "yes"}
        if confirm:
            data["confirm_permanent_delete"] = "yes"
        return self.client.post(
            reverse(
                "admin:library_sample_shared_indextype_delete",
                args=[self.index_type.pk],
            ),
            data,
        )

    def _all_archived(self):
        for obj in (self.index_type, self.pair, self.i7, self.i5):
            obj.refresh_from_db()
        return all(o.archived for o in (self.index_type, self.pair, self.i7, self.i5))

    def test_unused_type_confirmed_is_deleted_with_pairs_and_indices(self):
        self._delete_type(confirm=True)
        self.assertFalse(IndexType.objects.exists())
        self.assertFalse(IndexPair.objects.exists())
        self.assertFalse(IndexI7.objects.exists())
        self.assertFalse(IndexI5.objects.exists())

    def test_unused_type_without_confirm_is_archived_not_deleted(self):
        self._delete_type(confirm=False)
        self.assertTrue(IndexType.objects.filter(pk=self.index_type.pk).exists())
        self.assertTrue(self._all_archived())

    def test_type_used_at_sequencing_is_archived_even_if_confirmed(self):
        self._library(5)
        self._delete_type(confirm=True)
        self.assertTrue(IndexType.objects.filter(pk=self.index_type.pk).exists())
        self.assertTrue(self._all_archived())

    def test_status_below_sequencing_and_negative_do_not_count_as_used(self):
        self._library(4)
        self._library(-1)
        self._delete_type(confirm=True)
        self.assertFalse(IndexType.objects.exists())

    def test_usage_found_by_sequence_when_record_has_no_index_type(self):
        # Library whose IndexType FK is gone but whose i7 sequence is in use.
        other = create_index_type("Other")
        library = self._library(6, index_type=other, i7="ACGT")
        IndexType.objects.filter(pk=other.pk).delete()
        library.refresh_from_db()
        self.assertIsNone(library.index_type)

        self.client.post(
            reverse("admin:library_sample_shared_indexi7_delete", args=[self.i7.pk]),
            {"post": "yes", "confirm_permanent_delete": "yes"},
        )
        self.assertTrue(IndexI7.objects.filter(pk=self.i7.pk).exists())
        self.i7.refresh_from_db()
        self.assertTrue(self.i7.archived)

    def test_deleting_unused_index_removes_pairs_built_on_it(self):
        self.client.post(
            reverse("admin:library_sample_shared_indexi5_delete", args=[self.i5.pk]),
            {"post": "yes", "confirm_permanent_delete": "yes"},
        )
        self.assertFalse(IndexI5.objects.filter(pk=self.i5.pk).exists())
        self.assertFalse(IndexPair.objects.exists())

    def test_deleting_unused_pair_cleans_up_its_indices(self):
        self.client.post(
            reverse(
                "admin:library_sample_shared_indexpair_delete", args=[self.pair.pk]
            ),
            {"post": "yes", "confirm_permanent_delete": "yes"},
        )
        self.assertFalse(IndexPair.objects.exists())
        self.assertFalse(IndexI7.objects.exists())
        self.assertFalse(IndexI5.objects.exists())
        self.assertTrue(IndexType.objects.filter(pk=self.index_type.pk).exists())

    def test_deleting_pair_leaves_index_shared_with_other_pair(self):
        other = IndexPair.objects.create(
            index_type=self.index_type,
            index1=self.i7,
            index2=IndexI5.objects.create(prefix="i5_", number="02", index="AAAA"),
            char_coord="A",
            num_coord=2,
        )
        self.client.post(
            reverse(
                "admin:library_sample_shared_indexpair_delete", args=[self.pair.pk]
            ),
            {"post": "yes", "confirm_permanent_delete": "yes"},
        )
        self.assertFalse(IndexPair.objects.filter(pk=self.pair.pk).exists())
        self.assertTrue(IndexI7.objects.filter(pk=self.i7.pk).exists())
        self.assertFalse(IndexI5.objects.filter(pk=self.i5.pk).exists())
        self.assertTrue(IndexPair.objects.filter(pk=other.pk).exists())

    def test_used_pair_is_archived_even_when_permanent_delete_confirmed(self):
        self._library(5, i7="ACGT")
        self.client.post(
            reverse(
                "admin:library_sample_shared_indexpair_delete", args=[self.pair.pk]
            ),
            {"post": "yes", "confirm_permanent_delete": "yes"},
        )
        self.assertTrue(IndexPair.objects.filter(pk=self.pair.pk).exists())
        self.assertTrue(self._all_archived())

    def test_bulk_action_archives_used_and_deletes_unused_when_confirmed(self):
        used_type = create_index_type("Used")
        self._library(5, index_type=used_type)

        response = self.client.post(
            reverse("admin:library_sample_shared_indextype_changelist"),
            {
                "action": "delete_guarded",
                "_selected_action": [self.index_type.pk, used_type.pk],
                "post": "yes",
                "confirm_permanent_delete": "yes",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(IndexType.objects.filter(pk=self.index_type.pk).exists())
        used_type.refresh_from_db()
        self.assertTrue(used_type.archived)

    def test_plain_delete_selected_action_is_not_offered(self):
        response = self.client.get(
            reverse("admin:library_sample_shared_indextype_changelist")
        )
        self.assertNotContains(response, 'value="delete_selected"')
        self.assertContains(response, 'value="delete_guarded"')

    def test_archiving_an_index_type_cascades_to_pairs_and_indices(self):
        self.client.post(
            reverse("admin:library_sample_shared_indextype_changelist"),
            {"action": "mark_as_archived", "_selected_action": [self.index_type.pk]},
        )
        self.assertTrue(self._all_archived())


class ImportIndexPairsAtomicTest(BaseTestCase):
    """A failure part-way through an Index Pair spreadsheet import must not
    leave the rows imported before it behind."""

    def setUp(self):
        user = self.create_user(email="admin@test.io")
        user.is_superuser = True
        user.save()
        self.client.force_login(user)
        create_index_type("Plate", is_dual=True, format="plate")

    def _xlsx(self, rows):
        from io import BytesIO

        from django.core.files.uploadedfile import SimpleUploadedFile
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.append(
            [
                "index1_prefix",
                "index1_name",
                "index1_sequence",
                "index2_prefix",
                "index2_name",
                "index2_sequence",
                "coordinate",
                "index_type",
            ]
        )
        for row in rows:
            ws.append(row)
        buf = BytesIO()
        wb.save(buf)
        return SimpleUploadedFile("pairs.xlsx", buf.getvalue())

    def test_failure_on_second_row_rolls_back_first_row(self):
        from unittest import mock

        rows = [
            ["i7_", "01", "ACGT", "i5_", "01", "TTTT", "A2", "Plate"],
            ["i7_", "02", "CGTA", "i5_", "02", "AAAA", "B2", "Plate"],
        ]
        real_create = IndexPair.objects.create
        calls = []

        def fail_on_second(*args, **kwargs):
            calls.append(1)
            if len(calls) == 2:
                raise RuntimeError("boom")
            return real_create(*args, **kwargs)

        with mock.patch.object(IndexPair.objects, "create", fail_on_second):
            response = self.client.post(
                "/admin/library_sample_shared/indexpair/import_plate_pairs/",
                {"file": self._xlsx(rows)},
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(calls), 2)
        self.assertEqual(IndexPair.objects.count(), 0)
        self.assertEqual(IndexI7.objects.count(), 0)
        self.assertEqual(IndexI5.objects.count(), 0)


class GuardedCatalogDeleteTest(BaseTestCase):
    """Catalog entries still referenced by a library are archived, never deleted."""

    def setUp(self):
        user = self.create_user(email="admin@test.io")
        user.is_superuser = True
        user.save()
        self.client.force_login(user)

        from library.tests import create_library

        self.library = create_library("lib")

    def _delete(self, obj, name, confirm=True):
        data = {"post": "yes"}
        if confirm:
            data["confirm_permanent_delete"] = "yes"
        return self.client.post(
            reverse(f"admin:library_sample_shared_{name}_delete", args=[obj.pk]),
            data,
        )

    def test_used_entries_are_archived_even_when_permanent_delete_confirmed(self):
        for obj, name in (
            (self.library.organism, "organism"),
            (self.library.read_length, "readlength"),
            (self.library.library_protocol, "libraryprotocol"),
            (self.library.analysis_type, "analysistype"),
        ):
            with self.subTest(model=name):
                self._delete(obj, name)
                obj.refresh_from_db()
                self.assertTrue(obj.archived)
        self.library.refresh_from_db()
        self.assertIsNotNone(self.library.organism)
        self.assertIsNotNone(self.library.analysis_type)

    def test_unused_entry_is_archived_unless_permanent_delete_confirmed(self):
        organism = Organism.objects.create(name="Unused")
        self._delete(organism, "organism", confirm=False)
        organism.refresh_from_db()
        self.assertTrue(organism.archived)

        self._delete(organism, "organism")
        self.assertFalse(Organism.objects.filter(pk=organism.pk).exists())

    def _other_catalog_entries(self):
        from common.models import Organization, PrincipalInvestigator
        from flowcell.tests import create_flowcell, create_sequencer
        from index_generator.tests import create_pool
        from sample.tests import create_sample

        sample = create_sample("sample")
        sequencer = create_sequencer("Sequencer")
        create_flowcell("FC1", sequencer)
        pool = create_pool(self.create_user(email="pool@test.io"))
        organization = Organization.objects.create(name="Org")
        pi = PrincipalInvestigator.objects.create(name="pi", organization=organization)
        user = self.create_user(email="pi-user@test.io")
        user.pi = pi
        user.save()

        return (
            (sample.nucleic_acid_type, "sample", "nucleicacidtype"),
            (sequencer, "flowcell", "sequencer"),
            (pool.size, "index_generator", "poolsize"),
            (pi, "common", "principalinvestigator"),
            (organization, "common", "organization"),
        )

    def test_other_used_entries_are_archived_even_when_permanent_delete_confirmed(
        self,
    ):
        for obj, app, name in self._other_catalog_entries():
            with self.subTest(model=name):
                response = self.client.post(
                    reverse(f"admin:{app}_{name}_delete", args=[obj.pk]),
                    {"post": "yes", "confirm_permanent_delete": "yes"},
                )
                self.assertEqual(response.status_code, 302)
                obj.refresh_from_db()
                self.assertTrue(obj.archived)

    def test_other_unused_entries_are_archived_unless_permanent_delete_confirmed(
        self,
    ):
        from common.models import Organization, PrincipalInvestigator
        from flowcell.models import Sequencer
        from index_generator.models import PoolSize
        from sample.models import NucleicAcidType

        organization = Organization.objects.create(name="Unused org")
        unused = (
            (
                NucleicAcidType.objects.create(name="Unused"),
                "sample",
                "nucleicacidtype",
            ),
            (
                Sequencer.objects.create(name="Unused", lanes=1, lane_capacity=1),
                "flowcell",
                "sequencer",
            ),
            (
                PoolSize.objects.create(multiplier=1, size=1),
                "index_generator",
                "poolsize",
            ),
            (
                PrincipalInvestigator.objects.create(
                    name="unused", organization=organization
                ),
                "common",
                "principalinvestigator",
            ),
            (organization, "common", "organization"),
        )
        for obj, app, name in unused:
            url = reverse(f"admin:{app}_{name}_delete", args=[obj.pk])
            with self.subTest(model=name, confirm=False):
                self.client.post(url, {"post": "yes"})
                obj.refresh_from_db()
                self.assertTrue(obj.archived)
            with self.subTest(model=name, confirm=True):
                self.client.post(
                    url, {"post": "yes", "confirm_permanent_delete": "yes"}
                )
                self.assertFalse(type(obj).objects.filter(pk=obj.pk).exists())


class ArchiveHistoryTest(BaseTestCase):
    """Archiving and un-archiving of history-tracked models is logged."""

    def setUp(self):
        user = self.create_user(email="admin@test.io")
        user.is_superuser = True
        user.save()
        self.client.force_login(user)

    def _history(self, obj):
        return list(
            obj.history.order_by("history_date", "history_id").values_list(
                "archived", "history_type"
            )
        )

    def test_guarded_delete_logs_archiving(self):
        organism = Organism.objects.create(name="Tracked")
        self.client.post(
            reverse("admin:library_sample_shared_organism_delete", args=[organism.pk]),
            {"post": "yes"},
        )
        organism.refresh_from_db()
        self.assertTrue(organism.archived)
        self.assertEqual(self._history(organism), [(False, "+"), (True, "~")])

    def test_admin_actions_log_archiving_and_unarchiving(self):
        organism = Organism.objects.create(name="Tracked")
        url = (
            reverse("admin:library_sample_shared_organism_changelist")
            + "?archived__exact=_all"
        )
        for action in ("mark_as_archived", "mark_as_non_archived"):
            self.client.post(
                url,
                {"action": action, "_selected_action": [organism.pk]},
            )
        organism.refresh_from_db()
        self.assertFalse(organism.archived)
        self.assertEqual(
            self._history(organism), [(False, "+"), (True, "~"), (False, "~")]
        )

    def test_already_archived_rows_get_no_extra_history(self):
        organism = Organism.objects.create(name="Tracked", archived=True)
        url = (
            reverse("admin:library_sample_shared_organism_changelist")
            + "?archived__exact=_all"
        )
        self.client.post(
            url, {"action": "mark_as_archived", "_selected_action": [organism.pk]}
        )
        self.assertEqual(self._history(organism), [(True, "+")])

    def test_untracked_model_is_still_archived(self):
        from flowcell.models import Sequencer

        sequencer = Sequencer.objects.create(name="Plain", lanes=1, lane_capacity=1)
        self.client.post(
            reverse("admin:flowcell_sequencer_changelist"),
            {"action": "mark_as_archived", "_selected_action": [sequencer.pk]},
        )
        sequencer.refresh_from_db()
        self.assertTrue(sequencer.archived)


class TrackedModelsHistoryTest(BaseTestCase):
    """Edits to newly tracked models are logged and the history page renders."""

    def setUp(self):
        user = self.create_user(email="admin@test.io")
        user.is_superuser = True
        user.save()
        self.client.force_login(user)

    def _assert_history_page(self, obj):
        meta = obj._meta
        url = reverse(
            f"admin:{meta.app_label}_{meta.model_name}_history", args=[obj.pk]
        )
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_history_pages_render_for_newly_tracked_models(self):
        from flowcell.models import Sequencer
        from index_generator.models import PoolSize
        from library.tests import create_library
        from sample.models import NucleicAcidType
        from sample.tests import create_sample

        objs = [
            create_library("lib"),
            create_sample("sample"),
            Sequencer.objects.create(name="Seq", lanes=1, lane_capacity=1),
            PoolSize.objects.create(multiplier=1, size=1),
            NucleicAcidType.objects.create(name="NAT"),
            ReadLength.objects.create(name="RL"),
            IndexType.objects.create(name="IT"),
            self.create_user(email="u@test.io"),
        ]
        for obj in objs:
            with self.subTest(model=obj._meta.label):
                self._assert_history_page(obj)

    def test_library_and_sample_saves_are_logged(self):
        from library.tests import create_library
        from sample.tests import create_sample

        for obj in (create_library("lib"), create_sample("sample")):
            with self.subTest(model=obj._meta.label):
                obj.status = 1
                obj.save()
                self.assertEqual(
                    list(
                        obj.history.order_by("history_date", "history_id").values_list(
                            "status", "history_type"
                        )
                    ),
                    [(0, "+"), (1, "~")],
                )

    def test_user_cost_unit_reassignment_is_logged(self):
        from common.models import CostUnit

        user = self.create_user(email="cu@test.io")
        cost_unit = CostUnit.objects.create(name="CU")
        user.cost_unit.add(cost_unit)
        user.save()
        latest = user.history.latest()
        self.assertEqual(
            [c.cost_unit_id for c in latest.cost_unit.all()], [cost_unit.pk]
        )

    def test_user_history_excludes_password_and_last_login(self):
        fields = {f.name for f in get_user_model().history.model._meta.get_fields()}
        self.assertNotIn("password", fields)
        self.assertNotIn("last_login", fields)

    def test_update_with_history_logs_bulk_status_change(self):
        from common.utils import update_with_history
        from library.models import Library
        from library.tests import create_library

        library = create_library("lib")
        update_with_history(Library.objects.filter(pk=library.pk), status=4)
        library.refresh_from_db()
        self.assertEqual(library.status, 4)
        self.assertEqual(
            list(
                library.history.order_by("history_date", "history_id").values_list(
                    "status", "history_type"
                )
            ),
            [(0, "+"), (4, "~")],
        )
