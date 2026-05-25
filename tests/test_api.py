"""
UniCycle — API Tests
Verifies the category-weights JSON endpoint.
"""

from app.models import CATEGORY_WEIGHTS, CATEGORIES


class TestCategoryWeightsAPI:

    def test_category_weights_api_returns_json(self, client):
        """GET /items/api/category-weights should return 200 with JSON."""
        resp = client.get("/items/api/category-weights")
        assert resp.status_code == 200
        assert resp.content_type == "application/json"

    def test_category_weights_api_values(self, client):
        """Response should contain all categories with correct weight values."""
        resp = client.get("/items/api/category-weights")
        data = resp.get_json()

        for cat in CATEGORIES:
            assert cat in data, f"Missing category: {cat}"
            assert data[cat] == CATEGORY_WEIGHTS[cat]

    def test_category_weights_api_count(self, client):
        """API should return exactly the same number of entries as CATEGORIES."""
        resp = client.get("/items/api/category-weights")
        data = resp.get_json()
        assert len(data) == len(CATEGORIES)
