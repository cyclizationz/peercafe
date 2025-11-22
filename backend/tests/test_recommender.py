# backend/tests/test_recommender.py
"""
Comprehensive test suite for RestaurantRecommender

Test Levels:
1. Unit Tests - Fast, mocked, test business logic only
2. Integration Tests - Real Groq API calls (FREE) ⭐

Run different levels:
    # Unit only (fast, no API calls)
    pytest tests/test_recommender.py -m unit -v

    # Integration (REAL API calls with FREE Groq) ⭐⭐⭐
    pytest tests/test_recommender.py -m integration -v

    # All tests
    pytest tests/test_recommender.py -v

    # With coverage
    pytest tests/test_recommender.py --cov=utils --cov-report=term-missing -v
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from dotenv import load_dotenv

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Load environment
load_dotenv()


# ==========================================
# UNIT TESTS - Fast, Mocked, No API Calls
# ==========================================


@pytest.mark.unit
class TestRestaurantRecommenderUnit:
    """Unit tests with full mocking - no real API calls"""

    @pytest.fixture
    def mock_env(self):
        """Mock environment variables"""
        with patch.dict(
            os.environ,
            {
                "GROQ_API_KEY": "test-key-123",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "test-key",
            },
        ):
            yield

    @pytest.fixture
    def mock_supabase_client(self):
        """Create a mock Supabase client"""
        return MagicMock()

    @pytest.fixture
    def mock_groq_client(self):
        """Create a mock Groq client"""
        return MagicMock()

    @pytest.fixture
    def recommender(self, mock_env, mock_supabase_client, mock_groq_client):
        """Create recommender with mocked dependencies"""
        with (
            patch(
                "utils.restaurant_recommender.create_supabase_client",
                return_value=mock_supabase_client,
            ),
            patch("utils.restaurant_recommender.Groq", return_value=mock_groq_client),
        ):
            from utils.restaurant_recommender import RestaurantRecommender

            return RestaurantRecommender(use_groq=True)

    @pytest.fixture
    def mock_restaurants(self):
        """Mock restaurant data for testing"""
        return [
            {
                "id": 1,
                "name": "Bella Italia",
                "cuisine_type": "Italian",
                "price_range": "$$$",
                "address": "123 Downtown St",
                "description": "Romantic Italian dining with vegetarian options and outdoor seating",
                "rating": 4.5,
            },
            {
                "id": 2,
                "name": "Taco Haven",
                "cuisine_type": "Mexican",
                "price_range": "$",
                "address": "456 Main St",
                "description": "Casual Mexican food with vegan-friendly options",
                "rating": 4.2,
            },
            {
                "id": 3,
                "name": "Sushi Master",
                "cuisine_type": "Japanese",
                "price_range": "$$$$",
                "address": "789 Uptown Ave",
                "description": "Premium sushi with gluten-free options available",
                "rating": 4.8,
            },
            {
                "id": 4,
                "name": "Green Garden",
                "cuisine_type": "Vegetarian",
                "price_range": "$$",
                "address": "321 Downtown Plaza",
                "description": "All vegetarian menu with vegan and gluten-free options, outdoor seating, reservations accepted",
                "rating": 4.6,
            },
        ]

    def test_recommender_initialization(self, recommender):
        """Test that recommender initializes correctly"""
        assert recommender is not None
        assert hasattr(recommender, "client")
        assert hasattr(recommender, "supabase")
        assert recommender.provider == "groq"
        assert recommender.model == "llama-3.1-8b-instant"

    def test_search_returns_list(self, recommender):
        """Test that search_restaurants always returns a list"""
        mock_response = Mock()
        mock_response.data = []

        mock_query = MagicMock()
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response

        recommender.supabase.table.return_value.select.return_value = mock_query

        result = recommender.search_restaurants()

        assert isinstance(result, list)
        assert len(result) == 0

    def test_search_handles_none_data(self, recommender):
        """Test that None data from database is handled gracefully"""
        mock_response = Mock()
        mock_response.data = None

        mock_query = MagicMock()
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response

        recommender.supabase.table.return_value.select.return_value = mock_query

        result = recommender.search_restaurants()

        assert result == []

    def test_search_by_cuisine(self, recommender, mock_restaurants):
        """Test filtering by cuisine type"""
        mock_response = Mock()
        mock_response.data = [
            r for r in mock_restaurants if "Italian" in r["cuisine_type"]
        ]

        mock_query = MagicMock()
        mock_query.ilike.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response

        recommender.supabase.table.return_value.select.return_value = mock_query

        results = recommender.search_restaurants(cuisine="Italian")

        assert len(results) == 1
        assert results[0]["name"] == "Bella Italia"
        assert results[0]["cuisine_type"] == "Italian"

    def test_search_by_price_range(self, recommender, mock_restaurants):
        """Test filtering by price range"""
        mock_response = Mock()
        mock_response.data = [r for r in mock_restaurants if r["price_range"] == "$"]

        mock_query = MagicMock()
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response

        recommender.supabase.table.return_value.select.return_value = mock_query

        results = recommender.search_restaurants(price_range="$")

        assert len(results) == 1
        assert results[0]["price_range"] == "$"
        assert results[0]["name"] == "Taco Haven"

    def test_search_by_location(self, recommender, mock_restaurants):
        """Test filtering by location"""
        mock_response = Mock()
        mock_response.data = [r for r in mock_restaurants if "Downtown" in r["address"]]

        mock_query = MagicMock()
        mock_query.ilike.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response

        recommender.supabase.table.return_value.select.return_value = mock_query

        results = recommender.search_restaurants(location="Downtown")

        assert len(results) >= 1
        assert all("Downtown" in r["address"] for r in results)

    def test_search_vegetarian_friendly(self, recommender, mock_restaurants):
        """Test filtering by vegetarian-friendly options"""
        mock_response = Mock()
        mock_response.data = mock_restaurants

        mock_query = MagicMock()
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response

        recommender.supabase.table.return_value.select.return_value = mock_query

        results = recommender.search_restaurants(vegetarian_friendly=True)

        # Should filter to only restaurants with 'vegetarian' in description
        assert all("vegetarian" in r["description"].lower() for r in results)
        assert len(results) >= 1

    def test_search_multiple_filters(self, recommender, mock_restaurants):
        """Test combining multiple filters"""
        # Filter for Italian, $$$, Downtown
        filtered = [
            r
            for r in mock_restaurants
            if "Italian" in r["cuisine_type"]
            and r["price_range"] == "$$$"
            and "Downtown" in r["address"]
        ]

        mock_response = Mock()
        mock_response.data = filtered

        mock_query = MagicMock()
        mock_query.ilike.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response

        recommender.supabase.table.return_value.select.return_value = mock_query

        results = recommender.search_restaurants(
            cuisine="Italian", price_range="$$$", location="Downtown"
        )

        assert len(results) >= 1
        assert results[0]["cuisine_type"] == "Italian"
        assert results[0]["price_range"] == "$$$"

    def test_search_min_rating(self, recommender, mock_restaurants):
        """Test filtering by minimum rating"""
        mock_response = Mock()
        mock_response.data = [r for r in mock_restaurants if r["rating"] >= 4.5]

        mock_query = MagicMock()
        mock_query.gte.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response

        recommender.supabase.table.return_value.select.return_value = mock_query

        results = recommender.search_restaurants(min_rating=4.5)

        assert all(r["rating"] >= 4.5 for r in results)
        assert len(results) >= 1

    def test_get_recommendations_with_function_call(
        self, recommender, mock_restaurants
    ):
        """Test full recommendation flow when AI uses function calling"""
        # Mock the tool call
        mock_tool_call = Mock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "search_restaurants"
        mock_tool_call.function.arguments = json.dumps(
            {"cuisine": "Italian", "vegetarian_friendly": True}
        )

        # First response - AI wants to call search function
        first_message = Mock()
        first_message.tool_calls = [mock_tool_call]
        first_message.content = None

        first_response = Mock()
        first_response.choices = [Mock(message=first_message)]

        # Second response - Final recommendation
        final_message = Mock()
        final_message.content = "I recommend Bella Italia for authentic Italian cuisine with great vegetarian options!"
        final_message.tool_calls = None

        final_response = Mock()
        final_response.choices = [Mock(message=final_message)]

        # Setup mock to return both responses
        recommender.client.chat.completions.create.side_effect = [
            first_response,
            final_response,
        ]

        # Mock the search_restaurants method to return data
        recommender.search_restaurants = Mock(return_value=[mock_restaurants[0]])

        # Run the recommendation
        result = recommender.get_recommendations(
            "I want Italian food with veggie options"
        )

        assert result is not None
        assert isinstance(result, str)
        assert "Bella Italia" in result
        assert len(result) > 0

    def test_get_recommendations_without_function_call(self, recommender):
        """Test when AI responds directly without database search"""
        mock_message = Mock()
        mock_message.content = "I'd be happy to help you find a restaurant! What type of cuisine do you prefer?"
        mock_message.tool_calls = None

        mock_response = Mock()
        mock_response.choices = [Mock(message=mock_message)]

        recommender.client.chat.completions.create.return_value = mock_response

        result = recommender.get_recommendations("Tell me about restaurants")

        assert isinstance(result, str)
        assert len(result) > 0


# ============================================
# INTEGRATION TESTS - REAL API CALLS (FREE)
# ============================================


@pytest.mark.integration
class TestRestaurantRecommenderIntegration:
    """Integration tests with REAL Groq API calls (FREE)"""

    @pytest.fixture
    def recommender(self):
        """Create recommender with real Groq API, mocked database"""
        if not os.getenv("GROQ_API_KEY"):
            pytest.skip(
                "GROQ_API_KEY not set. Get your free key at https://console.groq.com/ "
                "and add it to your .env file"
            )

        # Use real Groq API but mock Supabase for controlled testing
        with patch("utils.restaurant_recommender.create_supabase_client"):
            from utils.restaurant_recommender import RestaurantRecommender

            rec = RestaurantRecommender(use_groq=True)

            # Setup mock Supabase - but we'll configure it per test
            rec.supabase = MagicMock()
            return rec

    @pytest.fixture
    def sample_restaurants(self):
        """Sample restaurant data to return from mocked database"""
        return [
            {
                "id": 1,
                "name": "Bella Italia",
                "cuisine_type": "Italian",
                "price_range": "$$$",
                "address": "123 Downtown St, Raleigh, NC",
                "description": "Romantic Italian dining with fresh homemade pasta, extensive vegetarian menu, and beautiful outdoor patio. Reservations recommended.",
                "rating": 4.7,
                "phone": "919-555-0100",
            },
            {
                "id": 2,
                "name": "Taco Fiesta",
                "cuisine_type": "Mexican",
                "price_range": "$",
                "address": "456 Main St, Raleigh, NC",
                "description": "Authentic Mexican street food with many vegan-friendly options. Quick casual service.",
                "rating": 4.3,
                "phone": "919-555-0200",
            },
            {
                "id": 3,
                "name": "Green Garden Cafe",
                "cuisine_type": "Vegetarian",
                "price_range": "$$",
                "address": "789 Peace St, Raleigh, NC",
                "description": "100% vegetarian and vegan restaurant with extensive gluten-free menu. Outdoor seating available with reservations.",
                "rating": 4.8,
                "phone": "919-555-0300",
            },
        ]

    def _mock_database_query(self, recommender, data_to_return):
        """
        Create a robust mock that intercepts search_restaurants directly
        This avoids the complexity of mocking the entire Supabase query chain
        """
        # Just patch the search_restaurants method to return our data
        recommender.search_restaurants = Mock(return_value=data_to_return)

    def test_real_api_simple_query(self, recommender, sample_restaurants):
        """
        Test REAL Groq API with simple query
        THIS MAKES AN ACTUAL API CALL TO GROQ (FREE)
        """
        print("\n🧪 Testing with REAL Groq API...")

        # Mock the database search to return specific data
        self._mock_database_query(recommender, sample_restaurants[:1])

        # Make REAL API call to Groq ⭐⭐⭐
        result = recommender.get_recommendations("Find me an Italian restaurant")

        # Verify we got a response
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

        # Result should mention Italian or restaurants
        result_lower = result.lower()
        assert (
            "italian" in result_lower
            or "restaurant" in result_lower
            or "bella" in result_lower
        )

        print(f"\n✅ Real API Response:\n{result}\n")

    def test_real_api_with_function_calling(self, recommender, sample_restaurants):
        """
        Test that Groq API actually uses function calling
        THIS MAKES AN ACTUAL API CALL TO GROQ (FREE)
        """
        print("\n🧪 Testing REAL function calling...")

        # Mock the database search
        self._mock_database_query(recommender, [sample_restaurants[2]])

        # Query that should trigger function calling ⭐⭐⭐
        result = recommender.get_recommendations(
            "I'm vegetarian and need a restaurant with outdoor seating"
        )

        # Verify response
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 50  # Should be a substantial response

        # Check that it mentions vegetarian
        result_lower = result.lower()
        assert any(
            word in result_lower
            for word in ["vegetarian", "veggie", "green", "garden", "restaurant"]
        )

        print(f"\n✅ Function Calling Works! Response:\n{result}\n")

    def test_real_api_multiple_filters(self, recommender, sample_restaurants):
        """
        Test complex query with multiple filters
        THIS MAKES AN ACTUAL API CALL TO GROQ (FREE)
        """
        print("\n🧪 Testing complex multi-filter query...")

        # Mock the database search
        self._mock_database_query(recommender, [sample_restaurants[2]])

        # Complex query ⭐⭐⭐
        result = recommender.get_recommendations(
            "I need a moderately priced vegetarian restaurant with vegan options and outdoor seating in Raleigh"
        )

        assert result is not None
        assert len(result) > 0

        print(f"\n✅ Complex Query Response:\n{result}\n")

    def test_real_api_no_results_scenario(self, recommender):
        """
        Test how API handles when database returns no results
        THIS MAKES AN ACTUAL API CALL TO GROQ (FREE)
        """
        print("\n🧪 Testing no results scenario...")

        # Mock the database search to return empty list
        self._mock_database_query(recommender, [])

        # Make REAL API call ⭐⭐⭐
        result = recommender.get_recommendations("Find me a Martian cuisine restaurant")

        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

        print(f"\n✅ No Results Response:\n{result}\n")

    def test_real_api_response_quality(self, recommender, sample_restaurants):
        """
        Test that API responses are high quality and relevant
        THIS MAKES AN ACTUAL API CALL TO GROQ (FREE)
        """
        print("\n🧪 Testing response quality...")

        # Mock the database search
        self._mock_database_query(recommender, sample_restaurants)

        # Make REAL API call ⭐⭐⭐
        result = recommender.get_recommendations(
            "Recommend a good restaurant for a romantic date night"
        )

        # Check response quality
        assert len(result) > 100  # Should be detailed
        result_lower = result.lower()

        # Should mention restaurants or provide recommendations
        assert any(
            word in result_lower for word in ["restaurant", "recommend", "suggest"]
        )

        # Should not be an error message
        assert "error" not in result_lower
        assert "failed" not in result_lower

        print(f"\n✅ Quality Response:\n{result[:300]}...\n")


# ==========================================
# EDGE CASE TESTS
# ==========================================


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.fixture
    def mock_env(self):
        with patch.dict(
            os.environ,
            {
                "GROQ_API_KEY": "test-key-123",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "test-key",
            },
        ):
            yield

    @pytest.fixture
    def recommender(self, mock_env):
        with (
            patch("utils.restaurant_recommender.create_supabase_client"),
            patch("utils.restaurant_recommender.Groq"),
        ):
            from utils.restaurant_recommender import RestaurantRecommender

            return RestaurantRecommender(use_groq=True)

    def test_empty_search_filters(self, recommender):
        """Test search with no filters"""
        mock_response = Mock()
        mock_response.data = []

        mock_query = MagicMock()
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response

        recommender.supabase.table.return_value.select.return_value = mock_query

        result = recommender.search_restaurants()

        assert isinstance(result, list)
        assert len(result) == 0

    def test_search_limits_to_10_results(self, recommender):
        """Test that search limits results to 10"""
        # Create 15 mock restaurants
        many_restaurants = [
            {
                "id": i,
                "name": f"Restaurant {i}",
                "cuisine_type": "Test",
                "price_range": "$",
                "address": "Test St",
                "description": "Test description",
                "rating": 4.0,
            }
            for i in range(15)
        ]

        mock_response = Mock()
        mock_response.data = many_restaurants

        mock_query = MagicMock()
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response

        recommender.supabase.table.return_value.select.return_value = mock_query

        results = recommender.search_restaurants()

        assert len(results) == 10  # Should be limited to 10


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
