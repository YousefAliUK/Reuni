import pytest
from unittest.mock import patch
from app.models import UniversityLogo
from app.utils.logo_downloader import (
    sanitize_svg,
    make_svg_single_color,
    wrap_png_in_svg,
    bg_fetch_logo
)

def test_sanitize_svg_strips_xss():
    malicious_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg">\n'
        '  <script>alert("XSS")</script>\n'
        '  <path d="M10 10 L20 20" onclick="hackSystem()" fill="red"/>\n'
        '  <image href="javascript:alert(1)" x="0" y="0"/>\n'
        '</svg>'
    )
    sanitized = sanitize_svg(malicious_svg)
    
    assert '<script>' not in sanitized
    assert 'onclick' not in sanitized
    assert 'hackSystem' not in sanitized
    assert 'javascript:alert(1)' not in sanitized

def test_make_svg_single_color():
    colored_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg">\n'
        '  <path d="M10 10 L20 20" fill="blue" stroke="#00FF00" style="fill:red;stroke:black;color:blue"/>\n'
        '</svg>'
    )
    cleaned = make_svg_single_color(colored_svg)
    
    assert 'fill="currentColor"' in cleaned
    assert 'stroke="currentColor"' in cleaned
    assert 'fill: currentColor' in cleaned
    assert 'stroke: currentColor' in cleaned

def test_wrap_png_in_svg():
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR...'
    wrapped = wrap_png_in_svg(png_data)
    
    assert '<svg' in wrapped
    assert '<image' in wrapped
    assert 'data:image/png;base64,' in wrapped

@patch('urllib.request.urlopen')
def test_bg_fetch_logo_failure_sets_no_logo(mock_urlopen, app, db_session):
    mock_urlopen.side_effect = Exception("Connection Timeout")
    domain = "test-fail.ac.uk"
    
    # Create pending record
    logo_rec = UniversityLogo(domain=domain, logo_status='pending')
    db_session.session.add(logo_rec)
    db_session.session.commit()
    
    # Run background downloader
    bg_fetch_logo(app, domain)
    
    # Verify DB status updated to no_logo
    updated_rec = UniversityLogo.query.filter_by(domain=domain).first()
    assert updated_rec.logo_status == 'no_logo'

