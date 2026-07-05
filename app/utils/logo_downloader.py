import urllib.request
import json
import urllib.parse
import os
import re
import base64
import threading
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from app import db
from app.models import UniversityLogo

def get_slug_from_domain(app, domain):
    mapping = app.config.get("SUBDOMAIN_UNIVERSITY_MAP", {})
    reverse_map = {v: k for k, v in mapping.items()}
    return reverse_map.get(domain, domain.split('.')[0])

def sanitize_svg(svg_content):
    """Sanitize SVG content by stripping script tags, event handlers, and external href links."""
    try:
        root = ET.fromstring(svg_content)
    except Exception:
        raise ValueError("Invalid SVG XML structure")
        
    for elem in root.iter():
        tag_name = elem.tag.split('}')[-1].lower()
        if tag_name == 'script':
            elem.clear()
            elem.tag = 'g'  # Convert script tag to empty group to safe-strip it
            
        # Strip all event handlers starting with "on"
        for attr in list(elem.attrib.keys()):
            attr_name = attr.split('}')[-1].lower()
            if attr_name.startswith('on'):
                del elem.attrib[attr]
            elif attr_name in ('href', 'xlink:href'):
                val = elem.attrib[attr].strip().lower()
                # Remove links pointing to external or javascript handlers
                if any(val.startswith(p) for p in ('javascript:', 'data:', 'http:', 'https:')):
                    del elem.attrib[attr]
                    
    return ET.tostring(root, encoding='unicode')

def make_svg_single_color(svg_content):
    """Convert SVG to a single-color stencil by setting fill and stroke to currentColor."""
    try:
        root = ET.fromstring(svg_content)
    except Exception:
        return svg_content
        
    for elem in root.iter():
        tag_name = elem.tag.split('}')[-1].lower()
        if tag_name in ('path', 'rect', 'circle', 'polygon', 'ellipse', 'line', 'polyline'):
            # Convert normal fills to currentColor
            fill = elem.attrib.get('fill')
            if fill and fill.lower() != 'none':
                elem.attrib['fill'] = 'currentColor'
                
            stroke = elem.attrib.get('stroke')
            if stroke and stroke.lower() != 'none':
                elem.attrib['stroke'] = 'currentColor'
                
            # Inline style attribute cleanup
            style = elem.attrib.get('style')
            if style:
                rules = style.split(';')
                new_rules = []
                for rule in rules:
                    if ':' in rule:
                        k, v = rule.split(':', 1)
                        k_clean = k.strip().lower()
                        v_clean = v.strip().lower()
                        if k_clean == 'fill' and v_clean != 'none':
                            new_rules.append(f"{k.strip()}: currentColor")
                        elif k_clean == 'stroke' and v_clean != 'none':
                            new_rules.append(f"{k.strip()}: currentColor")
                        elif k_clean in ('color', 'background-color'):
                            pass
                        else:
                            new_rules.append(rule)
                    else:
                        new_rules.append(rule)
                elem.attrib['style'] = ';'.join(new_rules)
                
    return ET.tostring(root, encoding='unicode')

def wrap_png_in_svg(png_bytes):
    """Wrap raw PNG bytes in a standard base64-encoded SVG element."""
    base64_data = base64.b64encode(png_bytes).decode('utf-8')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">\n'
        f'  <image href="data:image/png;base64,{base64_data}" x="0" y="0" width="100" height="100"/>\n'
        '</svg>\n'
    )

def fetch_from_clearbit(domain):
    """Attempt to fetch the logo from Clearbit's API."""
    url = f"https://logo.clearbit.com/{domain}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    # Specifying a strict 5s timeout to prevent infinite hanging
    with urllib.request.urlopen(req, timeout=5) as response:
        content_type = response.headers.get('Content-Type', '').lower()
        data = response.read()
        
    if 'image/svg' in content_type:
        return 'svg', data.decode('utf-8')
    elif 'image/png' in content_type:
        return 'png', data
    return None, None

def fetch_from_wikimedia(domain):
    """Query Wikimedia Commons API to find and download a university crest SVG."""
    # First search for the file using the domain name or university term
    search_query = f"{domain.split('.')[0]} university coat of arms"
    params = {
        'action': 'query',
        'list': 'search',
        'srsearch': search_query,
        'srlimit': 5,
        'format': 'json',
        'utf8': 1
    }
    url_params = urllib.parse.urlencode(params)
    api_url = f"https://commons.wikimedia.org/w/api.php?{url_params}"
    
    req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=5) as r:
        search_data = json.loads(r.read().decode('utf-8'))
        
    results = search_data.get('query', {}).get('search', [])
    file_title = None
    for res in results:
        title = res.get('title', '')
        if title.startswith('File:') and title.lower().endswith('.svg'):
            file_title = title
            break
            
    if not file_title:
        return None
        
    # Query ImageInfo to get direct download URL
    info_params = {
        'action': 'query',
        'titles': file_title,
        'prop': 'imageinfo',
        'iiprop': 'url',
        'format': 'json'
    }
    info_url = f"https://commons.wikimedia.org/w/api.php?{urllib.parse.urlencode(info_params)}"
    req_info = urllib.request.Request(info_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req_info, timeout=5) as r_info:
        info_data = json.loads(r_info.read().decode('utf-8'))
        
    pages = info_data.get('query', {}).get('pages', {})
    direct_url = None
    for page_id, page_data in pages.items():
        imageinfo = page_data.get('imageinfo', [])
        if imageinfo:
            direct_url = imageinfo[0].get('url')
            break
            
    if not direct_url:
        return None
        
    # Download the SVG content
    req_dl = urllib.request.Request(direct_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req_dl, timeout=5) as r_dl:
        svg_text = r_dl.read().decode('utf-8')
        
    return svg_text

def bg_fetch_logo(app, domain):
    """Background worker task to fetch, sanitize, and save a university logo."""
    with app.app_context():
        app.logger.info(f"Background logo fetch started for domain: {domain}")
        logo_record = UniversityLogo.query.filter_by(domain=domain).first()
        if not logo_record:
            logo_record = UniversityLogo(domain=domain, logo_status='pending')
            db.session.add(logo_record)
            db.session.commit()
            
        slug = get_slug_from_domain(app, domain)
        dest_filename = f"{slug}.svg"
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

        # 1. Try Clearbit Logo API
        try:
            format_type, data = fetch_from_clearbit(domain)
            if format_type == 'svg':
                sanitized = sanitize_svg(data)
                with open(dest_path, 'w', encoding='utf-8') as f:
                    f.write(sanitized)
                logo_record.logo_status = 'fetched'
                if safe_commit():
                    app.logger.info(f"Successfully fetched Clearbit SVG logo for {domain}")
                return
            elif format_type == 'png':
                # Wrap PNG in SVG
                wrapped = wrap_png_in_svg(data)
                with open(dest_path, 'w', encoding='utf-8') as f:
                    f.write(wrapped)
                logo_record.logo_status = 'fetched'
                if safe_commit():
                    app.logger.info(f"Successfully wrapped Clearbit PNG logo for {domain} into SVG")
                return
        except Exception as e:
            app.logger.warning(f"Failed to fetch logo from Clearbit for {domain}: {e}")
            
        # 2. Try Wikimedia Commons
        try:
            svg_text = fetch_from_wikimedia(domain)
            if svg_text:
                sanitized = sanitize_svg(svg_text)
                with open(dest_path, 'w', encoding='utf-8') as f:
                    f.write(sanitized)
                logo_record.logo_status = 'fetched'
                if safe_commit():
                    app.logger.info(f"Successfully fetched Wikimedia Commons SVG logo for {domain}")
                return
        except Exception as e:
            app.logger.warning(f"Failed to fetch logo from Wikimedia Commons for {domain}: {e}")
            
        # If all sources fail, mark as no_logo
        logo_record.logo_status = 'no_logo'
        if safe_commit():
            app.logger.error(f"Could not find logo for university domain: {domain}. Marked status as no_logo.")

def start_logo_fetch_job(app, domain):
    """Thread launcher to start the logo fetch task asynchronously or synchronously."""
    # Ensure a pending record is in the DB before starting the thread to avoid race conditions
    with app.app_context():
        logo_record = UniversityLogo.query.filter_by(domain=domain).first()
        if not logo_record:
            logo_record = UniversityLogo(domain=domain, logo_status='pending')
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
