from utils.restaurant_recommender import (
    cluster_orders_by_proximity,
    haversine_meters,
)

from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app

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

@pytest.mark.asyncio
async def test_eco_endpoint_no_orders():
    """Should return type=none when no ready orders."""
    with patch("routers.delivery_router.supabase.from_") as mock_from:
        mock_from.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value.data = []

        async with AsyncClient(app=app, base_url="http://test") as ac:
            resp = await ac.get("/deliveries/eco?latitude=37.0&longitude=-122.0")
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

    with patch("routers.delivery_router.supabase.from_") as mock_from:
        mock_from.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value.data = fake_orders

        # Mock distance calculation
        with patch("routers.delivery_router._compute_distances_and_durations") as mock_dist:
            mock_dist.return_value = (
                {"r1": 120},  # distance 120m
                {"r1": 20}    # duration 20s
            )

            async with AsyncClient(app=app, base_url="http://test") as ac:
                resp = await ac.get("/deliveries/eco?latitude=37.0&longitude=-122.0")
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

    with patch("routers.delivery_router.supabase.from_") as mock_from:
        mock_from.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value.data = fake_orders

        with patch("routers.delivery_router._compute_distances_and_durations") as mock_dist:
            mock_dist.return_value = (
                {"r1": 100, "r2": 110},
                {"r1": 20, "r2": 25}
            )

            # Mock grouping
            with patch("routers.delivery_router.cluster_orders_by_proximity") as mock_cluster:
                mock_cluster.return_value = [
                    [fake_orders[0], fake_orders[1]]  # 2 order group
                ]

                async with AsyncClient(app=app, base_url="http://test") as ac:
                    resp = await ac.get("/deliveries/eco?latitude=37.0&longitude=-122.0")
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

    with patch("routers.delivery_router.supabase.from_") as mock_from:
        mock_from.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value.data = fake_orders

        with patch("routers.delivery_router._compute_distances_and_durations") as mock_dist:
            mock_dist.return_value = (
                {"r1": 150},
                {"r1": 30}
            )

            async with AsyncClient(app=app, base_url="http://test") as ac:
                resp = await ac.get("/deliveries/ready?latitude=37&longitude=-122")
                assert resp.status_code == 200
                data = resp.json()

                assert len(data) == 1
                assert data[0]["order_id"] == "1"
                assert data[0]["distance_to_restaurant"] == 150
                assert data[0]["duration_to_restaurant"] == 30
