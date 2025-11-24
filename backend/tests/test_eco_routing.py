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
