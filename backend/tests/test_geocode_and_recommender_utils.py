import pytest

from utils import geocode as geocode_mod
from utils import restaurant_recommender as rr


class _FakeResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        return None

    def json(self):
        return self._data


class _FakeAsyncClient:
    def __init__(self, resp):
        self._resp = resp

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None):
        return self._resp


@pytest.mark.asyncio
async def test_geocode_invalid_input():
    lat, lng = await geocode_mod.geocode_address(123)
    assert lat is None and lng is None


@pytest.mark.asyncio
async def test_geocode_no_token(monkeypatch):
    # Ensure module thinks there's no token
    monkeypatch.setattr(geocode_mod, "MAPBOX_TOKEN", None)
    lat, lng = await geocode_mod.geocode_address("Some address")
    assert lat is None and lng is None


@pytest.mark.asyncio
async def test_geocode_mapbox_success(monkeypatch):
    # Simulate Mapbox returning a valid feature with center [lng, lat]
    fake_data = {"features": [{"center": [-122.431297, 37.773972]}]}
    fake_resp = _FakeResponse(fake_data)
    fake_client = _FakeAsyncClient(fake_resp)

    monkeypatch.setattr(geocode_mod, "MAPBOX_TOKEN", "fake-token")
    monkeypatch.setattr("httpx.AsyncClient", lambda timeout=10.0: fake_client)

    lat, lng = await geocode_mod.geocode_address("San Francisco, CA")
    assert pytest.approx(lat, rel=1e-3) == 37.773972
    assert pytest.approx(lng, rel=1e-3) == -122.431297


def test_haversine_zero_and_none():
    # same point -> near zero
    m = rr.haversine_meters(37.0, -122.0, 37.0, -122.0)
    assert pytest.approx(m, abs=0.1) == 0.0

    # None input yields None
    assert rr.haversine_meters(None, -122.0, 37.0, -122.0) is None


def test_cluster_orders_basic():
    # Create three orders: two close restaurants/customers should cluster
    orders = [
        {
            "order_id": "o1",
            "restaurants": {"latitude": 37.0, "longitude": -122.0},
            "latitude": 37.001,
            "longitude": -122.001,
        },
        {
            "order_id": "o2",
            "restaurants": {"latitude": 37.0005, "longitude": -122.0005},
            "latitude": 37.0012,
            "longitude": -122.0008,
        },
        {
            "order_id": "o3",
            "restaurants": {"latitude": 38.0, "longitude": -123.0},
            "latitude": 38.0001,
            "longitude": -123.0001,
        },
    ]

    groups = rr.cluster_orders_by_proximity(
        orders, rest_threshold_m=200, cust_threshold_m=500
    )
    # Expect two groups: first with o1 and o2, second with o3
    assert any(len(g) == 2 for g in groups)
    assert any(len(g) == 1 for g in groups)


def test_cluster_orders_missing_coords():
    orders = [
        {"order_id": "o1", "restaurants": {}, "latitude": None, "longitude": None},
        {
            "order_id": "o2",
            "restaurants": {"latitude": "", "longitude": ""},
            "latitude": "",
            "longitude": "",
        },
    ]
    groups = rr.cluster_orders_by_proximity(orders)
    # Missing coords -> each in its own group
    assert all(len(g) == 1 for g in groups)
