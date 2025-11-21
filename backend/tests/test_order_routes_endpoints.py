import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from routes import order_routes as orr


class MockResponse:
    def __init__(self, data):
        self.data = data


class MockQuery:
    def __init__(self, select_data=None):
        # select_data: list to return for select() -> execute()
        self._select_data = select_data or []
        self._last_update = None
        self._last_insert = None

    def select(self, *args, **kwargs):
        return self

    def eq(self, *args, **kwargs):
        return self

    def order(self, *args, **kwargs):
        return self

    def range(self, *args, **kwargs):
        return self

    def update(self, data):
        self._last_update = data
        return self

    def insert(self, data):
        self._last_insert = data
        return self

    def execute(self):
        # If update was called, return a merged response representing the updated row
        if self._last_update is not None:
            base = self._select_data[0] if self._select_data else {}
            merged = {**base, **self._last_update}
            return MockResponse([merged])
        if self._last_insert is not None:
            return MockResponse([self._last_insert])
        return MockResponse(self._select_data)


def test_list_orders_raises_when_no_client(monkeypatch):
    monkeypatch.setattr(orr, "get_supabase_client", lambda: None)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(orr.list_orders())
    # list_orders wraps internal HTTPExceptions and rethrows as 500
    assert exc.value.status_code == 500


def test_list_orders_success(monkeypatch):
    # return a query that yields two orders
    q = MockQuery(select_data=[{"order_id": "o1"}, {"order_id": "o2"}])
    monkeypatch.setattr(orr, "get_supabase_client", lambda: object())
    monkeypatch.setattr(orr, "_get_db_table", lambda client, name: q)

    res = asyncio.run(orr.list_orders(limit=2, offset=0))
    assert isinstance(res, list)
    assert len(res) == 2


def test_get_order_by_id_not_found(monkeypatch):
    q = MockQuery(select_data=[])
    monkeypatch.setattr(orr, "get_supabase_client", lambda: object())
    monkeypatch.setattr(orr, "_get_db_table", lambda client, name: q)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(orr.get_order_by_id("nope"))
    assert exc.value.status_code == 404


def test_get_order_by_id_success(monkeypatch):
    order = {
        "order_id": "o1",
        "user_id": "u1",
        "restaurant_id": 1,
        "order_items": [
            {
                "item_id": 1,
                "item_name": "X",
                "price": 2.5,
                "quantity": 2,
                "subtotal": 5.0,
            }
        ],
        "delivery_address": {
            "street": "s",
            "city": "c",
            "state": "ST",
            "zip_code": "12345",
        },
        "subtotal": 5.0,
        "tax_amount": 0.5,
        "delivery_fee": 0,
        "tip_amount": 0,
        "discount_amount": 0,
        "total_amount": 5.5,
    }
    q = MockQuery(select_data=[order])
    monkeypatch.setattr(orr, "get_supabase_client", lambda: object())
    monkeypatch.setattr(orr, "_get_db_table", lambda client, name: q)

    res = asyncio.run(orr.get_order_by_id("o1"))
    # should return an Order model instance (pydantic) with order_id
    assert getattr(res, "order_id") == "o1"


def test_update_order_status_not_found(monkeypatch):
    q = MockQuery(select_data=[])
    monkeypatch.setattr(orr, "get_supabase_client", lambda: object())
    monkeypatch.setattr(orr, "_get_db_table", lambda client, name: q)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(orr.update_order_status("x", orr.OrderStatus.CONFIRMED))
    assert exc.value.status_code == 404


def test_update_order_status_success(monkeypatch):
    existing = {
        "order_id": "x",
        "user_id": "u1",
        "restaurant_id": 1,
        "order_items": [
            {
                "item_id": 1,
                "item_name": "X",
                "price": 2.5,
                "quantity": 2,
                "subtotal": 5.0,
            }
        ],
        "delivery_address": {
            "street": "s",
            "city": "c",
            "state": "ST",
            "zip_code": "12345",
        },
        "subtotal": 5.0,
        "tax_amount": 0,
        "delivery_fee": 0,
        "tip_amount": 0,
        "discount_amount": 0,
        "total_amount": 5.0,
        "status": orr.OrderStatus.CONFIRMED.value,
    }
    q = MockQuery(select_data=[existing])
    monkeypatch.setattr(orr, "get_supabase_client", lambda: object())
    monkeypatch.setattr(orr, "_get_db_table", lambda client, name: q)
    # avoid running sanitization logic here (already validated data); return a sanitized record
    sanitized_result = {**existing, "status": orr.OrderStatus.PICKED_UP.value}
    monkeypatch.setattr(orr, "_sanitize_order_record", lambda o: sanitized_result)

    res = asyncio.run(orr.update_order_status("x", orr.OrderStatus.PICKED_UP))
    assert getattr(res, "order_id") == "x"
    assert getattr(res, "status") == orr.OrderStatus.PICKED_UP.value


def test_assign_delivery_user_bad_status(monkeypatch):
    existing = {"order_id": "a1", "status": orr.OrderStatus.PENDING.value}
    q = MockQuery(select_data=[existing])
    monkeypatch.setattr(orr, "get_supabase_client", lambda: object())
    monkeypatch.setattr(orr, "_get_db_table", lambda client, name: q)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(orr.assign_delivery_user("a1", "du1"))
    assert exc.value.status_code == 400


def test_cancel_order_success(monkeypatch):
    existing = {"order_id": "c1", "status": orr.OrderStatus.CONFIRMED.value}
    q = MockQuery(select_data=[existing])
    monkeypatch.setattr(orr, "get_supabase_client", lambda: object())
    monkeypatch.setattr(orr, "_get_db_table", lambda client, name: q)

    res = asyncio.run(orr.cancel_order("c1"))
    assert isinstance(res, dict)
    assert res["order_id"] == "c1"
    assert res["message"] == "Order cancelled successfully"


def test_cancel_order_cannot_cancel_delivered(monkeypatch):
    existing = {"order_id": "c2", "status": orr.OrderStatus.DELIVERED.value}
    q = MockQuery(select_data=[existing])
    monkeypatch.setattr(orr, "get_supabase_client", lambda: object())
    monkeypatch.setattr(orr, "_get_db_table", lambda client, name: q)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(orr.cancel_order("c2"))
    assert exc.value.status_code == 400


# Test loyalty points calculation through the verify_delivery_code endpoint
def test_verify_delivery_code_awards_loyalty_points_to_delivery_person(monkeypatch):
    """Test that delivery verification awards loyalty points to delivery person"""
    order_data = {
        "order_id": "test123",
        "status": orr.OrderStatus.PICKED_UP.value,
        "delivery_code": "123456",
        "delivery_user_id": "delivery_user_123",
        "total_amount": 50.0,  # Should award 5000 points (50 * 100)
        "delivery_code_used": False,
        "user_id": "customer123",
        "restaurant_id": 1,
        "order_items": [],
        "delivery_address": {},
    }

    mock_supabase = MagicMock()

    # Mock existing order response
    mock_existing_response = MagicMock()
    mock_existing_response.data = [order_data]

    # Mock update response
    mock_update_response = MagicMock()
    mock_update_response.data = [
        {
            **order_data,
            "status": orr.OrderStatus.DELIVERED.value,
            "delivery_code_used": True,
        }
    ]

    # Mock refetch response
    mock_refetch_response = MagicMock()
    mock_refetch_response.data = [
        {
            **order_data,
            "status": orr.OrderStatus.DELIVERED.value,
            "delivery_code_used": True,
        }
    ]

    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
        mock_existing_response,  # First call for existing order
        mock_refetch_response,  # Second call after update
    ]
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = (
        mock_update_response
    )

    # Mock the normalization function
    monkeypatch.setattr(
        orr, "_normalize_single_order", AsyncMock(return_value=order_data)
    )

    # Mock the loyalty points update to capture the call
    mock_loyalty_update = MagicMock()
    monkeypatch.setattr(orr, "update_loyalty_points", mock_loyalty_update)

    # Call the endpoint
    payload = {"delivery_code": "123456"}
    result = asyncio.run(orr.verify_delivery_code("test123", payload, mock_supabase))

    # Verify loyalty points were awarded to the delivery person with correct amount
    mock_loyalty_update.assert_called_once()
    call_args = mock_loyalty_update.call_args[0]
    assert call_args[1] == "delivery_user_123"  # delivery user ID
    assert call_args[2] == 5000  # 50 dollars * 100 points
    assert call_args[3] == "test123"  # order ID


def test_verify_delivery_code_no_loyalty_points_when_no_delivery_user(monkeypatch):
    """Test that no loyalty points are awarded when no delivery user is assigned"""
    order_data = {
        "order_id": "test123",
        "status": orr.OrderStatus.PICKED_UP.value,
        "delivery_code": "123456",
        "delivery_user_id": None,  # No delivery user assigned
        "total_amount": 50.0,
        "delivery_code_used": False,
        "user_id": "customer123",
        "restaurant_id": 1,
        "order_items": [],
        "delivery_address": {},
    }

    mock_supabase = MagicMock()
    mock_existing_response = MagicMock()
    mock_existing_response.data = [order_data]
    mock_update_response = MagicMock()
    mock_update_response.data = [
        {
            **order_data,
            "status": orr.OrderStatus.DELIVERED.value,
            "delivery_code_used": True,
        }
    ]
    mock_refetch_response = MagicMock()
    mock_refetch_response.data = [
        {
            **order_data,
            "status": orr.OrderStatus.DELIVERED.value,
            "delivery_code_used": True,
        }
    ]

    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
        mock_existing_response,
        mock_refetch_response,
    ]
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = (
        mock_update_response
    )

    monkeypatch.setattr(
        orr, "_normalize_single_order", AsyncMock(return_value=order_data)
    )

    # Mock the loyalty points update to verify it's NOT called
    mock_loyalty_update = MagicMock()
    monkeypatch.setattr(orr, "update_loyalty_points", mock_loyalty_update)

    # Call the endpoint
    payload = {"delivery_code": "123456"}
    result = asyncio.run(orr.verify_delivery_code("test123", payload, mock_supabase))

    # Verify no loyalty points were awarded
    mock_loyalty_update.assert_not_called()


def test_verify_delivery_code_loyalty_points_calculation_various_amounts(monkeypatch):
    """Test loyalty points calculation for different order amounts through the endpoint"""
    test_cases = [
        (25.0, 2500),  # 25 dollars = 2500 points
        (100.0, 10000),  # 100 dollars = 10000 points
        (0.99, 0),  # Less than 1 dollar = 0 points
        (1.0, 100),  # Exactly 1 dollar = 100 points
        (25.99, 2500),  # Floors to 25 dollars = 2500 points
    ]

    for total_amount, expected_points in test_cases:
        order_data = {
            "order_id": "test123",
            "status": orr.OrderStatus.PICKED_UP.value,
            "delivery_code": "123456",
            "delivery_user_id": "delivery_user_123",
            "total_amount": total_amount,
            "delivery_code_used": False,
            "user_id": "customer123",
            "restaurant_id": 1,
            "order_items": [],
            "delivery_address": {},
        }

        mock_supabase = MagicMock()
        mock_existing_response = MagicMock()
        mock_existing_response.data = [order_data]
        mock_update_response = MagicMock()
        mock_update_response.data = [
            {
                **order_data,
                "status": orr.OrderStatus.DELIVERED.value,
                "delivery_code_used": True,
            }
        ]
        mock_refetch_response = MagicMock()
        mock_refetch_response.data = [
            {
                **order_data,
                "status": orr.OrderStatus.DELIVERED.value,
                "delivery_code_used": True,
            }
        ]

        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            mock_existing_response,
            mock_refetch_response,
        ]
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = (
            mock_update_response
        )

        monkeypatch.setattr(
            orr, "_normalize_single_order", AsyncMock(return_value=order_data)
        )

        mock_loyalty_update = MagicMock()
        monkeypatch.setattr(orr, "update_loyalty_points", mock_loyalty_update)

        # Call the endpoint
        payload = {"delivery_code": "123456"}
        result = asyncio.run(
            orr.verify_delivery_code("test123", payload, mock_supabase)
        )

        # Verify correct points calculation
        mock_loyalty_update.assert_called()
        call_args = mock_loyalty_update.call_args[0]
        assert (
            call_args[2] == expected_points
        ), f"Failed for amount {total_amount}: expected {expected_points}, got {call_args[2]}"

        # Reset mock for next test case
        mock_loyalty_update.reset_mock()


# Test that the loyalty system integrates properly with the order delivery flow
def test_complete_delivery_flow_includes_loyalty_points(monkeypatch):
    """Test the complete delivery verification flow includes loyalty points awarding"""

    delivery_user_id = "delivery_user_999"
    order_id = "order_999"

    order_data = {
        "order_id": order_id,
        "status": orr.OrderStatus.PICKED_UP.value,
        "delivery_code": "999999",
        "delivery_user_id": delivery_user_id,
        "total_amount": 75.50,  # Should award 7500 points
        "delivery_code_used": False,
        "user_id": "customer123",
        "restaurant_id": 1,
        "order_items": [],
        "delivery_address": {},
    }

    mock_supabase = MagicMock()

    # Mock database responses
    mock_existing_response = MagicMock()
    mock_existing_response.data = [order_data]

    mock_update_response = MagicMock()
    mock_update_response.data = [
        {
            **order_data,
            "status": orr.OrderStatus.DELIVERED.value,
            "delivery_code_used": True,
        }
    ]

    mock_refetch_response = MagicMock()
    mock_refetch_response.data = [
        {
            **order_data,
            "status": orr.OrderStatus.DELIVERED.value,
            "delivery_code_used": True,
        }
    ]

    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
        mock_existing_response,
        mock_refetch_response,
    ]
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = (
        mock_update_response
    )

    # Mock normalization
    monkeypatch.setattr(
        orr, "_normalize_single_order", AsyncMock(return_value=order_data)
    )

    # Capture loyalty points update
    loyalty_calls = []

    def capture_loyalty_update(supabase, user_id, points, order_id_arg):
        loyalty_calls.append(
            {"user_id": user_id, "points": points, "order_id": order_id_arg}
        )

    monkeypatch.setattr(orr, "update_loyalty_points", capture_loyalty_update)

    # Execute delivery verification
    payload = {"delivery_code": "999999"}
    result = asyncio.run(orr.verify_delivery_code(order_id, payload, mock_supabase))

    # Verify the complete flow
    assert len(loyalty_calls) == 1
    assert loyalty_calls[0]["user_id"] == delivery_user_id
    assert loyalty_calls[0]["points"] == 7500  # 75 dollars * 100 points
    assert loyalty_calls[0]["order_id"] == order_id

    # Verify order status was updated to DELIVERED
    assert mock_supabase.table.return_value.update.called


def test_verify_delivery_fails_when_loyalty_update_fails(monkeypatch):
    """Test that delivery verification fails when loyalty points update fails"""
    order_data = {
        "order_id": "test123",
        "status": orr.OrderStatus.PICKED_UP.value,
        "delivery_code": "123456",
        "delivery_user_id": "delivery_user_123",
        "total_amount": 50.0,
        "delivery_code_used": False,
        "user_id": "customer123",
        "restaurant_id": 1,
        "order_items": [],
        "delivery_address": {},
    }

    mock_supabase = MagicMock()
    mock_existing_response = MagicMock()
    mock_existing_response.data = [order_data]
    mock_update_response = MagicMock()
    mock_update_response.data = [
        {
            **order_data,
            "status": orr.OrderStatus.DELIVERED.value,
            "delivery_code_used": True,
        }
    ]
    mock_refetch_response = MagicMock()
    mock_refetch_response.data = [
        {
            **order_data,
            "status": orr.OrderStatus.DELIVERED.value,
            "delivery_code_used": True,
        }
    ]

    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
        mock_existing_response,
        mock_refetch_response,
    ]
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = (
        mock_update_response
    )

    monkeypatch.setattr(
        orr, "_normalize_single_order", AsyncMock(return_value=order_data)
    )

    # Mock loyalty points to raise an exception
    def failing_loyalty_update(supabase, user_id, points, order_id):
        raise Exception("Loyalty system temporarily unavailable")

    monkeypatch.setattr(orr, "update_loyalty_points", failing_loyalty_update)

    # Call should fail with HTTPException when loyalty system is down
    payload = {"delivery_code": "123456"}
    with pytest.raises(HTTPException) as exc:
        asyncio.run(orr.verify_delivery_code("test123", payload, mock_supabase))

    # Verify it's a 500 error
    assert exc.value.status_code == 500
    assert "Loyalty system temporarily unavailable" in str(exc.value.detail)
