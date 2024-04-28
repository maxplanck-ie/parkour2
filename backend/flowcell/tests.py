import json

from common.tests import BaseTestCase
from common.utils import get_random_name
from django.urls import reverse
from index_generator.tests import create_pool, create_pool_size
from library.tests import create_library
from sample.tests import create_sample

from .models import Flowcell, Lane, Sequencer


def create_sequencer(name, lanes=1, lane_capacity=200):
    sequencer = Sequencer(
        name=name,
    )
    sequencer.save()
    create_pool_size(multiplier=lanes, size=lane_capacity, cycles=150, sequencer=sequencer)
    return sequencer


def create_lane(name, pool):
    lane = Lane(
        name=name,
        pool=pool,
        loading_concentration=1.0,
    )
    lane.save()
    return lane


def create_flowcell(flowcell_id, pool_size):
    flowcell = Flowcell(
        flowcell_id=flowcell_id,
        pool_size=pool_size,
    )
    flowcell.save()
    return flowcell


# Models


class TestSequencerModel(BaseTestCase):
    def setUp(self):
        self.sequencer = create_sequencer(get_random_name())

    def test_sequencer_name(self):
        self.assertTrue(isinstance(self.sequencer, Sequencer))
        self.assertEqual(self.sequencer.__str__(), self.sequencer.name)

    def test_sequencer_lanes(self):
        self.assertEqual(self.sequencer.poolsize_set.first().lanes, 1)

    def test_sequencer_lane_capacity(self):
        self.assertEqual(self.sequencer.poolsize_set.first().size, 200)

    def test_sequencer_different_lanes(self):
        sequencer = create_sequencer(get_random_name(), lanes=2, lane_capacity=200)
        self.assertEqual(sequencer.poolsize_set.first().lanes, 2)


class TestLaneModel(BaseTestCase):
    def setUp(self):
        self.user = self.create_user("test@test.io", "foo-bar")
        pool = create_pool(self.user)
        self.lane = create_lane(get_random_name(len=6), pool)

    def test_lane_name(self):
        self.assertTrue(isinstance(self.lane, Lane))
        self.assertEqual(
            self.lane.__str__(), f"{self.lane.name}: {self.lane.pool.name}"
        )

    def test_lane_loading_concentration(self):
        self.assertEqual(self.lane.loading_concentration, 1.0)

    def test_lane_phix(self):
        self.assertIsNone(self.lane.phix)

    def test_lane_completed(self):
        self.assertFalse(self.lane.completed)

    def test_increment_pool_loaded(self):
        """
        Ensure a lane pool's value 'loaded' is incremented
        when the lane is created.
        """
        pool1 = create_pool(self.user)
        pool2 = create_pool(self.user)
        self.assertEqual(pool1.loaded, 0)
        self.assertEqual(pool1.loaded, 0)

        create_lane("Lane 1", pool1)
        create_lane("Lane 2", pool2)
        create_lane("Lane 3", pool2)
        self.assertEqual(pool1.loaded, 1)
        self.assertEqual(pool2.loaded, 2)


class TestFlowcellModel(BaseTestCase):
    def setUp(self):
        pool_size = create_pool_size()
        self.flowcell = create_flowcell(get_random_name(), pool_size)

    def test_lane_name(self):
        self.assertTrue(isinstance(self.flowcell, Flowcell))
        self.assertEqual(self.flowcell.__str__(), self.flowcell.flowcell_id)

    def test_flowcell_different_sequencer(self):
        sequencer = create_sequencer(get_random_name(), lanes=2)
        flowcell = create_flowcell(get_random_name(), sequencer.poolsize_set.first())
        self.assertEqual(flowcell.pool_size.sequencer, sequencer)

    def test_flowcell_lanes(self):
        self.assertEqual(self.flowcell.lanes.count(), 0)

    def test_flowcell_requests(self):
        self.assertEqual(self.flowcell.requests.count(), 0)

    def test_flowcell_matrix(self):
        self.assertIsNone(self.flowcell.matrix)

    def test_flowcell_sequences(self):
        self.assertIsNone(self.flowcell.sequences)


# Views


class TestSequencer(BaseTestCase):
    def setUp(self):
        self.create_user()
        self.login()

    def test_sequencer_list(self):
        """Ensure get sequencer list behaves correctly."""
        sequencer = create_sequencer(get_random_name())
        response = self.client.get(reverse("sequencers-list"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        sequencers = [x["name"] for x in data]
        self.assertIn(sequencer.name, sequencers)


class TestFlowcell(BaseTestCase):
    """Tests for flowcells."""

    def setUp(self):
        self.user = self.create_user()

    def test_pool_list(self):
        """Ensure get pool list behaves correctly."""
        self.client.login(email="test@test.io", password="foo-bar")

        # Case 1: pool is ready
        pool1 = create_pool(self.user)
        library1 = create_library(get_random_name(), status=4)
        library2 = create_library(get_random_name(), status=-1)  # failed P QC
        sample1 = create_sample(get_random_name(), status=4)
        pool1.libraries.add(*[library1.pk, library2.pk])
        pool1.samples.add(sample1)

        # Case 2: pool is not ready
        pool2 = create_pool(self.user)
        library3 = create_library(get_random_name(), status=4)
        sample2 = create_sample(get_random_name(), status=3)
        pool2.libraries.add(library3)
        pool2.samples.add(sample2.pk)

        # Case 3: some of the pool's samples haven't reached the Pooling step
        pool3 = create_pool(self.user)
        sample3 = create_sample(get_random_name(), status=2)  # no Pooling obj
        sample4 = create_sample(get_random_name(), status=-1)  # failed P QC
        pool3.samples.add(*[sample3.pk, sample4.pk])

        response = self.client.get(reverse("flowcells-pool-list"))
        data = response.json()

        self.assertEqual(response.status_code, 200)
        pools = [x["name"] for x in data]
        self.assertIn(pool1.name, pools)
        self.assertIn(pool2.name, pools)
        self.assertNotIn(pool3.name, pools)

        pool1_obj = [x for x in data if x["name"] == pool1.name][0]
        pool2_obj = [x for x in data if x["name"] == pool2.name][0]
        self.assertTrue(pool1_obj["ready"])
        self.assertFalse(pool2_obj["ready"])

        self.assertTrue(data[0]["read_length_name"], library1.read_length.name)
        self.assertTrue(data[1]["read_length_name"], sample1.read_length.name)
        self.assertTrue(data[0]["pool_size"], pool1.size.multiplier)
        self.assertTrue(data[1]["pool_size"], pool2.size.multiplier)

    def test_flowcell_list(self):
        """Ensure get flowcell list behaves correctly."""
        self.client.login(email="test@test.io", password="foo-bar")

        library1 = create_library(get_random_name(), 4)
        library2 = create_library(get_random_name(), 4)
        sample1 = create_sample(get_random_name(), 4)
        sample2 = create_sample(get_random_name(), 4)

        pool1 = create_pool(self.user)
        pool1.libraries.add(library1)
        pool1.samples.add(sample1)

        pool2 = create_pool(self.user)
        pool2.libraries.add(library2)
        pool2.samples.add(sample2)

        pool_size = create_pool_size(multiplier=4)
        flowcell = create_flowcell(get_random_name(), pool_size)

        lanes1 = []
        for i in range(2):
            name = f"Lane {i + 1}"
            lane = Lane(name=name, pool=pool1)
            lane.save()
            lanes1.append(lane.pk)

        lanes2 = []
        for i in range(2, 4):
            name = f"Lane {i + 1}"
            lane = Lane(name=name, pool=pool2, completed=True)
            lane.save()
            lanes2.append(lane.pk)

        flowcell.lanes.add(*lanes1)
        flowcell.lanes.add(*lanes2)

        response = self.client.get(reverse("flowcells-list"))
        data = response.json()
        self.assertEqual(response.status_code, 200)
        lane_ids = [x["pk"] for x in data]
        self.assertIn(lanes1[0], lane_ids)
        self.assertIn(lanes1[1], lane_ids)
        self.assertNotIn(lanes2[0], lane_ids)
        self.assertNotIn(lanes2[1], lane_ids)

    def test_create_flowcell(self):
        """Ensure create flowcell behaves correctly."""
        self.client.login(email="test@test.io", password="foo-bar")

        library1 = create_library(get_random_name(), 4)
        library2 = create_library(get_random_name(), 4)
        sample1 = create_sample(get_random_name(), 4)
        sample2 = create_sample(get_random_name(), 4)

        pool1 = create_pool(self.user, multiplier=4)
        pool1.libraries.add(library1)
        pool1.samples.add(sample1)

        pool2 = create_pool(self.user, multiplier=8)
        pool2.libraries.add(library2)
        pool2.samples.add(sample2)

        pool_size = create_pool_size(multiplier=8)
        flowcell_id = get_random_name()

        lanes1 = [
            {
                "name": f"Lane {i + 1}",
                "pool_id": pool1.pk,
            }
            for i in range(4)
        ]

        lanes2 = [
            {
                "name": f"Lane {i + 1}",
                "pool_id": pool2.pk,
            }
            for i in range(4, 8)
        ]

        response = self.client.post(
            reverse("flowcells-list"),
            {
                "data": json.dumps(
                    {
                        "flowcell_id": flowcell_id,
                        "pool_size": pool_size.pk,
                        "lanes": lanes1 + lanes2,
                    }
                )
            },
        )
        data = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertTrue(data["success"])
        flowcells = Flowcell.objects.values_list("flowcell_id", flat=True)
        self.assertIn(flowcell_id, flowcells)

        updated_library1 = library1.__class__.objects.get(pk=library1.pk)
        updated_library2 = library2.__class__.objects.get(pk=library2.pk)
        updated_sample1 = sample1.__class__.objects.get(pk=sample1.pk)
        updated_sample2 = sample2.__class__.objects.get(pk=sample2.pk)
        self.assertEqual(updated_library1.status, 5)
        self.assertEqual(updated_library2.status, 4)
        self.assertEqual(updated_sample1.status, 5)
        self.assertEqual(updated_sample2.status, 4)

    def test_create_flowcell_no_lanes(self):
        """Ensure error is thrown if no lanes are provided."""
        self.client.login(email="test@test.io", password="foo-bar")

        sequencer = create_sequencer(get_random_name())
        flowcell_id = get_random_name()

        response = self.client.post(
            reverse("flowcells-list"),
            {
                "data": json.dumps(
                    {
                        "flowcell_id": flowcell_id,
                        "sequencer": sequencer.pk,
                        "lanes": [],
                    }
                )
            },
        )
        data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "Invalid payload.")
        self.assertIn("No lanes are provided.", data["errors"]["lanes"])

    def test_create_flowcell_some_lanes_not_loaded(self):
        """Ensure error is thrown if not all lanes are loaded."""
        self.client.login(email="test@test.io", password="foo-bar")

        library = create_library(get_random_name(), 4)
        pool = create_pool(self.user)
        pool.libraries.add(library)

        lanes = [
            {
                "name": f"Lane {i + 1}",
                "pool_id": pool.pk,
            }
            for i in range(4)
        ]

        pool_size = create_pool_size()
        flowcell_id = get_random_name()

        response = self.client.post(
            reverse("flowcells-list"),
            {
                "data": json.dumps(
                    {
                        "flowcell_id": flowcell_id,
                        "pool_size": pool_size.pk,
                        "lanes": lanes,
                    }
                )
            },
        )
        data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "Invalid payload.")
        self.assertIn("All lanes must be loaded.", data["errors"]["lanes"])

    def test_update_lane(self):
        """Ensure update lanes behaves correctly."""
        self.client.login(email="test@test.io", password="foo-bar")

        library = create_library(get_random_name(), 4)
        pool = create_pool(self.user)
        pool.libraries.add(library)

        pool_size = create_pool_size(multiplier=1)
        flowcell = create_flowcell(get_random_name(), pool_size)

        lane = Lane(name=get_random_name(len=6), pool=pool)
        lane.save()

        flowcell.lanes.add(lane)

        response = self.client.post(
            reverse("flowcells-edit"),
            {
                "data": json.dumps(
                    [
                        {
                            "pk": lane.pk,
                            "loading_concentration": 1.0,
                        }
                    ]
                )
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(Lane.objects.get(pk=lane.pk).loading_concentration, 1.0)

    def test_update_lane_contains_invalid(self):
        """Ensure update lanes containing invalid lanes behaves correctly."""
        self.client.login(email="test@test.io", password="foo-bar")

        library = create_library(get_random_name(), 4)
        pool = create_pool(self.user)
        pool.libraries.add(library)

        pool_size = create_pool_size(multiplier=2)
        flowcell = create_flowcell(get_random_name(), pool_size)

        lane1 = Lane(name=get_random_name(len=6), pool=pool)
        lane1.save()

        lane2 = Lane(name=get_random_name(len=6), pool=pool)
        lane2.save()

        flowcell.lanes.add(*[lane1.pk, lane2.pk])

        response = self.client.post(
            reverse("flowcells-edit"),
            {
                "data": json.dumps(
                    [
                        {
                            "pk": lane1.pk,
                            "loading_concentration": 1.0,
                        },
                        {
                            "pk": lane2.pk,
                            "loading_concentration": "blah",
                        },
                    ]
                )
            },
        )
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(data["message"], "Some records cannot be updated.")
        self.assertEqual(Lane.objects.get(pk=lane1.pk).loading_concentration, 1.0)

    def test_quality_check_completed(self):
        """Ensure quality check has completed behaves correctly."""
        self.client.login(email="test@test.io", password="foo-bar")

        library = create_library(get_random_name(), 4)
        pool = create_pool(self.user)
        pool.libraries.add(library)

        pool_size = create_pool_size(multiplier=1)
        flowcell = create_flowcell(get_random_name(), pool_size)

        lane = Lane(name=get_random_name(len=6), pool=pool)
        lane.save()

        flowcell.lanes.add(lane)

        response = self.client.post(
            reverse("flowcells-edit"),
            {
                "data": json.dumps(
                    [
                        {
                            "pk": lane.pk,
                            "quality_check": "completed",
                        }
                    ]
                )
            },
        )

        updated_lane = Lane.objects.get(pk=lane.pk)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertTrue(updated_lane.completed)

    def test_invalid_json(self):
        """Ensure error is thrown if the JSON object is empty."""
        self.client.login(email="test@test.io", password="foo-bar")
        response = self.client.post(reverse("flowcells-edit"), {})
        data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data["success"])
        self.assertIn("Invalid payload.", data["message"])
