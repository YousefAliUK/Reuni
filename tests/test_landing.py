"""
Reuni — Landing Page Bento Grid & Cookie Redirection Tests
Verifies the custom landing page rendering, cookie redirects, and subdomain gating.
"""

from app.models import Item, User


def test_landing_page_renders_with_aggregates(client, db_session, sample_user):
    """GET / with X-Test-Landing header should render the landing page with statistics."""
    # Create some sold items to populate ESG stats
    item1 = Item(
        title="Sold Book",
        description="Sold",
        category="Books",
        condition="Good",
        price=10.0,
        seller_id=sample_user.id,
        is_sold=True,
        kg_saved=5.5,
        university_domain="brookes.ac.uk"
    )
    item2 = Item(
        title="Sold Electronics",
        description="Sold",
        category="Electronics",
        condition="New",
        price=50.0,
        seller_id=sample_user.id,
        is_sold=True,
        kg_saved=12.0,
        university_domain="oxford.ac.uk"
    )
    # Active listing (should count towards selection node counts)
    item3 = Item(
        title="Active Sports Item",
        description="Active",
        category="Sports",
        condition="Good",
        price=20.0,
        seller_id=sample_user.id,
        is_sold=False,
        kg_saved=3.0,
        university_domain="brookes.ac.uk"
    )
    db_session.session.add_all([item1, item2, item3])
    db_session.session.commit()

    # Call / with X-Test-Landing header to prevent the testing mode fallback
    resp = client.get("/", headers={"X-Test-Landing": "true"})
    assert resp.status_code == 200
    
    # Assert Outfit/Syne custom fonts are loaded in html
    assert b"landing.css" in resp.data
    assert b"landing.js" in resp.data
    assert b"Outfit:wght" in resp.data
    assert b"Syne:wght" in resp.data
    
    # Assert editorial sections are present
    assert b"floating-navbar" in resp.data
    assert b"section-hero" in resp.data
    assert b"section-live-proof" in resp.data
    assert b"walkthrough-section" in resp.data
    assert b"section-trust-layer" in resp.data
    assert b"section-campuses" in resp.data
    assert b"section-sustainability" in resp.data
    assert b"section-dual-cta" in resp.data
    
    # Assert values: total saved is 17.5 kg
    assert b"17.5" in resp.data
    
    # Assert listings count: Brookes has 1 active listing
    assert b"data-count=\"1\"" in resp.data


def test_landing_page_cookie_redirect(client):
    """GET / with selected_uni cookie should redirect to subdomain."""
    client.set_cookie("selected_uni", "brookes")
    
    # Do request to main domain landing page
    resp = client.get("/", headers={"X-Test-Landing": "true"})
    
    # Should redirect (302) to the subdomain
    assert resp.status_code == 302
    assert "brookes.localhost" in resp.headers["Location"]


def test_landing_page_cookie_redirect_bypass(client):
    """GET / with selected_uni cookie and noredirect=true should not redirect."""
    client.set_cookie("selected_uni", "brookes")
    
    # Do request with bypass query parameter
    resp = client.get("/?noredirect=true", headers={"X-Test-Landing": "true"})
    
    # Should load the landing page successfully (200) instead of redirecting
    assert resp.status_code == 200
    assert b"section-campuses" in resp.data


def test_unrecognized_subdomain_aborts(client):
    """Accessing an unrecognized subdomain should return 404."""
    # Mocking request to unrecognized subdomain (using 3-part hostname)
    resp = client.get("/", base_url="http://fakeuni.reuni.local:5000/")
    assert resp.status_code == 404


def test_cannot_claim_item_from_different_university(auth_client, db_session, second_user):
    """A user cannot claim an item listed on another university's domain."""
    # Create an item on Oxford domain (second_user domain is university.ac.uk, which matches auth_client)
    # So let's set the item's university_domain to 'oxford.ac.uk'
    item = Item(
        title="Oxford Item",
        description="Listed on Oxford",
        category="Books",
        condition="Good",
        price=10.0,
        seller_id=second_user.id,
        is_sold=False,
        kg_saved=3.0,
        university_domain="oxford.ac.uk"
    )
    db_session.session.add(item)
    db_session.session.commit()

    # Try to claim this item using auth_client (whose domain is university.ac.uk)
    resp = auth_client.post(f"/items/{item.id}/buy", follow_redirects=True)
    
    # Should show flash message indicating they can't claim from other universities
    assert b"You cannot claim items from other universities." in resp.data
    
    # Verify in DB that it is NOT claimed (buyer_id is still None)
    item_after = db_session.session.get(Item, item.id)
    assert item_after.buyer_id is None

