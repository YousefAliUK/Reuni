"""
UniCycle — Index & Dashboard Tests
Verifies marketplace home page and dashboard access.
"""


class TestIndexPage:

    def test_index_page_loads(self, client):
        """GET / should return 200."""
        resp = client.get("/")
        assert resp.status_code == 200

    def test_index_shows_items(self, client, sample_item):
        """Index page should display item titles."""
        resp = client.get("/")
        assert b"Test Textbook" in resp.data

    def test_index_category_filter(self, client, sample_item):
        """Filtering by category should only show matching items."""
        resp = client.get("/?category=Books")
        assert b"Test Textbook" in resp.data

        resp = client.get("/?category=Electronics")
        assert b"Test Textbook" not in resp.data

    def test_index_search(self, client, sample_item):
        """Searching by keyword should filter items."""
        resp = client.get("/?q=Textbook")
        assert b"Test Textbook" in resp.data

        resp = client.get("/?q=NonExistentProduct")
        assert b"Test Textbook" not in resp.data

    def test_index_shows_welcome_for_anonymous(self, client):
        """Anonymous users should see the welcome banner."""
        resp = client.get("/")
        assert b"second life" in resp.data

    def test_index_no_welcome_for_logged_in(self, auth_client):
        """Logged-in users should not see the welcome banner."""
        resp = auth_client.get("/")
        assert b"Get Started" not in resp.data


class TestDashboard:

    def test_dashboard_requires_login(self, client):
        """GET /dashboard unauthenticated should redirect to login."""
        resp = client.get("/dashboard", follow_redirects=False)
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers["Location"]

    def test_dashboard_loads_for_authenticated(self, auth_client):
        """GET /dashboard authenticated should return 200."""
        resp = auth_client.get("/dashboard")
        assert resp.status_code == 200
        assert b"Dashboard" in resp.data

    def test_dashboard_shows_listings(self, auth_client, sample_item):
        """Dashboard should display the user's listings."""
        resp = auth_client.get("/dashboard")
        assert b"Test Textbook" in resp.data

    def test_dashboard_shows_kg_saved(self, auth_client, sample_user):
        """Dashboard should display the user's kg saved total."""
        resp = auth_client.get("/dashboard")
        # kg saved value is 0.0 for a new user
        assert b"kg Saved" in resp.data


class TestSecurityHeaders:

    def test_x_content_type_options(self, client):
        """Response should include X-Content-Type-Options: nosniff."""
        resp = client.get("/")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_frame_options(self, client):
        """Response should include X-Frame-Options: SAMEORIGIN."""
        resp = client.get("/")
        assert resp.headers.get("X-Frame-Options") == "SAMEORIGIN"

    def test_referrer_policy(self, client):
        """Response should include Referrer-Policy header."""
        resp = client.get("/")
        assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
