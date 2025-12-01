import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app


client = TestClient(app)


sample_row = {
    "item_id": 1,
    "restaurant_id": 1,
    "item_name": "Test Item",
    "description": "Tasty",
    "is_available": True,
    "image": None,
    "price": 10.0,
    "quantity": 5,
    "reorder_threshold": 10,
    "reorder_quantity": 20,
    "lead_time_days": 3,
    "is_promo": False,
    "promo_note": None,
    "last_sales_7d": 1,
    "last_sales_30d": 2,
    "created_at": None,
    "updated_at": None,
}


@pytest.fixture
def mock_supabase():
    # Ensure the global supabase in the module is reset so our patched
    # create_supabase_client is used.
    with patch("routes.inventory_routes.supabase", None), patch(
        "routes.inventory_routes.create_supabase_client"
    ) as mock_create:
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[sample_row])
        mock_client.from_.return_value = mock_table
        mock_create.return_value = mock_client
        yield mock_client


def test_get_inventory_status_success(mock_supabase):
    response = client.get("/api/ai/inventory/status")
    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["item_name"] == "Test Item"
    assert data["low_stock_items"][0]["shortage"] == 5


@patch("routes.inventory_routes.InventoryLLMAdvisor")
def test_inventory_analysis_success(mock_advisor_cls, mock_supabase):
    mock_advisor = MagicMock()
    mock_advisor.generate_analysis.return_value = "Analysis text"
    mock_advisor_cls.return_value = mock_advisor

    response = client.post("/api/ai/inventory/analysis", json={})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["analysis"] == "Analysis text"


@patch("routes.inventory_routes.InventoryLLMAdvisor")
def test_inventory_refill_plan_success(mock_advisor_cls, mock_supabase):
    mock_advisor = MagicMock()
    mock_advisor.generate_refill_plan.return_value = "Plan text"
    mock_advisor_cls.return_value = mock_advisor

    response = client.post("/api/ai/inventory/refill-plan", json={})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["plan"] == "Plan text"


@patch("routes.inventory_routes.InventoryLLMAdvisor")
def test_inventory_promo_suggestions_success(mock_advisor_cls, mock_supabase):
    mock_advisor = MagicMock()
    mock_advisor.generate_promo_suggestions.return_value = "Promo text"
    mock_advisor_cls.return_value = mock_advisor

    response = client.post("/api/ai/inventory/promo-suggestions", json={})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["suggestions"] == "Promo text"


@patch("routes.inventory_routes.InventoryLLMAdvisor", side_effect=ValueError("Missing key"))
def test_inventory_analysis_missing_key(mock_advisor_cls, mock_supabase):
    response = client.post("/api/ai/inventory/analysis", json={})
    assert response.status_code == 503
    assert "Missing key" in response.json()["detail"]


@patch("routes.inventory_routes.InventoryLLMAdvisor", side_effect=ValueError("Missing key"))
def test_inventory_refill_missing_key(mock_advisor_cls, mock_supabase):
    response = client.post("/api/ai/inventory/refill-plan", json={})
    assert response.status_code == 503


@patch("routes.inventory_routes.InventoryLLMAdvisor", side_effect=ValueError("Missing key"))
def test_inventory_promo_missing_key(mock_advisor_cls, mock_supabase):
    response = client.post("/api/ai/inventory/promo-suggestions", json={})
    assert response.status_code == 503


def test_inventory_status_filters_by_restaurant_id():
    with patch("routes.inventory_routes.supabase", None), patch(
        "routes.inventory_routes.create_supabase_client"
    ) as mock_create:
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[sample_row])
        mock_client.from_.return_value = mock_table
        mock_create.return_value = mock_client

        response = client.get("/api/ai/inventory/status?restaurant_id=1")
        assert response.status_code == 200
        mock_client.from_.assert_called_with("menu_items")
        # ensure eq was used with restaurant_id
        assert any(
            call[0][0] == "restaurant_id" and call[0][1] == 1
            for call in mock_table.eq.call_args_list
        )


