import math

from utils.restaurant_recommender import haversine_meters, cluster_orders_by_proximity


def test_haversine_meters_zero():
    assert haversine_meters(0, 0, 0, 0) == 0


def test_haversine_meters_known_distance():
    # Distance between (0,0) and (0,1) ~ 111.195 km
    d = haversine_meters(0, 0, 0, 1)
    assert isinstance(d, float)
    assert 111000 <= d <= 112000


def make_order(rest_lat, rest_lng, cust_lat, cust_lng, order_id):
    return {
        "order_id": order_id,
        "restaurant_id": f"r{order_id}",
        "restaurants": {"latitude": rest_lat, "longitude": rest_lng},
        "latitude": cust_lat,
        "longitude": cust_lng,
    }


def test_cluster_orders_by_proximity_groups():
    # Two restaurants very close, customers close -> should group
    o1 = make_order(37.0, -122.0, 37.001, -122.001, "1")
    o2 = make_order(37.0005, -122.0005, 37.002, -122.002, "2")
    o3 = make_order(38.0, -123.0, 38.0, -123.0, "3")

    groups = cluster_orders_by_proximity([o1, o2, o3], rest_threshold_m=200, cust_threshold_m=500)
    # Expect one group with o1 and o2, and one singleton for o3
    assert any(len(g) == 2 for g in groups)
    assert any(len(g) == 1 for g in groups)


def test_cluster_orders_by_proximity_singletons_when_far():
    o1 = make_order(0, 0, 0, 0, "1")
    o2 = make_order(10, 10, 10, 10, "2")
    groups = cluster_orders_by_proximity([o1, o2], rest_threshold_m=1000, cust_threshold_m=1000)
    # Very far apart -> two singletons
    assert len(groups) == 2
    assert all(len(g) == 1 for g in groups)
import routes.delivery_routes as delivery_routes
from utils.restaurant_recommender import cluster_orders_by_proximity, haversine_meters


def test_haversine_meters_zero():
    assert haversine_meters(0, 0, 0, 0) == 0


def test_haversine_meters_known_distance():
    # Distance between (0,0) and (0,1) ~ 111.195 km
    d = haversine_meters(0, 0, 0, 1)
    assert isinstance(d, float)
    assert 111000 <= d <= 112000


def make_order(rest_lat, rest_lng, cust_lat, cust_lng, order_id):
    return {
        "order_id": order_id,
        "restaurant_id": f"r{order_id}",
        "restaurants": {"latitude": rest_lat, "longitude": rest_lng},
        "latitude": cust_lat,
        "longitude": cust_lng,
    }


def test_cluster_orders_by_proximity_groups():
    # Two restaurants very close, customers close -> should group
    o1 = make_order(37.0, -122.0, 37.001, -122.001, "1")
    o2 = make_order(37.0005, -122.0005, 37.002, -122.002, "2")
    o3 = make_order(38.0, -123.0, 38.0, -123.0, "3")

    groups = cluster_orders_by_proximity(
        [o1, o2, o3], rest_threshold_m=200, cust_threshold_m=500
    )
    # Expect one group with o1 and o2, and one singleton for o3
    assert any(len(g) == 2 for g in groups)
    assert any(len(g) == 1 for g in groups)


def test_cluster_orders_by_proximity_singletons_when_far():
    o1 = make_order(0, 0, 0, 0, "1")
    o2 = make_order(10, 10, 10, 10, "2")
    groups = cluster_orders_by_proximity(
        [o1, o2], rest_threshold_m=1000, cust_threshold_m=1000
    )
    # Very far apart -> two singletons
    assert len(groups) == 2
    assert all(len(g) == 1 for g in groups)


def test_haversine_meters_none_inputs():
    # Any None input should result in None
    assert haversine_meters(None, 0, 0, 0) is None
    assert haversine_meters(0, None, 0, 0) is None
    assert haversine_meters(0, 0, None, 0) is None
    assert haversine_meters(0, 0, 0, None) is None


def test_haversine_negative_coordinates():
    # Check negative and mixed coordinates
    d = haversine_meters(-33.86, 151.20, 51.50, -0.12)  # Sydney to London approx
    assert isinstance(d, float)
    assert d > 8000000  # should be several thousand km


def test_cluster_orders_missing_restaurant_coords():
    # Orders without restaurant coords should be singletons
    o1 = {
        "order_id": "1",
        "restaurant_id": "r1",
        "restaurants": {},
        "latitude": 37.0,
        "longitude": -122.0,
    }
    o2 = {
        "order_id": "2",
        "restaurant_id": "r2",
        "restaurants": {},
        "latitude": 37.01,
        "longitude": -122.01,
    }
    groups = cluster_orders_by_proximity(
        [o1, o2], rest_threshold_m=5000, cust_threshold_m=5000
    )
    # No restaurant coords -> cannot compute rest distances -> should be two groups (singletons)
    assert len(groups) == 2


def test_cluster_orders_string_coordinates_and_missing_customer():
    # Coordinates as strings should parse; missing customer coords still allow grouping by restaurant proximity
    o1 = {
        "order_id": "1",
        "restaurant_id": "r1",
        "restaurants": {"latitude": "37.0", "longitude": "-122.0"},
        "latitude": None,
        "longitude": None,
    }
    o2 = {
        "order_id": "2",
        "restaurant_id": "r2",
        "restaurants": {"latitude": "37.0005", "longitude": "-122.0005"},
        "latitude": None,
        "longitude": None,
    }
    groups = cluster_orders_by_proximity(
        [o1, o2], rest_threshold_m=200, cust_threshold_m=100
    )
    # Restaurants within 200m -> should group even though customers missing
    assert any(len(g) == 2 for g in groups)


def test_cluster_multiple_groups_and_threshold_behavior():
    # Create 4 orders forming two clusters
    a1 = make_order(40.0, -75.0, 40.001, -75.001, "a1")
    a2 = make_order(40.0004, -75.0004, 40.002, -75.002, "a2")
    b1 = make_order(41.0, -74.0, 41.001, -74.001, "b1")
    b2 = make_order(41.0003, -74.0003, 41.002, -74.002, "b2")

    groups = cluster_orders_by_proximity(
        [a1, a2, b1, b2], rest_threshold_m=600, cust_threshold_m=1000
    )
    # Expect two groups of 2
    sizes = sorted([len(g) for g in groups])
    assert sizes == [2, 2]

    # Now set rest_threshold very small -> all singletons
    groups_small = cluster_orders_by_proximity(
        [a1, a2, b1, b2], rest_threshold_m=10, cust_threshold_m=10
    )
    assert all(len(g) == 1 for g in groups_small)


def test_eco_endpoint_no_orders(client, monkeypatch):
    """Should return type=none when no ready orders."""

    class MockResult:
        def __init__(self, data):
            self.data = data

    class MockSupabaseEmpty:
        def from_(self, table):
            return self

        def select(self, *args, **kwargs):
            return self

        def eq(self, *args, **kwargs):
            return self

        def is_(self, *args, **kwargs):
            return self

        def execute(self):
            return MockResult([])

    monkeypatch.setattr(delivery_routes, "supabase", MockSupabaseEmpty())

    resp = client.get(
        "/api/deliveries/eco", params={"latitude": 37.0, "longitude": -122.0}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "none"
    assert data["orders"] == []


@pytest.mark.asyncio
async def test_eco_endpoint_single_closest_order():
    """Should return single closest order."""
    fake_orders = [
        {
            "order_id": "1",
            "user_id": "u1",
            "restaurant_id": "r1",
            "restaurants": {"latitude": 37.0, "longitude": -122.0},
            "latitude": 37.001,
            "longitude": -122.001,
            "status": "ready",
        }
    ]

    class MockResult:
        def __init__(self, data):
            self.data = data

    class MockSupabase:
        def from_(self, table):
            return self

        def select(self, *args, **kwargs):
            return self

        def eq(self, *args, **kwargs):
            return self

        def is_(self, *args, **kwargs):
            return self

        def execute(self):
            return MockResult(fake_orders)

    monkeypatch.setattr(delivery_routes, "supabase", MockSupabase())

    async def fake_compute(src_lng, src_lat, dests):
        return ({"r1": 120}, {"r1": 20})

    monkeypatch.setattr(
        delivery_routes, "_compute_distances_and_durations", fake_compute
    )

    resp = client.get(
        "/api/deliveries/eco", params={"latitude": 37.0, "longitude": -122.0}
    )
    assert resp.status_code == 200
    data = resp.json()

                assert data["type"] == "single"
                assert data["orders"] == ["1"]


@pytest.mark.asyncio
async def test_eco_endpoint_group_orders():
    """Should return group when clustering produces >1 orders."""
    fake_orders = [
        {
            "order_id": "1",
            "restaurant_id": "r1",
            "restaurants": {"latitude": 37.0, "longitude": -122.0},
            "latitude": 37.001,
            "longitude": -122.001,
            "status": "ready",
        },
        {
            "order_id": "2",
            "restaurant_id": "r2",
            "restaurants": {"latitude": 37.0005, "longitude": -122.0005},
            "latitude": 37.002,
            "longitude": -122.002,
            "status": "ready",
        },
    ]

    class MockResult:
        def __init__(self, data):
            self.data = data

    class MockSupabase:
        def from_(self, table):
            return self

        def select(self, *args, **kwargs):
            return self

        def eq(self, *args, **kwargs):
            return self

        def is_(self, *args, **kwargs):
            return self

        def execute(self):
            return MockResult(fake_orders)

    monkeypatch.setattr(delivery_routes, "supabase", MockSupabase())

    async def fake_compute(src_lng, src_lat, dests):
        return ({"r1": 100, "r2": 110}, {"r1": 20, "r2": 25})

    monkeypatch.setattr(
        delivery_routes, "_compute_distances_and_durations", fake_compute
    )
    monkeypatch.setattr(
        delivery_routes, "cluster_orders_by_proximity", lambda orders: [fake_orders]
    )

    resp = client.get(
        "/api/deliveries/eco", params={"latitude": 37.0, "longitude": -122.0}
    )
    assert resp.status_code == 200
    data = resp.json()

                    assert data["type"] == "group"
                    assert data["group_size"] == 2
                    assert set(data["orders"]) == {"1", "2"}


@pytest.mark.asyncio
async def test_ready_orders_endpoint():
    """Test /deliveries/ready returns enriched orders."""
    fake_orders = [
        {
            "order_id": "1",
            "restaurant_id": "r1",
            "restaurants": {"latitude": 37.0, "longitude": -122.0},
            "latitude": 37.001,
            "longitude": -122.001,
            "status": "ready",
        }
    ]

    class MockResult:
        def __init__(self, data):
            self.data = data

    class MockSupabase:
        def from_(self, table):
            return self

        def select(self, *args, **kwargs):
            return self

        def eq(self, *args, **kwargs):
            return self

        def is_(self, *args, **kwargs):
            return self

        def execute(self):
            return MockResult(fake_orders)

    monkeypatch.setattr(delivery_routes, "supabase", MockSupabase())

    async def fake_compute(src_lng, src_lat, dests):
        return ({"r1": 150}, {"r1": 30})

    monkeypatch.setattr(
        delivery_routes, "_compute_distances_and_durations", fake_compute
    )

    resp = client.get(
        "/api/deliveries/ready", params={"latitude": 37, "longitude": -122}
    )
    assert resp.status_code == 200
    data = resp.json()

                assert len(data) == 1
                assert data[0]["order_id"] == "1"
                assert data[0]["distance_to_restaurant"] == 150
                assert data[0]["duration_to_restaurant"] == 30
