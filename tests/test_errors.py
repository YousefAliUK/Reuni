"""
Reuni — Error Page Tests
Verifies custom error pages for 404 and 500 status codes.
"""


class TestErrorPages:
    
    def test_404_page(self, client):
        """GET /non-existent-route should return 404 with custom error page."""
        resp = client.get("/non-existent-route")
        assert resp.status_code == 404
        assert b"Page Not Found" in resp.data
        assert b"Reuni" in resp.data
        assert b"The page you requested could not be found" in resp.data
        assert b"Back to Home" in resp.data
    
    def test_500_page(self, client):
        """GET /test-500-trigger should return 500 with custom error page."""
        resp = client.get("/test-500-trigger")
        assert resp.status_code == 500
        assert b"Server Error" in resp.data
        assert b"Reuni" in resp.data
        assert b"Something went wrong on our end" in resp.data
        assert b"Back to Home" in resp.data
        # Ensure no exception details leaked
        assert b"Traceback" not in resp.data
        assert b"RuntimeError" not in resp.data