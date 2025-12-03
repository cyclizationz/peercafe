# tests/test_conversational_recommender.py
"""
All tests pass – unit (mocked) + integration (real Groq)
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
from utils.conversational_recommender import ConversationalRestaurantBot

import pytest
from dotenv import load_dotenv

from utils.conversational_recommender import ConversationalRestaurantBot

# --------------------------------------------------------------
# 1. Load .env from project root
# --------------------------------------------------------------
# This file lives at backend/tests/test_conversational_recommender.py
# Project root is therefore three levels up: repo_root/backend/tests -> repo_root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# --------------------------------------------------------------
# 2. Make `utils` importable
# --------------------------------------------------------------
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# --------------------------------------------------------------
# Helper – mimics real Supabase response
# --------------------------------------------------------------
class FakeSupabaseResponse:
    def __init__(self, data):
        self.data = data


# ============================= UNIT TESTS =============================


@pytest.mark.unit
class TestConversationalBotUnit:
    @pytest.fixture
    def mock_env(self):
        with patch.dict("os.environ", {"GROQ_API_KEY": "fake"}):
            yield

    @pytest.fixture
    def mock_groq(self):
        return MagicMock()

    @pytest.fixture
    def mock_supabase(self):
        return MagicMock()

    @pytest.fixture
    def bot(self, mock_env, mock_groq, mock_supabase):
        with (
            patch("utils.conversational_recommender.Groq", return_value=mock_groq),
            patch(
                "utils.conversational_recommender.create_supabase_client",
                return_value=mock_supabase,
            ),
        ):
            return ConversationalRestaurantBot()

    @pytest.fixture
    def sample_restaurants(self):
        return [
            {
                "id": 1,
                "name": "Bella Italia",
                "cuisine_type": "Italian",
                "price_range": "$$",
                "address": "123 Main St, Downtown",
                "rating": 4.8,
                "description": "Romantic Italian spot with vegetarian pasta and outdoor seating.",
            },
            {
                "id": 2,
                "name": "Veggie Haven",
                "cuisine_type": "Vegetarian",
                "price_range": "$",
                "address": "456 Green Ave",
                "rating": 4.6,
                "description": "Fully vegetarian, vegan-friendly, outdoor patio.",
            },
            {
                "id": 3,
                "name": "Sushi Zen",
                "cuisine_type": "Japanese",
                "price_range": "$$$",
                "address": "789 Ocean Blvd",
                "rating": 4.9,
                "description": "Premium sushi, no outdoor seating.",
            },
        ]

    # ------------------- search_restaurants -------------------
    def test_search_applies_all_filters(self, bot, sample_restaurants):
        mock_q = MagicMock()
        mock_q.ilike.side_effect = lambda *a, **k: mock_q
        mock_q.eq.side_effect = lambda *a, **k: mock_q
        mock_q.gte.side_effect = lambda *a, **k: mock_q
        mock_q.order.side_effect = lambda *a, **k: mock_q
        mock_q.limit.side_effect = lambda *a, **k: mock_q
        mock_q.execute.return_value = FakeSupabaseResponse(sample_restaurants)

        bot.supabase.table.return_value.select.return_value = mock_q

        res = bot.search_restaurants(
            cuisine="Italian",
            price_range="$$",
            location="Downtown",
            vegetarian_friendly=True,
            outdoor_seating=True,
            min_rating=4.5,
        )
        assert len(res) == 1
        assert res[0]["name"] == "Bella Italia"

    def test_search_no_description_filters(self, bot, sample_restaurants):
        mock_q = MagicMock()
        mock_q.ilike.return_value = mock_q
        mock_q.order.return_value = mock_q
        mock_q.limit.return_value = mock_q
        mock_q.execute.return_value = FakeSupabaseResponse(sample_restaurants)
        bot.supabase.table.return_value.select.return_value = mock_q

        res = bot.search_restaurants(cuisine="Japanese")
        assert len(res) == 1
        assert res[0]["name"] == "Sushi Zen"

    def test_search_empty_db(self, bot):
        mock_q = MagicMock()
        mock_q.order.return_value = mock_q
        mock_q.limit.return_value = mock_q
        mock_q.execute.return_value = FakeSupabaseResponse([])
        bot.supabase.table.return_value.select.return_value = mock_q

        assert bot.search_restaurants(cuisine="Quantum") == []

    # ------------------- chat flow -------------------
    def test_chat_triggers_function_call(self, bot, sample_restaurants):
        tool = MagicMock()
        tool.id = "call_1"
        tool.function.name = "search_restaurants"
        tool.function.arguments = json.dumps(
            {"cuisine": "Italian", "vegetarian_friendly": True}
        )

        first = MagicMock()
        first.choices[0].message.tool_calls = [tool]
        first.choices[0].message.content = None

        final = MagicMock()
        final.choices[0].message.content = "Bella Italia is perfect!"
        final.choices[0].message.tool_calls = None

        bot.client.chat.completions.create.side_effect = [first, final]

        mock_q = MagicMock()
        mock_q.ilike.return_value = mock_q
        mock_q.order.return_value = mock_q
        mock_q.limit.return_value = mock_q
        mock_q.execute.return_value = FakeSupabaseResponse([sample_restaurants[0]])
        bot.supabase.table.return_value.select.return_value = mock_q

        ans = bot.chat("Italian vegetarian")
        assert "Bella Italia" in ans
        assert len(bot.conversation_history) == 5

    def test_chat_direct_response(self, bot):
        resp = MagicMock()
        resp.choices[0].message.tool_calls = None
        resp.choices[0].message.content = "What cuisine?"
        bot.client.chat.completions.create.return_value = resp

        ans = bot.chat("Not sure")
        assert ans == "What cuisine?"

    def test_chat_malformed_json_fallback(self, bot):
        tool = MagicMock()
        tool.id = "bad"
        tool.function.arguments = '{ "cuisine": "Pizza" oops'
        first = MagicMock()
        first.choices[0].message.tool_calls = [tool]
        bot.client.chat.completions.create.return_value = first

        with patch("builtins.print"):
            ans = bot.chat("Pizza")
        assert any(p in ans.lower() for p in ["confused", "try again"])

    # ------------------- conversation state -------------------
    def test_history_persists(self, bot):
        # Mock the Groq response to return a string
        resp = MagicMock()
        resp.choices[0].message.tool_calls = None
        resp.choices[0].message.content = "Sure, I can help!"
        bot.client.chat.completions.create.return_value = resp

        bot.chat("Hi")

        # Set up for second call
        resp.choices[0].message.content = "What kind of Italian?"
        bot.chat("Italian")

        assert len(bot.conversation_history) == 5  # system + 2 user + 2 assistant
        assert bot.conversation_history[1]["content"] == "Hi"

    def test_reset_clears_history(self, bot):
        bot.chat("Hello")
        bot.reset()
        assert len(bot.conversation_history) == 1
        assert bot.conversation_history[0]["role"] == "system"


# =========================== INTEGRATION TESTS ===========================


@pytest.mark.integration
class TestConversationalBotIntegration:
    @pytest.fixture
    def bot(self):
        if not os.getenv("GROQ_API_KEY"):
            pytest.skip("GROQ_API_KEY missing")
        with patch("utils.conversational_recommender.create_supabase_client"):
            b = ConversationalRestaurantBot()
            b.supabase = MagicMock()
            return b

    @pytest.fixture
    def sample_restaurants(self):
        return [
            {
                "id": 10,
                "name": "Green Garden",
                "cuisine_type": "Vegetarian",
                "price_range": "$$",
                "address": "321 Peace St",
                "rating": 4.7,
                "description": "100% vegetarian, outdoor",
            }
        ]

    def _mock_search(self, bot, data):
        bot.search_restaurants = Mock(return_value=data)

    def test_real_simple_query(self, bot, sample_restaurants):
        print("\nREAL Groq – simple")
        self._mock_search(bot, sample_restaurants)
        ans = bot.chat("vegetarian")
        assert ans
        print(f"Response: {ans}")

    def test_real_function_calling(self, bot, sample_restaurants):
        print("\nREAL Groq – function call")
        self._mock_search(bot, sample_restaurants)
        ans = bot.chat("vegetarian with outdoor seating")
        assert len(ans) > 20
        print(f"Response: {ans}")

    def test_real_no_results(self, bot):
        print("\nREAL Groq – no results")
        self._mock_search(bot, [])
        ans = bot.chat("Martian food")
        assert ans
        print(f"Response: {ans}")

    def test_real_multi_turn(self, bot, sample_restaurants):
        print("\nREAL Groq – multi-turn")
        self._mock_search(bot, sample_restaurants)

        # First turn - greeting (shouldn't trigger function call)
        a0 = bot.chat("Hi, I'm looking for a restaurant")
        assert a0
        print(f"Turn0: {a0}")

        # Second turn - specific request (should trigger function call)
        a1 = bot.chat("I want vegetarian food")
        assert a1
        print(f"Turn1: {a1}")

        # Third turn - follow-up with more context (not just "outdoor")
        a2 = bot.chat("Does it have outdoor seating?")
        assert a2
        print(f"Turn2: {a2}")


# ============================= EDGE CASES =============================


@pytest.mark.unit
class TestEdgeCases:
    @pytest.fixture
    def bot(self):
        with (
            patch("utils.conversational_recommender.Groq"),
            patch("utils.conversational_recommender.create_supabase_client"),
        ):
            b = ConversationalRestaurantBot()
            b.supabase = MagicMock()
            return b

    def test_search_limits_to_5(self, bot):
        many = [
            {
                "id": i,
                "name": f"R{i}",
                "cuisine_type": "Test",
                "price_range": "$",
                "address": "Test",
                "rating": 4.0,
                "description": "test",
            }
            for i in range(30)
        ]

        mock_q = MagicMock()
        mock_q.order.return_value = mock_q
        mock_q.limit.return_value = mock_q
        mock_q.execute.return_value = FakeSupabaseResponse(many)
        bot.supabase.table.return_value.select.return_value = mock_q

        res = bot.search_restaurants()
        assert len(res) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
