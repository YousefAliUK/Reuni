import os
import re
import threading
import socket
import ipaddress
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from app import db
from app.models import UniversityConfig

def _is_safe_url(url: str) -> bool:
    """Validate that the URL resolves to a public, global IP address to prevent SSRF."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False
        
        hostname = parsed.hostname
        if not hostname:
            return False
        
        # Resolve hostname to all associated IPs to handle multi-homing/DNS rebinding
        addr_info = socket.getaddrinfo(hostname, None)
        for info in addr_info:
            ip_str = info[4][0]
            ip = ipaddress.ip_address(ip_str)
            if (ip.is_loopback or 
                ip.is_link_local or 
                ip.is_private or 
                ip.is_reserved or 
                ip.is_multicast or 
                ip.is_unspecified):
                return False
        return True
    except Exception:
        return False

def get_slug_from_domain(app, domain):
    try:
        from app import get_subdomain_map
        mapping = get_subdomain_map()
        reverse_map = {v: k for k, v in mapping.items()}
        if domain in reverse_map:
            return reverse_map[domain]
    except Exception:
        pass
    return domain.split('.')[0]

DEFAULT_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; compatible; Reuni/1.0)"}

def _download_and_save(url: str, path: str, headers: dict = None, min_size: int = 0) -> bool:
    if not _is_safe_url(url):
        return False
    if not headers:
        headers = DEFAULT_HEADERS
    try:
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200 and len(r.content) > min_size * 100:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(r.content)
            return True
    except Exception:
        pass
    return False

def _fallback_google_favicon(domain: str, slug: str, save_path: str) -> bool:
    url = f"https://www.google.com/s2/favicons?sz=256&domain={domain}"
    return _download_and_save(url, save_path, {}, min_size=0)

def fetch_from_wikimedia_png(slug: str) -> str:
    """Query Wikimedia Commons for a university coat of arms/logo and get a PNG render URL."""
    search_queries = [
        f"University of {slug} coat of arms",
        f"{slug} university coat of arms",
        f"{slug} university logo",
        f"{slug} university shield"
    ]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; compatible; Reuni/1.0)'}
    for query in search_queries:
        try:
            params = {
                'action': 'query',
                'list': 'search',
                'srsearch': query,
                'srnamespace': 6, # File namespace only
                'srlimit': 3,
                'format': 'json',
                'utf8': 1
            }
            api_url = f"https://commons.wikimedia.org/w/api.php"
            r = requests.get(api_url, params=params, headers=headers, timeout=5)
            if r.status_code != 200:
                continue
            data = r.json()
            results = data.get('query', {}).get('search', [])
            file_title = None
            for res in results:
                title = res.get('title', '')
                if title.startswith('File:') and title.lower().endswith(('.svg', '.png')):
                    file_title = title
                    break
                    
            if file_title:
                # Query ImageInfo with iiurlwidth=256 to get the PNG thumbnail url
                info_params = {
                    'action': 'query',
                    'titles': file_title,
                    'prop': 'imageinfo',
                    'iiprop': 'url',
                    'iiurlwidth': 256,
                    'format': 'json'
                }
                r_info = requests.get(api_url, params=info_params, headers=headers, timeout=5)
                if r_info.status_code != 200:
                    continue
                info_data = r_info.json()
                pages = info_data.get('query', {}).get('pages', {})
                for page_id, page_data in pages.items():
                    imageinfo = page_data.get('imageinfo', [])
                    if imageinfo:
                        direct_url = imageinfo[0].get('thumburl')
                        if not direct_url:
                            direct_url = imageinfo[0].get('url')
                        return direct_url
        except Exception:
            pass
    return None

def fetch_university_logo(domain: str, slug: str, save_path: str) -> bool:
    """
    Fetch the best available icon mark for a university domain.
    Priority: apple-touch-icon (180px) → high-res manifest icon → 
              og:image/large icon → Wikimedia Commons PNG → Google favicon.ico
    Saves to static/img/logos/{slug}.png
    Returns True if saved, False if nothing found.
    """
    base_url = f"https://{domain}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; compatible; Reuni/1.0)"}
    
    try:
        if not _is_safe_url(base_url):
            raise ValueError("Unsafe base URL")
        resp = requests.get(base_url, headers=headers, timeout=8)
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception:
        # If the main website is unreachable or unsafe, fallback to Wikimedia search, then Google favicon
        wiki_png_url = fetch_from_wikimedia_png(slug)
        if wiki_png_url and _download_and_save(wiki_png_url, save_path, {}, min_size=0):
            return True
        return _fallback_google_favicon(domain, slug, save_path)
    
    # Priority 1 — apple-touch-icon (180×180, always the icon mark)
    for rel in ["apple-touch-icon-precomposed", "apple-touch-icon"]:
        tag = soup.find("link", rel=lambda r: r and r.lower() == rel)
        if tag and tag.get("href"):
            url = urljoin(base_url, tag["href"])
            if _download_and_save(url, save_path, headers, min_size=60):
                return True
    
    # Priority 2 — web app manifest icons (often 192px or 512px)
    manifest_tag = soup.find("link", rel=lambda r: r and r.lower() == "manifest")
    if manifest_tag and manifest_tag.get("href"):
        try:
            manifest_url = urljoin(base_url, manifest_tag["href"])
            if not _is_safe_url(manifest_url):
                raise ValueError("Unsafe manifest URL")
            manifest = requests.get(manifest_url, headers=headers, timeout=5).json()
            icons = sorted(
                manifest.get("icons", []),
                key=lambda i: int(re.sub(r"[^\d]", "", i.get("sizes","0").split()[0]) or 0),
                reverse=True
            )
            for icon in icons:
                url = urljoin(base_url, icon.get("src",""))
                if _download_and_save(url, save_path, headers, min_size=60):
                    return True
        except Exception:
            pass
    
    # Priority 3 — any large favicon link tag
    for tag in soup.find_all("link", rel=lambda r: r and "icon" in r.lower()):
        sizes = tag.get("sizes", "0x0")
        try:
            w = int(sizes.split("x")[0])
        except (ValueError, IndexError):
            w = 0
        if w >= 96 and tag.get("href"):
            url = urljoin(base_url, tag["href"])
            if _download_and_save(url, save_path, headers, min_size=60):
                return True
                
    # Priority 4 — Wikimedia Commons PNG
    wiki_png_url = fetch_from_wikimedia_png(slug)
    if wiki_png_url and _download_and_save(wiki_png_url, save_path, {}, min_size=0):
        return True

    # Priority 5 — Google favicon at sz=256
    return _fallback_google_favicon(domain, slug, save_path)

def bg_fetch_logo(app, domain):
    """Background worker task to fetch and save a university PNG logo."""
    with app.app_context():
        app.logger.info(f"Background logo fetch started for domain: {domain}")
        logo_record = UniversityConfig.query.filter_by(domain=domain).first()
        if not logo_record:
            logo_record = UniversityConfig(domain=domain, logo_status='pending')
            db.session.add(logo_record)
            db.session.commit()
            
        slug = get_slug_from_domain(app, domain)
        dest_filename = f"{slug}.png"
        dest_path = os.path.join(app.static_folder, 'img', 'logos', dest_filename)
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        def safe_commit():
            try:
                db.session.commit()
                return True
            except Exception as e:
                db.session.rollback()
                app.logger.warning(f"Database commit error in bg_fetch_logo thread for {domain}: {e}")
                return False

        try:
            success = fetch_university_logo(domain, slug, dest_path)
            if success:
                logo_record.logo_status = 'fetched'
                if safe_commit():
                    app.logger.info(f"Successfully fetched PNG logo for {domain} and saved to {dest_path}")
                return
        except Exception as e:
            app.logger.warning(f"Failed to fetch logo for {domain}: {e}")
            
        logo_record.logo_status = 'no_logo'
        if safe_commit():
            app.logger.error(f"Could not find logo for university domain: {domain}. Marked status as no_logo.")

def start_logo_fetch_job(app, domain):
    """Thread launcher to start the logo fetch task asynchronously or synchronously."""
    # Ensure a pending record is in the DB before starting the thread to avoid race conditions
    with app.app_context():
        logo_record = UniversityConfig.query.filter_by(domain=domain).first()
        if not logo_record:
            logo_record = UniversityConfig(domain=domain, logo_status='pending')
            db.session.add(logo_record)
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
            
    if app.config.get("TESTING"):
        # Run synchronously in testing to prevent async threads writing to dropped DB tables
        bg_fetch_logo(app, domain)
    else:
        thread = threading.Thread(target=bg_fetch_logo, args=(app, domain))
        thread.daemon = True
        thread.start()
