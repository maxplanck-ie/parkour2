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
    IndexType,
    LibraryProtocol,
    LibraryType,
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


def create_index_type(
    name, save=True, is_dual=False, index_length="8", format="single"
):
    index_type = IndexType(
        name=name, is_dual=is_dual, index_length=index_length, format=format
    )

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

    def test_library_protocol_in_library_type(self):
        """
        Ensure a new library protocol is added to the list of protocols of
        the library type 'Other'.
        """
        library_type = LibraryType.objects.get(name="Other")
        library_protocols = library_type.library_protocol.all().values_list(
            "name", flat=True
        )
        self.assertIn(self.library_protocol.name, library_protocols)


class LibraryTypeTest(TestCase):
    def setUp(self):
        self.library_type = LibraryType(name=get_random_name())

    def test_library_type_name(self):
        self.assertTrue(isinstance(self.library_type, LibraryType))
        self.assertEqual(self.library_type.__str__(), self.library_type.name)


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


class TestLibraryTypes(BaseTestCase):
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

        self.library_type = LibraryType(name=self._get_random_name())
        self.library_type.save()
        self.library_type.library_protocol.add(self.library_protocol)

    def test_library_type_list(self):
        """Ensure get library types behaves correctly."""
        response = self.client.get(reverse("library-type-list"))
        data = response.json()
        library_types = [x["name"] for x in data]
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.library_type.name, library_types)

    def test_library_type_with_protocol_list(self):
        """
        Ensure get library types given library protocol behaves correctly.
        """
        response = self.client.get(
            reverse("library-type-list"),
            {
                "library_protocol_id": self.library_protocol.pk,
            },
        )
        data = response.json()
        library_types = [x["name"] for x in data]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(library_types), 2)  # +1 for 'Other'
        self.assertIn(self.library_type.name, library_types)

    def test_library_type_invalid_protocol(self):
        """
        Ensure get library types given invalid library protocol behaves
        correctly.
        """
        response = self.client.get(
            reverse("library-type-list"),
            {
                "library_protocol_id": "blah",
            },
        )
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, [])
