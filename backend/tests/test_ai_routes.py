# backend/tests/test_ai_routes.py
import uuid
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


# ============ FIXTURES ============


@pytest.fixture
def mock_recommender():
    """Mock the get_recommender function to return a mock recommender"""
    with patch("routes.ai_routes.get_recommender") as mock_get:
        instance = Mock()
        instance.get_recommendations.return_value = (
            "Here are some great Italian restaurants downtown with vegetarian options!"
        )
        mock_get.return_value = instance
        yield instance


@pytest.fixture
def mock_recommender_none():
    """Mock get_recommender to return None (not configured)"""
    with patch("routes.ai_routes.get_recommender", return_value=None):
        yield


@pytest.fixture
def mock_chatbot():
    """Mock ConversationalRestaurantBot"""
    with patch("routes.ai_routes.ConversationalRestaurantBot") as mock:
        instance = Mock()
        instance.chat.return_value = "I'd be happy to help you find a restaurant!"
        instance.reset.return_value = None
        mock.return_value = instance
        yield instance


@pytest.fixture
def clear_sessions():
    """Clear chatbot sessions before and after each test"""
    import routes.ai_routes as ai_routes

    ai_routes.chatbot_sessions.clear()
    # Also reset the global recommender
    ai_routes.recommender = None
    yield
    ai_routes.chatbot_sessions.clear()
    ai_routes.recommender = None


# ============ RECOMMENDATION ENDPOINT TESTS ============


def test_get_recommendations_success(mock_recommender, clear_sessions):
    """Test successful recommendation request"""
    response = client.post(
        "/api/ai/recommendations", json={"query": "I want Italian food downtown"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Italian" in data["recommendation"]
    mock_recommender.get_recommendations.assert_called_once_with(
        "I want Italian food downtown"
    )


def test_get_recommendations_empty_query(mock_recommender, clear_sessions):
    """Test recommendation with empty query"""
    response = client.post("/api/ai/recommendations", json={"query": ""})

    assert response.status_code == 200
    # Should still call the function even with empty query
    mock_recommender.get_recommendations.assert_called_once_with("")


def test_get_recommendations_missing_query():
    """Test recommendation without query field"""
    response = client.post("/api/ai/recommendations", json={})

    assert response.status_code == 422  # Validation error


def test_get_recommendations_recommender_not_configured(
    mock_recommender_none, clear_sessions
):
    """Test when recommender initialization fails"""
    response = client.post(
        "/api/ai/recommendations", json={"query": "I want Italian food"}
    )

    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]


def test_get_recommendations_error(mock_recommender, clear_sessions):
    """Test when recommender throws an error"""
    # Make the mock raise an exception
    mock_recommender.get_recommendations.side_effect = Exception("API Error")

    response = client.post(
        "/api/ai/recommendations", json={"query": "I want Italian food"}
    )

    assert response.status_code == 500
    assert "Failed to get recommendations" in response.json()["detail"]


# ============ CHATBOT ENDPOINT TESTS ============


def test_chat_new_session(mock_chatbot, clear_sessions):
    """Test starting a new chat session"""
    response = client.post(
        "/api/ai/chat", json={"message": "I'm looking for dinner", "session_id": None}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "session_id" in data
    assert len(data["session_id"]) > 0  # UUID should be generated
    assert data["response"] == "I'd be happy to help you find a restaurant!"
    mock_chatbot.chat.assert_called_once_with("I'm looking for dinner")


def test_chat_existing_session(mock_chatbot, clear_sessions):
    """Test continuing an existing chat session"""
    # First message to create session
    response1 = client.post(
        "/api/ai/chat", json={"message": "I want Italian food", "session_id": None}
    )
    session_id = response1.json()["session_id"]

    # Second message with same session
    mock_chatbot.chat.return_value = "Great choice! Here are some Italian restaurants."
    response2 = client.post(
        "/api/ai/chat",
        json={"message": "What about downtown?", "session_id": session_id},
    )

    assert response2.status_code == 200
    data = response2.json()
    assert data["session_id"] == session_id  # Same session ID
    assert "Italian restaurants" in data["response"]


def test_chat_with_custom_session_id(mock_chatbot, clear_sessions):
    """Test providing your own session ID"""
    custom_session_id = str(uuid.uuid4())

    response = client.post(
        "/api/ai/chat", json={"message": "Hello", "session_id": custom_session_id}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == custom_session_id


def test_chat_missing_message():
    """Test chat without message field"""
    response = client.post("/api/ai/chat", json={"session_id": "test-session"})

    assert response.status_code == 422  # Validation error


def test_chat_initialization_error(clear_sessions):
    """Test when chatbot initialization fails"""
    with patch("routes.ai_routes.ConversationalRestaurantBot") as mock:
        mock.side_effect = Exception("Failed to initialize")

        response = client.post(
            "/api/ai/chat", json={"message": "Hello", "session_id": None}
        )

        assert response.status_code == 503
        assert "Failed to initialize chatbot" in response.json()["detail"]


def test_chat_runtime_error(mock_chatbot, clear_sessions):
    """Test when chat throws an error"""
    mock_chatbot.chat.side_effect = Exception("Chat error")

    response = client.post(
        "/api/ai/chat", json={"message": "Hello", "session_id": None}
    )

    assert response.status_code == 500
    assert "Chat error" in response.json()["detail"]


# ============ CHAT RESET TESTS ============


def test_reset_chat_success(mock_chatbot, clear_sessions):
    """Test resetting an existing chat session"""
    # Create a session first
    response1 = client.post(
        "/api/ai/chat", json={"message": "Hello", "session_id": None}
    )
    session_id = response1.json()["session_id"]

    # Reset the session
    response2 = client.post("/api/ai/chat/reset", json={"session_id": session_id})

    assert response2.status_code == 200
    data = response2.json()
    assert data["success"] is True
    assert data["session_id"] == session_id
    mock_chatbot.reset.assert_called_once()


def test_reset_chat_nonexistent_session(clear_sessions):
    """Test resetting a session that doesn't exist"""
    response = client.post(
        "/api/ai/chat/reset", json={"session_id": "nonexistent-session-id"}
    )

    assert response.status_code == 404
    assert "Session not found" in response.json()["detail"]


def test_reset_chat_missing_session_id():
    """Test reset without session_id"""
    response = client.post("/api/ai/chat/reset", json={})

    assert response.status_code == 422  # Validation error


# ============ DELETE SESSION TESTS ============


def test_delete_session_success(mock_chatbot, clear_sessions):
    """Test deleting an existing session"""
    # Create a session
    response1 = client.post(
        "/api/ai/chat", json={"message": "Hello", "session_id": None}
    )
    session_id = response1.json()["session_id"]

    # Delete the session
    response2 = client.delete(f"/api/ai/chat/{session_id}")

    assert response2.status_code == 200
    data = response2.json()
    assert data["success"] is True
    assert "deleted" in data["message"]


def test_delete_session_nonexistent(clear_sessions):
    """Test deleting a session that doesn't exist"""
    response = client.delete("/api/ai/chat/nonexistent-session-id")

    assert response.status_code == 404
    assert "Session not found" in response.json()["detail"]


# ============ LIST SESSIONS TESTS ============


def test_list_sessions_empty(clear_sessions):
    """Test listing sessions when none exist"""
    response = client.get("/api/ai/chat/sessions")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["count"] == 0
    assert data["active_sessions"] == []


def test_list_sessions_with_active_sessions(mock_chatbot, clear_sessions):
    """Test listing sessions when some exist"""
    # Create 3 sessions
    session_ids = []
    for i in range(3):
        response = client.post(
            "/api/ai/chat", json={"message": f"Hello {i}", "session_id": None}
        )
        session_ids.append(response.json()["session_id"])

    # List sessions
    response = client.get("/api/ai/chat/sessions")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["count"] == 3
    assert set(data["active_sessions"]) == set(session_ids)


# ============ INTEGRATION TESTS ============


def test_full_conversation_flow(mock_chatbot, clear_sessions):
    """Test a complete conversation flow"""
    mock_chatbot.chat.side_effect = [
        "I'd be happy to help! What type of cuisine are you interested in?",
        "Great! I found some Italian restaurants for you.",
        "Here are the restaurants sorted by rating.",
    ]

    # Start conversation
    response1 = client.post(
        "/api/ai/chat", json={"message": "I'm hungry", "session_id": None}
    )
    session_id = response1.json()["session_id"]

    # Continue conversation
    response2 = client.post(
        "/api/ai/chat", json={"message": "Italian food", "session_id": session_id}
    )

    response3 = client.post(
        "/api/ai/chat",
        json={"message": "Show me the best ones", "session_id": session_id},
    )

    # Verify all responses used same session
    assert response1.json()["session_id"] == session_id
    assert response2.json()["session_id"] == session_id
    assert response3.json()["session_id"] == session_id

    # Verify chat was called 3 times
    assert mock_chatbot.chat.call_count == 3


def test_session_isolation(mock_chatbot, clear_sessions):
    """Test that different sessions are isolated"""
    # Create two separate sessions
    response1 = client.post(
        "/api/ai/chat", json={"message": "Session 1", "session_id": None}
    )
    session1_id = response1.json()["session_id"]

    response2 = client.post(
        "/api/ai/chat", json={"message": "Session 2", "session_id": None}
    )
    session2_id = response2.json()["session_id"]

    # Verify they're different
    assert session1_id != session2_id

    # List sessions - should have 2
    response = client.get("/api/ai/chat/sessions")
    assert response.json()["count"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
