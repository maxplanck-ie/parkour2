import json

from common.tests import BaseTestCase
from common.utils import get_random_name
from django.apps import apps
from flowcell.tests import create_flowcell
from index_generator.tests import create_pool, create_pool_size
from library.tests import create_library
from request.tests import create_request
from sample.tests import create_sample

Flowcell = apps.get_model("flowcell", "Flowcell")
Lane = apps.get_model("flowcell", "Lane")


class TestRunStatistics(BaseTestCase):
    def setUp(self):
        self.user = self.create_user()
        self.login()

    def test_flowcell_list(self):
        library1 = create_library(get_random_name(), 4)
        library2 = create_library(get_random_name(), 4)
        sample1 = create_sample(get_random_name(), 4)
        sample2 = create_sample(get_random_name(), 4)

        request = create_request(self.user)
        request.libraries.add(library1)
        request.libraries.add(library2)
        request.samples.add(sample1)
        request.samples.add(sample2)

        pool = create_pool(self.user)
        pool.libraries.add(library1)
        pool.libraries.add(library2)
        pool.samples.add(sample1)
        pool.samples.add(sample2)

        pool_size = create_pool_size(multiplier=8)
        flowcell = create_flowcell(get_random_name(), pool_size)

        lanes = []
        matrix = []
        for i in range(8):
            name = f"Lane {i + 1}"
            lane = Lane(name=name, pool=pool)
            lane.save()

            lanes.append(lane.pk)
            matrix.append({"name": name, "read_1": i + 1})

        flowcell.lanes.add(*lanes)
        flowcell.matrix = matrix
        flowcell.save()

        response = self.client.get("/api/run_statistics/")
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 8)
        self.assertEqual(data[0]["name"], "1")
        self.assertEqual(data[0]["sequencing_kit"], str(flowcell.pool_size))
        self.assertEqual(data[0]["read_length"], library1.read_length.name)
        self.assertEqual(data[0]["read_1"], 1)

    def test_upload_flowcell_matrix(self):
        pool_size = create_pool_size(multiplier=8)
        flowcell = create_flowcell(get_random_name(), pool_size)

        matrix = [
            {
                "name": "Lane 1",
                "density": None,
                "cluster_pf": None,
                "reads_pf": None,
                "undetermined_indices": None,
                "aligned_spike_in": None,
                "read_1": None,
                "read_2": None,
                "read_3": None,
                "read_4": None,
            },
            {
                "name": "Lane 2",
            },
        ]

        response = self.client.post(
            "/api/run_statistics/upload/",
            {
                "flowcell_id": flowcell.flowcell_id,
                "matrix": json.dumps(matrix),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        updated_flowcell = Flowcell.objects.get(pk=flowcell.pk)
        self.assertEqual(updated_flowcell.matrix, matrix)

    def test_upload_flowcell_matrix_invalid_flowcell_id(self):
        flowcell_id = get_random_name()
        response = self.client.post(
            "/api/run_statistics/upload/",
            {
                "flowcell_id": flowcell_id,
            },
        )
        data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data["success"])
        self.assertEqual(
            data["message"],
            f'Flowcell with id "{flowcell_id}" doesn\'t exist.',
        )

    def test_upload_flowcell_matrix_invalid_matrix(self):
        pool_size = create_pool_size(multiplier=8)
        flowcell = create_flowcell(get_random_name(), pool_size)

        response = self.client.post(
            "/api/run_statistics/upload/",
            {
                "flowcell_id": flowcell.flowcell_id,
            },
        )

        data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "Invalid matrix data.")


class TestSequencesStatistics(BaseTestCase):
    def setUp(self):
        self.user = self.create_user()
        self.login()

    def test_flowcell_list(self):
        library1 = create_library(get_random_name(), 4)
        library2 = create_library(get_random_name(), 4)
        sample1 = create_sample(get_random_name(), 4)
        sample2 = create_sample(get_random_name(), 4)

        request = create_request(self.user)
        request.libraries.add(library1)
        request.libraries.add(library2)
        request.samples.add(sample1)
        request.samples.add(sample2)

        pool = create_pool(self.user)
        pool.libraries.add(library1)
        pool.libraries.add(library2)
        pool.samples.add(sample1)
        pool.samples.add(sample2)

        pool_size = create_pool_size(multiplier=8)
        flowcell = create_flowcell(get_random_name(), pool_size)
        sequences = [
            {"barcode": library1.barcode, 'name': library1.name},
            {"barcode": library2.barcode, 'name': library2.name},
            {"barcode": sample1.barcode, 'name': sample1.name},
            {"barcode": sample2.barcode, 'name': sample2.name},
        ]

        lanes = []
        for i in range(8):
            name = f"Lane {i + 1}"
            lane = Lane(name=name, pool=pool)
            lane.save()
            lanes.append(lane.pk)

        flowcell.lanes.add(*lanes)
        flowcell.sequences = sequences
        flowcell.save()

        response = self.client.get("/api/sequences_statistics/")
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 4)
        self.assertEqual(data[0]["sequencing_kit"], str(flowcell.pool_size))

    def test_upload_flowcell_sequences(self):
        pool_size = create_pool_size(multiplier=8)
        flowcell = create_flowcell(get_random_name(), pool_size)

        sequences = [
            {"barcode": "barcode"},
            {"barcode": "barcode"},
        ]

        response = self.client.post(
            "/api/sequences_statistics/upload/",
            {
                "flowcell_id": flowcell.flowcell_id,
                "sequences": json.dumps(sequences),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        updated_flowcell = Flowcell.objects.get(pk=flowcell.pk)
        self.assertEqual(updated_flowcell.sequences, sequences)

    def test_upload_flowcell_sequences_invalid_flowcell_id(self):
        flowcell_id = get_random_name()
        response = self.client.post(
            "/api/sequences_statistics/upload/",
            {
                "flowcell_id": flowcell_id,
            },
        )
        data = response.json()
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data["detail"], "Not found.")

    def test_upload_flowcell_sequences_invalid_data(self):
        pool_size = create_pool_size(multiplier=8)
        flowcell = create_flowcell(get_random_name(), pool_size)

        response = self.client.post(
            "/api/sequences_statistics/upload/",
            {
                "flowcell_id": flowcell.flowcell_id,
            },
        )

        data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "Invalid sequences data.")
