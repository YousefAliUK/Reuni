import pytest
from unittest.mock import patch, MagicMock
from app.models import UniversityLogo
from app.utils.logo_downloader import (
    _download_and_save,
    _fallback_google_favicon,
    fetch_university_logo,
    bg_fetch_logo
)

@patch('requests.get')
def test_download_and_save_success(mock_get, tmp_path):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'a' * 7000  # min_size is 60 * 100 = 6000 bytes
    mock_get.return_value = mock_response

    test_file = tmp_path / "test.png"
    success = _download_and_save("http://example.com/logo.png", str(test_file), {}, min_size=60)
    assert success is True
    assert test_file.exists()
    assert test_file.read_bytes() == b'a' * 7000

@patch('requests.get')
def test_download_and_save_too_small(mock_get, tmp_path):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'a' * 5000  # too small (less than 6000 bytes)
    mock_get.return_value = mock_response

    test_file = tmp_path / "test.png"
    success = _download_and_save("http://example.com/logo.png", str(test_file), {}, min_size=60)
    assert success is False
    assert not test_file.exists()

@patch('requests.get')
def test_fetch_university_logo_apple_touch_icon(mock_get, tmp_path):
    # Mocking HTML response with apple-touch-icon link tag
    html_response = MagicMock()
    html_response.status_code = 200
    html_response.text = '<html><head><link rel="apple-touch-icon" href="/icons/apple-icon.png"></head></html>'
    
    image_response = MagicMock()
    image_response.status_code = 200
    image_response.content = b'png_data' * 1000
    
    mock_get.side_effect = [html_response, image_response]
    
    test_file = tmp_path / "oxford.png"
    success = fetch_university_logo("oxford.ac.uk", "oxford", str(test_file))
    assert success is True
    assert test_file.exists()
    # Check that it attempted to request the correct absolute URL
    assert mock_get.call_count == 2
    mock_get.assert_any_call("https://oxford.ac.uk/icons/apple-icon.png", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; compatible; Reuni/1.0)"}, timeout=8)

@patch('requests.get')
def test_fetch_university_logo_fallback_google_favicon(mock_get, tmp_path):
    def dynamic_get(url, *args, **kwargs):
        if "commons.wikimedia.org" in url:
            m = MagicMock(status_code=200)
            m.json.return_value = {"query": {"search": []}}
            return m
        elif "s2/favicons" in url:
            return MagicMock(status_code=200, content=b'google_bytes')
        else:
            raise Exception("Connection Error")
            
    mock_get.side_effect = dynamic_get
    
    test_file = tmp_path / "oxford.png"
    success = fetch_university_logo("oxford.ac.uk", "oxford", str(test_file))
    assert success is True
    assert test_file.exists()
    assert test_file.read_bytes() == b'google_bytes'
    mock_get.assert_any_call("https://www.google.com/s2/favicons?sz=256&domain=oxford.ac.uk", headers={}, timeout=8)

@patch('app.utils.logo_downloader.fetch_university_logo')
def test_bg_fetch_logo_success_updates_db(mock_fetch, app, db_session):
    mock_fetch.return_value = True
    domain = "test-success.ac.uk"
    
    # Create pending record
    logo_rec = UniversityLogo(domain=domain, logo_status='pending')
    db_session.session.add(logo_rec)
    db_session.session.commit()
    
    bg_fetch_logo(app, domain)
    
    updated_rec = UniversityLogo.query.filter_by(domain=domain).first()
    assert updated_rec.logo_status == 'fetched'

@patch('app.utils.logo_downloader.fetch_university_logo')
def test_bg_fetch_logo_failure_sets_no_logo(mock_fetch, app, db_session):
    mock_fetch.return_value = False
    domain = "test-fail.ac.uk"
    
    # Create pending record
    logo_rec = UniversityLogo(domain=domain, logo_status='pending')
    db_session.session.add(logo_rec)
    db_session.session.commit()
    
    bg_fetch_logo(app, domain)
    
    updated_rec = UniversityLogo.query.filter_by(domain=domain).first()
    assert updated_rec.logo_status == 'no_logo'

@patch('requests.get')
def test_fetch_university_logo_fallback_wikimedia_png(mock_get, tmp_path):
    # Mock HTML request raising exception
    mock_html = Exception("Connection Error")
    
    # Mock Wikimedia search returning a result
    mock_search = MagicMock(status_code=200)
    mock_search.json.return_value = {
        "query": {
            "search": [
                {"title": "File:Arms of University of Oxford.svg"}
            ]
        }
    }
    
    # Mock Wikimedia imageinfo returning thumburl
    mock_info = MagicMock(status_code=200)
    mock_info.json.return_value = {
        "query": {
            "pages": {
                "123": {
                    "imageinfo": [
                        {"thumburl": "https://upload.wikimedia.org/oxford.png"}
                    ]
                }
            }
        }
    }
    
    # Mock download success
    mock_download = MagicMock(status_code=200, content=b'wiki_png_bytes')
    
    mock_get.side_effect = [mock_html, mock_search, mock_info, mock_download]
    
    test_file = tmp_path / "oxford.png"
    success = fetch_university_logo("oxford.ac.uk", "oxford", str(test_file))
    assert success is True
    assert test_file.exists()
    assert test_file.read_bytes() == b'wiki_png_bytes'
