"""
Reuni — Index & Dashboard Tests
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

    def test_search_wildcard_escaping(self, client, db_session, sample_user):
        """Search queries containing % and _ should be escaped to match literally."""
        from app.models import Item
        item1 = Item(
            title="100% Pure Silk Scarf",
            description="Scarf",
            category="Clothing",
            condition="New",
            price=12.50,
            seller_id=sample_user.id,
            image_filename="scarf.jpg"
        )
        item2 = Item(
            title="Cotton_Shirt_Blue",
            description="Shirt",
            category="Clothing",
            condition="Good",
            price=10.00,
            seller_id=sample_user.id,
            image_filename="shirt.jpg"
        )
        db_session.session.add_all([item1, item2])
        db_session.session.commit()

        # Search literal '%'
        resp = client.get("/?q=%")
        assert b"100% Pure Silk Scarf" in resp.data
        assert b"Cotton_Shirt_Blue" not in resp.data

        # Search literal '_'
        resp = client.get("/?q=_")
        assert b"Cotton_Shirt_Blue" in resp.data
        assert b"100% Pure Silk Scarf" not in resp.data

    def test_price_filter_edge_cases(self, client, db_session, sample_user):
        """Price filter should not crash on negative inputs or invalid ranges."""
        from app.models import Item
        item = Item(
            title="Filtered Item",
            description="Test",
            category="Books",
            condition="New",
            price=10.00,
            seller_id=sample_user.id,
            image_filename="book.jpg"
        )
        db_session.session.add(item)
        db_session.session.commit()

        # Min price negative
        resp = client.get("/?min_price=-5&max_price=15")
        assert resp.status_code == 200
        assert b"Filtered Item" in resp.data

        # Min price > Max price
        resp = client.get("/?min_price=20&max_price=5")
        assert resp.status_code == 200
        assert b"Filtered Item" not in resp.data


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


class TestProfilePage:

    def test_profile_route_authenticated(self, auth_client):
        """GET /profile as logged-in user should succeed."""
        resp = auth_client.get("/profile")
        assert resp.status_code == 200
        assert b"Eco Impact" in resp.data or b"Activity" in resp.data

    def test_profile_route_anonymous(self, client):
        """GET /profile as anonymous user should redirect to login."""
        resp = client.get("/profile", follow_redirects=False)
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers["Location"]

    def test_profile_bought_excludes_pending(self, second_auth_client, second_user, db_session, sample_item):
        """Profile bought count should exclude items claimed but not verified/sold yet."""
        import re
        from bs4 import BeautifulSoup
        from app.models import Item

        # 1. Initially, second_user has not claimed anything. Bought/recycled stats should be 0.
        resp = second_auth_client.get("/profile")
        assert resp.status_code == 200

        # Let's set the buyer of the sample_item to second_user and keep is_sold=False (pending PIN)
        sample_item.buyer_id = second_user.id
        sample_item.is_sold = False
        db_session.session.commit()

        # 2. Check the profile again. Since is_sold is False, bought/recycled should still be 0.
        resp = second_auth_client.get("/profile")
        assert resp.status_code == 200
        
        # Parse HTML to verify stats
        data_str = resp.data.decode("utf-8")
        assert "Bought" in data_str
        assert "Items recycled" in data_str
        
        # Robust check for 0 value in bought stat specifically
        soup = BeautifulSoup(resp.data, "html.parser")
        bought_label = soup.find(string=re.compile("Bought"))
        assert bought_label is not None, "Bought label not found"
        bought_value = bought_label.find_next().text.strip()
        assert bought_value == "0", f"Expected bought count to be 0, got {bought_value}"

        recycled_label = soup.find(string=re.compile("Items recycled"))
        assert recycled_label is not None, "Items recycled label not found"
        recycled_value = recycled_label.find_next().text.strip()
        assert recycled_value == "0", f"Expected recycled count to be 0, got {recycled_value}"

        # 3. Mark the item as sold (simulating a completed transaction with PIN handshake)
        sample_item.is_sold = True
        db_session.session.commit()

        # 4. Check the profile again. Now bought and recycled should be 1.
        resp = second_auth_client.get("/profile")
        assert resp.status_code == 200
        
        # Verify updated stats
        soup_after = BeautifulSoup(resp.data, "html.parser")
        bought_label_after = soup_after.find(string=re.compile("Bought"))
        assert bought_label_after is not None, "Bought label not found after sale"
        bought_value_after = bought_label_after.find_next().text.strip()
        assert bought_value_after == "1", f"Expected bought count to be 1, got {bought_value_after}"

        recycled_label_after = soup_after.find(string=re.compile("Items recycled"))
        assert recycled_label_after is not None, "Items recycled label not found after sale"
        recycled_value_after = recycled_label_after.find_next().text.strip()
        assert recycled_value_after == "1", f"Expected recycled count to be 1, got {recycled_value_after}"
