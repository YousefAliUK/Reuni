"""
Reuni — Demo Seed Script
Populates the database with investor-grade demo data for Oxford Brookes.

Usage (development / fresh DB):
    python seed.py

Usage (staging / non-debug / existing data override):
    python seed.py --force

WARNING: Running with --force will DROP ALL EXISTING DATA.
"""

import os
import sys
import uuid
import shutil
import random
import argparse
from datetime import datetime, timezone, timedelta

from PIL import Image as PILImage, ImageDraw, ImageFont

from app import create_app, db
from app.models import User, Item, Message, CancellationRecord, CATEGORY_WEIGHTS, CATEGORIES, CONDITION_CHOICES, UniversityConfig, Season, WeeklySnapshot, SeasonalSnapshot
from app.utils.email_validation import extract_university_domain

app = create_app()

FIRST_NAMES = [
    "Alex", "Emma", "Liam", "Olivia", "Noah", "Ava", "Oliver", "Sophia", "Elijah", "Isabella",
    "James", "Mia", "Benjamin", "Charlotte", "Lucas", "Amelia", "Henry", "Harper", "Alexander", "Evelyn",
    "Daniel", "Abigail", "Matthew", "Emily", "Michael", "Elizabeth", "William", "Sofia", "David", "Avery",
    "Joseph", "Ella", "Carter", "Madison", "Owen", "Scarlett", "Wyatt", "Victoria", "John", "Aria"
]
LAST_NAMES = [
    "Smith", "Jones", "Taylor", "Brown", "Williams", "Wilson", "Johnson", "Davies", "Robinson", "Wright",
    "Thompson", "Evans", "Walker", "White", "Roberts", "Green", "Hall", "Wood", "Harris", "Martin",
    "Jackson", "Clark", "Cooper", "Harrison", "Ward", "Turner", "Carter", "Phillips", "Mitchell", "Patel"
]

# ── Directory paths ──
UPLOAD_DIR = os.path.join(app.static_folder, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Source folder: app/static/images/seed/ — user places real images here before running seed
SEED_IMAGES_SOURCE_DIR = os.path.join(app.static_folder, "images", "seed")

# Placeholder colours (used only if a real image file is missing)
CATEGORY_COLOURS = {
    "Electronics":  ("#6366f1", "#ffffff"),
    "Furniture":    ("#f59e0b", "#1e293b"),
    "Kitchenware":  ("#ef4444", "#ffffff"),
    "Clothing":     ("#ec4899", "#ffffff"),
    "Books":        ("#0ea5e9", "#ffffff"),
    "Stationery":   ("#8b5cf6", "#ffffff"),
    "Sports":       ("#10b981", "#ffffff"),
    "Other":        ("#64748b", "#ffffff"),
}


def cleanup_r2_uploads():
    """Delete all listing images from the Cloudflare R2 bucket."""
    import boto3
    from botocore.config import Config
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=app.config["CF_R2_ENDPOINT_URL"],
            aws_access_key_id=app.config["CF_R2_ACCESS_KEY_ID"],
            aws_secret_access_key=app.config["CF_R2_SECRET_ACCESS_KEY"],
            config=Config(signature_version="s3v4")
        )
        bucket_name = app.config["CF_R2_BUCKET_NAME"]
        
        # Paginate through all objects in the bucket
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name)
        
        delete_keys = []
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    key = obj['Key']
                    # Delete files matching our listing filename conventions:
                    # 1. seed_*.webp
                    # 2. uuid.webp (32 hex characters + .webp)
                    is_seed = key.startswith("seed_") and key.endswith(".webp")
                    import re
                    is_uuid_webp = re.fullmatch(r"[0-9a-f]{32}\.webp", key.lower()) is not None
                    
                    if is_seed or is_uuid_webp:
                        delete_keys.append({'Key': key})
        
        if delete_keys:
            print(f"  Deleting {len(delete_keys)} objects from Cloudflare R2...")
            # boto3 delete_objects can delete up to 1000 keys at once
            for i in range(0, len(delete_keys), 1000):
                chunk = delete_keys[i:i+1000]
                s3.delete_objects(
                    Bucket=bucket_name,
                    Delete={'Objects': chunk}
                )
            print("  Cloudflare R2 cleanup complete.")
        else:
            print("  No listing images found in Cloudflare R2 to clean up.")
            
    except Exception as e:
        print(f"  [WARN] Failed to clean up Cloudflare R2 bucket: {e}")


def _save_seed_image(img, filename):
    """Save a seed image locally or upload to Cloudflare R2 if configured."""
    storage_provider = app.config.get("STORAGE_PROVIDER", "local")
    if storage_provider == "r2":
        import io
        import boto3
        from botocore.config import Config
        try:
            buffer = io.BytesIO()
            img.save(buffer, "WEBP", quality=80)
            buffer.seek(0)
            s3 = boto3.client(
                "s3",
                endpoint_url=app.config["CF_R2_ENDPOINT_URL"],
                aws_access_key_id=app.config["CF_R2_ACCESS_KEY_ID"],
                aws_secret_access_key=app.config["CF_R2_SECRET_ACCESS_KEY"],
                config=Config(signature_version="s3v4")
            )
            s3.upload_fileobj(
                buffer,
                app.config["CF_R2_BUCKET_NAME"],
                filename,
                ExtraArgs={"ContentType": "image/webp"}
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to upload seed image {filename} to Cloudflare R2"
            ) from e
    else:
        dest_path = os.path.join(UPLOAD_DIR, filename)
        img.save(dest_path, "WEBP", quality=80)


def make_placeholder(category, title):
    """Generate a simple coloured placeholder image for a given category."""
    bg, fg = CATEGORY_COLOURS.get(category, ("#64748b", "#ffffff"))
    img = PILImage.new("RGB", (800, 600), bg)
    draw = ImageDraw.Draw(img)

    try:
        font_large = ImageFont.truetype("arial.ttf", 48)
        font_small = ImageFont.truetype("arial.ttf", 28)
    except (IOError, OSError):
        font_large = ImageFont.load_default()
        font_small = font_large

    draw.text((400, 240), category, fill=fg, font=font_large, anchor="mm")
    short_title = title if len(title) <= 30 else title[:27] + "…"
    draw.text((400, 320), short_title, fill=fg, font=font_small, anchor="mm")

    filename = f"seed_{uuid.uuid4().hex}.webp"
    _save_seed_image(img, filename)
    return filename


def copy_seed_image(source_filename, category, title):
    """
    Load, resize to max 800px on either side, strip metadata, and save a seed image
    from 'app/static/images/seed/' into static/uploads/ as WebP.
    Falls back to make_placeholder() if missing or on failure.

    Args:
        source_filename (str): The exact filename in 'app/static/images/seed/',
                               e.g. "MacBook Air M2 (2022) 8GB256GB.jpg"
        category (str): Item category, used for placeholder fallback.
        title (str): Item title, used for placeholder fallback.

    Returns:
        str: The new filename (UUID-based) saved in static/uploads/.
    """
    source_path = os.path.join(SEED_IMAGES_SOURCE_DIR, source_filename)

    if not os.path.exists(source_path):
        print(f"  [WARN] Image not found: {source_filename} — using placeholder.")
        return make_placeholder(category, title)

    try:
        img = PILImage.open(source_path)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        
        img.thumbnail((800, 800), PILImage.LANCZOS)

        clean_img = PILImage.new(img.mode, img.size)
        clean_img.putdata(list(img.getdata()))

        new_filename = f"seed_{uuid.uuid4().hex}.webp"
        _save_seed_image(clean_img, new_filename)
        return new_filename
    except Exception as e:
        print(f"  [ERROR] Failed to process seed image {source_filename}: {e} — using placeholder.")
        return make_placeholder(category, title)


SAMPLE_USERS = [
    # ── Students ──
    {
        "email": "a.rahman@brookes.ac.uk",
        "name": "Aisha Rahman",
        "password": "BrookesDemo1",
        "role": "student",
        "partner_university": None,
    },
    {
        "email": "j.whitfield@brookes.ac.uk",
        "name": "Jack Whitfield",
        "password": "BrookesDemo1",
        "role": "student",
        "partner_university": None,
    },
    {
        "email": "p.nair@brookes.ac.uk",
        "name": "Priya Nair",
        "password": "BrookesDemo1",
        "role": "student",
        "partner_university": None,
    },
    {
        "email": "c.fraser@brookes.ac.uk",
        "name": "Callum Fraser",
        "password": "BrookesDemo1",
        "role": "student",
        "partner_university": None,
    },
    {
        "email": "m.zhou@brookes.ac.uk",
        "name": "Mei-Ling Zhou",
        "password": "BrookesDemo1",
        "role": "student",
        "partner_university": None,
    },
    {
        "email": "t.keller@brookes.ac.uk",
        "name": "Tobias Keller",
        "password": "BrookesDemo1",
        "role": "student",
        "partner_university": None,
    },
    {
        "email": "f.alamin@brookes.ac.uk",
        "name": "Fatima Al-Amin",
        "password": "BrookesDemo1",
        "role": "student",
        "partner_university": None,
    },
    {
        "email": "s.osei@brookes.ac.uk",
        "name": "Samuel Osei",
        "password": "BrookesDemo1",
        "role": "student",
        "partner_university": None,
    },
    {
        "email": "i.constantin@brookes.ac.uk",
        "name": "Ioana Constantin",
        "password": "BrookesDemo1",
        "role": "student",
        "partner_university": None,
    },
    {
        "email": "r.marsh@brookes.ac.uk",
        "name": "Reuben Marsh",
        "password": "BrookesDemo1",
        "role": "student",
        "partner_university": None,
    },
    {
        "email": "d.park@brookes.ac.uk",
        "name": "Danielle Park",
        "password": "BrookesDemo1",
        "role": "student",
        "partner_university": None,
    },
    {
        "email": "o.hurst@brookes.ac.uk",
        "name": "Oliver Hurst",
        "password": "BrookesDemo1",
        "role": "student",
        "partner_university": None,
    },
    # ── Admin ──
    {
        "email": "admin@brookes.ac.uk",
        "name": "Yousef Ali",
        "password": "BrookesDemo1",
        "role": "admin",
        "partner_university": None,
    },
    # ── Partner ──
    {
        "email": "sustainability@brookes.ac.uk",
        "name": "Sustainability Office",
        "password": "BrookesDemo1",
        "role": "partner",
        "partner_university": "brookes.ac.uk",
    },
    # ── Oxford Demo Users ──
    {
        "email": "w.churchill@ox.ac.uk",
        "name": "Winston Churchill",
        "password": "OxfordDemo1",
        "role": "student",
        "partner_university": None,
    },
    {
        "email": "m.thatcher@ox.ac.uk",
        "name": "Margaret Thatcher",
        "password": "OxfordDemo1",
        "role": "student",
        "partner_university": None,
    },
    {
        "email": "a.turing@ox.ac.uk",
        "name": "Alan Turing",
        "password": "OxfordDemo1",
        "role": "student",
        "partner_university": None,
    },
    {
        "email": "admin@ox.ac.uk",
        "name": "Oxford Admin",
        "password": "OxfordDemo1",
        "role": "admin",
        "partner_university": None,
    },
    {
        "email": "sustainability@ox.ac.uk",
        "name": "Oxford Sustainability Office",
        "password": "OxfordDemo1",
        "role": "partner",
        "partner_university": "ox.ac.uk",
    },
    # ── Cambridge Demo Users ──
    {
        "email": "i.newton@cam.ac.uk",
        "name": "Isaac Newton",
        "password": "BrookesDemo1",
        "role": "student",
        "partner_university": None,
    },
    {
        "email": "c.darwin@cam.ac.uk",
        "name": "Charles Darwin",
        "password": "BrookesDemo1",
        "role": "student",
        "partner_university": None,
    },
    {
        "email": "admin@cam.ac.uk",
        "name": "Cambridge Admin",
        "password": "BrookesDemo1",
        "role": "admin",
        "partner_university": None,
    },
    {
        "email": "sustainability@cam.ac.uk",
        "name": "Cambridge Sustainability Office",
        "password": "BrookesDemo1",
        "role": "partner",
        "partner_university": "cam.ac.uk",
    },
]

SAMPLE_ITEMS = [
    # ── Electronics (5 items: 3 sold, 2 active) ──
    {
        "title": "MacBook Air M2 (2022) 8GB/256GB",
        "description": (
            "Excellent condition, barely used during second year. Comes with the original MagSafe charger and box. "
            "Perfect for lecture notes, coding assignments, and design work. Battery health still at 94%. "
            "Space Grey. Collection from Headington campus preferred."
        ),
        "category": "Electronics",
        "condition": "Like New",
        "price": 680.00,
        "is_free": False,
        "seller_email": "a.rahman@brookes.ac.uk",
        "image_file": "MacBook Air M2 (2022) 8GB256GB.jpg",
        "is_sold": True,
        "buyer_email": "j.whitfield@brookes.ac.uk",
        "days_ago_claimed": 12,
        "days_active_before_claim": 3,
        "days_ago_listed": None,
    },
    {
        "title": "Casio fx-991EX ClassWiz Calculator",
        "description": (
            "The essential calculator for every maths, engineering, and science module at Brookes. "
            "Works perfectly — just upgraded to a graphical model. Includes the original slide cover. "
            "No scratches on the screen."
        ),
        "category": "Electronics",
        "condition": "Good",
        "price": 12.00,
        "is_free": False,
        "seller_email": "c.fraser@brookes.ac.uk",
        "image_file": "Casio fx-991EX ClassWiz Calculator.jpg",
        "is_sold": True,
        "buyer_email": "p.nair@brookes.ac.uk",
        "days_ago_claimed": 5,
        "days_active_before_claim": 2,
        "days_ago_listed": None,
    },
    {
        "title": "Logitech MX Keys Wireless Keyboard",
        "description": (
            "Full-size wireless keyboard with beautiful backlit keys and multi-device pairing (up to 3 devices). "
            "Barely used — I moved fully to my laptop keyboard. Still has months of battery life. "
            "Compatible with Mac and Windows."
        ),
        "category": "Electronics",
        "condition": "Like New",
        "price": 45.00,
        "is_free": False,
        "seller_email": "t.keller@brookes.ac.uk",
        "image_file": "Logitech MX Keys Wireless Keyboard.jpg",
        "is_sold": True,
        "buyer_email": "f.alamin@brookes.ac.uk",
        "days_ago_claimed": 8,
        "days_active_before_claim": 4,
        "days_ago_listed": None,
    },
    {
        "title": "Sony WH-1000XM4 Headphones (Black)",
        "description": (
            "Industry-leading noise cancellation — ideal for the library, lectures, and commuting. "
            "One small scratch on the left ear cup, barely visible. "
            "Includes carry case, USB-C cable, and 3.5mm audio cable. "
            "Battery life still excellent (25+ hours). "
            "Selling because I switched to in-ears for the gym."
        ),
        "category": "Electronics",
        "condition": "Good",
        "price": 110.00,
        "is_free": False,
        "seller_email": "m.zhou@brookes.ac.uk",
        "image_file": "Sony WH-1000XM4 Headphones (Black).jpg",
        "is_sold": False,
        "buyer_email": None,
        "days_ago_claimed": None,
        "days_active_before_claim": None,
        "days_ago_listed": 6,
    },
    {
        "title": "Ring LED Desk Lamp (USB-C)",
        "description": (
            "Dimmable ring light desk lamp with 3 colour temperatures (warm, neutral, cool). "
            "Great for study sessions, video calls, and late-night revision. "
            "USB-C powered — plugs into any laptop or USB hub. "
            "Selling because I'm moving out of halls at the end of term."
        ),
        "category": "Electronics",
        "condition": "Good",
        "price": 8.00,
        "is_free": False,
        "seller_email": "r.marsh@brookes.ac.uk",
        "image_file": "Ring LED Desk Lamp (USB-C).jpg",
        "is_sold": False,
        "buyer_email": None,
        "days_ago_claimed": None,
        "days_active_before_claim": None,
        "days_ago_listed": 11,
    },

    # ── Furniture (4 items: 2 sold, 2 active) ──
    {
        "title": "IKEA MALM Desk (White, 140cm)",
        "description": (
            "Sturdy, spacious student desk in excellent condition. "
            "Disassembled and ready for collection on the Headington campus — all original screws and fixings included in a labelled bag. "
            "Dimensions: 140cm wide × 65cm deep. White finish with cable management holes."
        ),
        "category": "Furniture",
        "condition": "Good",
        "price": 30.00,
        "is_free": False,
        "seller_email": "s.osei@brookes.ac.uk",
        "image_file": "IKEA MALM Desk (White, 140cm).jpg",
        "is_sold": True,
        "buyer_email": "d.park@brookes.ac.uk",
        "days_ago_claimed": 3,
        "days_active_before_claim": 2,
        "days_ago_listed": None,
    },
    {
        "title": "IKEA KALLAX 4-Cube Shelf (White)",
        "description": (
            "Perfect for a student room — holds books, folders, clothes, anything. "
            "White finish, 4-cube layout (2x2). Disassembled. Collection from Harcourt Hill campus. "
            "Small scuff on the base panel, otherwise in great condition. "
            "Free — just needs to be collected this week."
        ),
        "category": "Furniture",
        "condition": "Fair",
        "price": 0.0,
        "is_free": True,
        "seller_email": "j.whitfield@brookes.ac.uk",
        "image_file": "IKEA KALLAX 4-Cube Shelf (White).jpg",
        "is_sold": True,
        "buyer_email": "i.constantin@brookes.ac.uk",
        "days_ago_claimed": 7,
        "days_active_before_claim": 3,
        "days_ago_listed": None,
    },
    {
        "title": "Single Mattress (Memory Foam, 3ft)",
        "description": (
            "Clean, hygienic single mattress from a non-smoking, pet-free room. "
            "A mattress protector was used the entire time. No stains. "
            "Moving abroad at the end of term — I simply cannot take it with me. "
            "Buyer must collect from Headington. Worth £120 new."
        ),
        "category": "Furniture",
        "condition": "Good",
        "price": 40.00,
        "is_free": False,
        "seller_email": "o.hurst@brookes.ac.uk",
        "image_file": "Single Mattress (Memory Foam, 3ft).jpg",
        "is_sold": False,
        "buyer_email": None,
        "days_ago_claimed": None,
        "days_active_before_claim": None,
        "days_ago_listed": 14,
    },
    {
        "title": "Swivel Office Chair (Grey Mesh)",
        "description": (
            "Adjustable height swivel chair with lumbar support and padded armrests. "
            "Used throughout first year — comfortable for long study sessions. "
            "Some wear on the seat cushion but fully functional. "
            "Selling cheap as I'm leaving halls at the end of term."
        ),
        "category": "Furniture",
        "condition": "Fair",
        "price": 20.00,
        "is_free": False,
        "seller_email": "f.alamin@brookes.ac.uk",
        "image_file": "Swivel Office Chair (Grey Mesh).jpg",
        "is_sold": False,
        "buyer_email": None,
        "days_ago_claimed": None,
        "days_active_before_claim": None,
        "days_ago_listed": 20,
    },

    # ── Books (6 items: 3 sold, 3 active) ──
    {
        "title": "Molecular Biology of the Cell — Alberts, 7th Ed.",
        "description": (
            "Highlighted throughout in yellow and pink, but every word is still clearly readable. "
            "Essential for all life sciences, biomedical science, and biology students at Brookes. "
            "ISBN: 978-0-393-88436-8. Some pages have pencil annotations in the margins."
        ),
        "category": "Books",
        "condition": "Good",
        "price": 18.00,
        "is_free": False,
        "seller_email": "p.nair@brookes.ac.uk",
        "image_file": "Molecular Biology book Alberts, 7th Ed..jpg",
        "is_sold": True,
        "buyer_email": "a.rahman@brookes.ac.uk",
        "days_ago_claimed": 14,
        "days_active_before_claim": 5,
        "days_ago_listed": None,
    },
    {
        "title": "Oxford Handbook of Clinical Medicine, 10th Ed.",
        "description": (
            "A must-have for nursing and healthcare students at Brookes. "
            "Very lightly annotated in pencil — most pages are completely clean. "
            "Fits in a lab coat pocket. 10th edition (the latest). "
            "Selling as I've finished my placement year."
        ),
        "category": "Books",
        "condition": "Like New",
        "price": 22.00,
        "is_free": False,
        "seller_email": "d.park@brookes.ac.uk",
        "image_file": "Oxford Handbook of Clinical Medicine.jpg",
        "is_sold": True,
        "buyer_email": "c.fraser@brookes.ac.uk",
        "days_ago_claimed": 6,
        "days_active_before_claim": 2,
        "days_ago_listed": None,
    },
    {
        "title": "Introduction to Algorithms (CLRS), 4th Ed.",
        "description": (
            "The definitive textbook for computer science students — known as CLRS. "
            "No highlighting anywhere, spine is intact and clean. "
            "Selling as I've completed my algorithms module and have no further use for it. "
            "4th edition — the newest version."
        ),
        "category": "Books",
        "condition": "Good",
        "price": 35.00,
        "is_free": False,
        "seller_email": "r.marsh@brookes.ac.uk",
        "image_file": "Introduction to Algorithms (CLRS), 4th Ed..jpg",
        "is_sold": True,
        "buyer_email": "t.keller@brookes.ac.uk",
        "days_ago_claimed": 4,
        "days_active_before_claim": 3,
        "days_ago_listed": None,
    },
    {
        "title": "Contemporary Business Communication — Hynes",
        "description": (
            "Required reading for several Business School modules at Brookes. "
            "Good condition — a few dog-eared pages and some light pencil underlining. "
            "No torn pages. Good value at this price."
        ),
        "category": "Books",
        "condition": "Fair",
        "price": 8.00,
        "is_free": False,
        "seller_email": "i.constantin@brookes.ac.uk",
        "image_file": "Contemporary Business Communication — Hynes.jpg",
        "is_sold": False,
        "buyer_email": None,
        "days_ago_claimed": None,
        "days_active_before_claim": None,
        "days_ago_listed": 9,
    },
    {
        "title": "Oxford English Grammar — Chalker & Weiner",
        "description": (
            "Excellent reference for English Language, Linguistics, and any international student "
            "wanting to strengthen their academic writing. Clean copy, no annotations. "
            "Hardback edition."
        ),
        "category": "Books",
        "condition": "Good",
        "price": 6.00,
        "is_free": False,
        "seller_email": "c.fraser@brookes.ac.uk",
        "image_file": "Oxford English Grammar — Chalker & Weiner.jpg",
        "is_sold": False,
        "buyer_email": None,
        "days_ago_claimed": None,
        "days_active_before_claim": None,
        "days_ago_listed": 18,
    },
    {
        "title": "Stationery & Book Bundle (6 items)",
        "description": (
            "Mix of A4 ruled notebooks (x2), a lab notebook (x1), plus an assortment of pens, "
            "sticky tabs, and highlighters. All brand new and unused. "
            "Happy to donate — just come and collect from Gipsy Lane campus."
        ),
        "category": "Books",
        "condition": "New",
        "price": 0.0,
        "is_free": True,
        "seller_email": "d.park@brookes.ac.uk",
        "image_file": "Stationery & Book Bundle (6 items).jpg",
        "is_sold": False,
        "buyer_email": None,
        "days_ago_claimed": None,
        "days_active_before_claim": None,
        "days_ago_listed": 3,
    },

    # ── Kitchenware (4 items: 2 sold, 2 active) ──
    {
        "title": "Full Kitchen Starter Kit (Pots, Pans, Utensils)",
        "description": (
            "Everything a first-year needs to cook properly: 2 saucepans (small and medium), "
            "1 frying pan, spatula, wooden spoon, grater, tin opener, and colander. "
            "All clean and in good working order. Moving out — selling as a bundle only."
        ),
        "category": "Kitchenware",
        "condition": "Good",
        "price": 20.00,
        "is_free": False,
        "seller_email": "o.hurst@brookes.ac.uk",
        "image_file": "Full Kitchen Starter Kit (Pots, Pans, Utensils).jpg",
        "is_sold": True,
        "buyer_email": "r.marsh@brookes.ac.uk",
        "days_ago_claimed": 10,
        "days_active_before_claim": 4,
        "days_ago_listed": None,
    },
    {
        "title": "Russell Hobbs 1.7L Kettle (Stainless Steel)",
        "description": (
            "Fast-boil kettle, works perfectly. Selling because my flat now has a shared kettle in the kitchen. "
            "Lightly limescaled inside but functions without any issues — descaler tablet included. "
            "Stainless steel body, approx. 1 year old."
        ),
        "category": "Kitchenware",
        "condition": "Good",
        "price": 12.00,
        "is_free": False,
        "seller_email": "j.whitfield@brookes.ac.uk",
        "image_file": "Russell Hobbs 1.7L Kettle (Stainless Steel).jpg",
        "is_sold": True,
        "buyer_email": "m.zhou@brookes.ac.uk",
        "days_ago_claimed": 2,
        "days_active_before_claim": 2,
        "days_ago_listed": None,
    },
    {
        "title": "Instant Pot Duo 5.7L Pressure Cooker",
        "description": (
            "Only used a handful of times — still essentially new. "
            "Ideal for batch cooking during term: soups, curries, rice, pasta. "
            "Comes with all original accessories (inner pot, steam rack, measuring cup, ladle, spoon) "
            "and the full recipe booklet."
        ),
        "category": "Kitchenware",
        "condition": "Like New",
        "price": 55.00,
        "is_free": False,
        "seller_email": "a.rahman@brookes.ac.uk",
        "image_file": "Instant Pot Duo 5.7L Pressure Cooker.jpg",
        "is_sold": False,
        "buyer_email": None,
        "days_ago_claimed": None,
        "days_active_before_claim": None,
        "days_ago_listed": 7,
    },
    {
        "title": "Microwave (700W, White)",
        "description": (
            "Works perfectly fine. Exterior is a bit battered on one corner (see photo) but the interior is clean. "
            "700W, standard size. Moving out and can't take it with me. "
            "Collection only from Marston Road area — cannot deliver."
        ),
        "category": "Kitchenware",
        "condition": "Fair",
        "price": 15.00,
        "is_free": False,
        "seller_email": "s.osei@brookes.ac.uk",
        "image_file": "Microwave (700W, White).jpg",
        "is_sold": False,
        "buyer_email": None,
        "days_ago_claimed": None,
        "days_active_before_claim": None,
        "days_ago_listed": 22,
    },

    # ── Clothing (4 items: 1 sold, 3 active) ──
    {
        "title": "North Face Resolve Waterproof Jacket (M)",
        "description": (
            "Dark navy. Fully waterproof with taped seams — survived an entire Oxford winter without a leak. "
            "Selling because I received a new one as a birthday gift. "
            "Size M. DryVent technology. Packable."
        ),
        "category": "Clothing",
        "condition": "Good",
        "price": 45.00,
        "is_free": False,
        "seller_email": "c.fraser@brookes.ac.uk",
        "image_file": "North Face Resolve Waterproof Jacket (M).jpg",
        "is_sold": False,
        "buyer_email": None,
        "days_ago_claimed": None,
        "days_active_before_claim": None,
        "days_ago_listed": 30,
    },
    {
        "title": "Bundle: 5 Men's Shirts (15\"/38cm collar)",
        "description": (
            "Mix of smart-casual shirts — ideal for presentations, placement interviews, and seminars. "
            "All from Next, laundered, ironed, and on hangers. "
            "15 inch / 38cm collar. Slim fit. Various colours (white, blue, grey, check, pale pink)."
        ),
        "category": "Clothing",
        "condition": "Good",
        "price": 15.00,
        "is_free": False,
        "seller_email": "t.keller@brookes.ac.uk",
        "image_file": "Bundle - 5 Men's Shirts (15-38cm collar).jpg",
        "is_sold": False,
        "buyer_email": None,
        "days_ago_claimed": None,
        "days_active_before_claim": None,
        "days_ago_listed": 16,
    },
    {
        "title": "Brookes Freshers Week Hoodie (Size L)",
        "description": (
            "Grey, official Oxford Brookes University Freshers Week 2024 hoodie. "
            "Worn twice and washed once — still looks brand new. "
            "Size L. A bit of a collector's item if you weren't there! "
            "Selling as it's slightly too big for me."
        ),
        "category": "Clothing",
        "condition": "Like New",
        "price": 10.00,
        "is_free": False,
        "seller_email": "f.alamin@brookes.ac.uk",
        "image_file": "Brookes Freshers Week Hoodie (Size L).jpg",
        "is_sold": True,
        "buyer_email": "s.osei@brookes.ac.uk",
        "days_ago_claimed": 9,
        "days_active_before_claim": 2,
        "days_ago_listed": None,
    },
    {
        "title": "Women's Puffer Jacket — ASOS (Size 12)",
        "description": (
            "Black, lightweight but genuinely warm puffer jacket from ASOS. "
            "Used for one winter season. Selling as I've switched to a heavier coat. "
            "No rips, tears, or stains. Size 12 UK."
        ),
        "category": "Clothing",
        "condition": "Good",
        "price": 20.00,
        "is_free": False,
        "seller_email": "m.zhou@brookes.ac.uk",
        "image_file": "Women's Puffer Jacket — ASOS (Size 12).jpg",
        "is_sold": False,
        "buyer_email": None,
        "days_ago_claimed": None,
        "days_active_before_claim": None,
        "days_ago_listed": 25,
    },

    # ── Sports (4 items: 1 sold, 3 active) ──
    {
        "title": "Yoga Mat (6mm, Purple)",
        "description": (
            "Non-slip, 6mm thick yoga mat. Lightly used — about 20 sessions. "
            "Comes with a carry strap for easy transport to the Brookes gym or classes. "
            "Sold because I now do classes at a studio that provides mats."
        ),
        "category": "Sports",
        "condition": "Good",
        "price": 8.00,
        "is_free": False,
        "seller_email": "i.constantin@brookes.ac.uk",
        "image_file": "Yoga Mat (6mm, Purple).jpg",
        "is_sold": True,
        "buyer_email": "a.rahman@brookes.ac.uk",
        "days_ago_claimed": 15,
        "days_active_before_claim": 4,
        "days_ago_listed": None,
    },
    {
        "title": "Boxing Gloves (12oz, Hayabusa)",
        "description": (
            "Good quality Hayabusa boxing gloves, 12oz. Used at the Brookes gym for one term. "
            "Clean inside — no smell. Wrist wraps not included. "
            "Selling as I've moved to a different gym that provides equipment."
        ),
        "category": "Sports",
        "condition": "Good",
        "price": 25.00,
        "is_free": False,
        "seller_email": "r.marsh@brookes.ac.uk",
        "image_file": "Boxing Gloves (12oz, Hayabusa).jpg",
        "is_sold": False,
        "buyer_email": None,
        "days_ago_claimed": None,
        "days_active_before_claim": None,
        "days_ago_listed": 13,
    },
    {
        "title": "Adjustable Dumbbell Set (2x5kg)",
        "description": (
            "Rubber-coated hex dumbbells, 5kg each. Scratched on the flat ends but fully functional and safe. "
            "Great for home workouts, shoulder press, bicep curls, lunges. "
            "Selling as I've upgraded to a heavier set."
        ),
        "category": "Sports",
        "condition": "Fair",
        "price": 18.00,
        "is_free": False,
        "seller_email": "o.hurst@brookes.ac.uk",
        "image_file": "Adjustable Dumbbell Set (2x5kg).jpg",
        "is_sold": False,
        "buyer_email": None,
        "days_ago_claimed": None,
        "days_active_before_claim": None,
        "days_ago_listed": 40,
    },
    {
        "title": "Tennis Racket (Wilson Clash 100)",
        "description": (
            "Intermediate-level racket, good condition. Restrung approximately 8 months ago. "
            "Comes with the original Wilson cover. Perfect for casual play on the Brookes courts. "
            "Grip size 3 (4 3/8 inches)."
        ),
        "category": "Sports",
        "condition": "Good",
        "price": 30.00,
        "is_free": False,
        "seller_email": "d.park@brookes.ac.uk",
        "image_file": "Tennis Racket (Wilson Clash 100).jpg",
        "is_sold": False,
        "buyer_email": None,
        "days_ago_claimed": None,
        "days_active_before_claim": None,
        "days_ago_listed": 5,
    },

    # ── Stationery (2 items: 0 sold, 2 active) ──
    {
        "title": "Giant Stationery Bundle (30+ Items)",
        "description": (
            "Enough to last a whole academic year: Staedtler pens (x10), Muji mechanical pencils (x3), "
            "a Leuchtturm1917 A5 notebook, Pritt Sticks (x4), A4 ring binders (x3), dividers, "
            "and assorted highlighters. All brand new and unused — never opened some packs. "
            "Happy to donate, just collect from Gipsy Lane."
        ),
        "category": "Stationery",
        "condition": "New",
        "price": 0.0,
        "is_free": True,
        "seller_email": "p.nair@brookes.ac.uk",
        "image_file": "Giant Stationery Bundle (30+ Items).jpg",
        "is_sold": False,
        "buyer_email": None,
        "days_ago_claimed": None,
        "days_active_before_claim": None,
        "days_ago_listed": 2,
    },
    {
        "title": "A2 Whiteboard (Self-Adhesive)",
        "description": (
            "Stick-and-remove A2 whiteboard sheet — attaches to any smooth wall surface and peels off cleanly. "
            "Ideal for revision mind maps, semester planning, and timetables on your bedroom wall. "
            "Like new — used twice. Comes with 2 dry-wipe markers."
        ),
        "category": "Stationery",
        "condition": "Like New",
        "price": 6.00,
        "is_free": False,
        "seller_email": "c.fraser@brookes.ac.uk",
        "image_file": "A2 Whiteboard (Self-Adhesive).jpg",
        "is_sold": False,
        "buyer_email": None,
        "days_ago_claimed": None,
        "days_active_before_claim": None,
        "days_ago_listed": 8,
    },

    # ── Other (2 items: 1 sold, 1 active) ──
    {
        "title": "Mini Portable Fan (USB-A)",
        "description": (
            "Absolute lifesaver in the Headington halls during September and early October. "
            "3 speed settings, near-silent operation, and folds flat for easy storage. "
            "USB-A powered — works from any laptop or USB charger. "
            "Selling as I've finished my first year."
        ),
        "category": "Other",
        "condition": "Good",
        "price": 5.00,
        "is_free": False,
        "seller_email": "j.whitfield@brookes.ac.uk",
        "image_file": "Mini Portable Fan (USB-A).jpg",
        "is_sold": True,
        "buyer_email": "p.nair@brookes.ac.uk",
        "days_ago_claimed": 20,
        "days_active_before_claim": 5,
        "days_ago_listed": None,
    },
    {
        "title": "Extension Lead 4-Gang (3m, Surge Protected)",
        "description": (
            "The single most important item for a student room — 4 sockets and 3 metres of cable "
            "lets you charge everything from one wall socket. "
            "Surge protection built-in. Works perfectly. "
            "Selling as I'm moving somewhere with more sockets."
        ),
        "category": "Other",
        "condition": "Good",
        "price": 7.00,
        "is_free": False,
        "seller_email": "t.keller@brookes.ac.uk",
        "image_file": "Extension Lead 4-Gang (3m, Surge Protected).jpg",
        "is_sold": False,
        "buyer_email": None,
        "days_ago_claimed": None,
        "days_active_before_claim": None,
        "days_ago_listed": 35,
    },
    # ── Oxford Demo Items ──
    {
        "title": "Oxford Leather College Chair",
        "description": (
            "Classic dark wood and leather library chair. Very comfortable and solid. "
            "Has some minor wear on the arms but fits perfectly in any study room."
        ),
        "category": "Furniture",
        "condition": "Good",
        "price": 20.00,
        "is_free": False,
        "seller_email": "w.churchill@ox.ac.uk",
        "image_file": "oxford_chair.jpg",
        "is_sold": False,
        "buyer_email": None,
        "days_ago_claimed": None,
        "days_active_before_claim": None,
        "days_ago_listed": 4,
    },
    {
        "title": "Introduction to Algorithms (CLRS) 4th Edition",
        "description": (
            "The bible of computer science. Clean copy, no highlighting or annotations. "
            "Practically brand new, required for CS students."
        ),
        "category": "Books",
        "condition": "New",
        "price": 15.00,
        "is_free": False,
        "seller_email": "a.turing@ox.ac.uk",
        "image_file": "clrs_book.jpg",
        "is_sold": False,
        "buyer_email": None,
        "days_ago_claimed": None,
        "days_active_before_claim": None,
        "days_ago_listed": 2,
    },
    {
        "title": "Custom Mechanical Keyboard (Brown Switches)",
        "description": (
            "Keychron K2 with tactile Gateron Brown switches. Bluetooth and wired modes. "
            "RGB backlighting. Includes original keycaps and keycap puller."
        ),
        "category": "Electronics",
        "condition": "Like New",
        "price": 30.00,
        "is_free": False,
        "seller_email": "a.turing@ox.ac.uk",
        "image_file": "keychron_keyboard.jpg",
        "is_sold": True,
        "buyer_email": "m.thatcher@ox.ac.uk",
        "days_ago_claimed": 3,
        "days_active_before_claim": 5,
        "days_ago_listed": 8,
    },
    {
        "title": "Oxford Graduation Gown and Cap Bundle",
        "description": (
            "Official sub-fusc graduation gown and mortarboard cap. "
            "Worn once. Fit for medium height (approx 170-180cm). "
            "Giving away for free to anyone who needs it for their upcoming ceremony."
        ),
        "category": "Clothing",
        "condition": "Like New",
        "price": 0.00,
        "is_free": True,
        "seller_email": "m.thatcher@ox.ac.uk",
        "image_file": "gown_bundle.jpg",
        "is_sold": False,
        "buyer_email": None,
        "days_ago_claimed": None,
        "days_active_before_claim": None,
        "days_ago_listed": 6,
    },
    {
        "title": "Vintage Porcelain Tea Set",
        "description": (
            "Includes teapot, 4 cups, and saucers. Beautiful floral pattern with gold details. "
            "No chips or cracks."
        ),
        "category": "Kitchenware",
        "condition": "Good",
        "price": 10.00,
        "is_free": False,
        "seller_email": "w.churchill@ox.ac.uk",
        "image_file": "tea_set.jpg",
        "is_sold": False,
        "buyer_email": None,
        "days_ago_claimed": None,
        "days_active_before_claim": None,
        "days_ago_listed": 5,
    },
    # ── Cambridge Active Season Item ──
    {
        "title": "Cambridge Science Lab Coat",
        "description": "Clean white lab coat, size L. Essential for physics and chemistry labs.",
        "category": "Clothing",
        "condition": "Like New",
        "price": 0.00,
        "is_free": True,
        "seller_email": "i.newton@cam.ac.uk",
        "image_file": "labcoat.jpg",
        "is_sold": True,
        "buyer_email": "c.darwin@cam.ac.uk",
        "days_ago_claimed": 12,
        "days_active_before_claim": 2,
        "days_ago_listed": None,
    },
    # ── Spring Term 2026 Past Season Items (between 31 and 120 days ago) ──
    {
        "title": "Organic Chemistry Textbook",
        "description": "Standard study guide for first year courses. Very neat.",
        "category": "Books",
        "condition": "Good",
        "price": 15.00,
        "is_free": False,
        "seller_email": "a.rahman@brookes.ac.uk",
        "image_file": "chemistry_book.jpg",
        "is_sold": True,
        "buyer_email": "j.whitfield@brookes.ac.uk",
        "days_ago_claimed": 45,
        "days_active_before_claim": 5,
        "days_ago_listed": None,
    },
    {
        "title": "Solid Oak Dining Chair",
        "description": "Sturdy student desk chair. Dark oak finish.",
        "category": "Furniture",
        "condition": "Good",
        "price": 20.00,
        "is_free": False,
        "seller_email": "w.churchill@ox.ac.uk",
        "image_file": "oak_chair.jpg",
        "is_sold": True,
        "buyer_email": "m.thatcher@ox.ac.uk",
        "days_ago_claimed": 50,
        "days_active_before_claim": 4,
        "days_ago_listed": None,
    },
    {
        "title": "Optics Lab Prism Kit",
        "description": "Refraction glass prisms in a protective velvet box.",
        "category": "Electronics",
        "condition": "Like New",
        "price": 10.00,
        "is_free": False,
        "seller_email": "i.newton@cam.ac.uk",
        "image_file": "prism_kit.jpg",
        "is_sold": True,
        "buyer_email": "c.darwin@cam.ac.uk",
        "days_ago_claimed": 60,
        "days_active_before_claim": 3,
        "days_ago_listed": None,
    },
    # ── Spring Term 2026 Additional Items for Standings Balance ──
    {
        "title": "Spring Wardrobe Brookes 1",
        "description": "Large wooden wardrobe.",
        "category": "Furniture",
        "condition": "Good",
        "price": 0.0,
        "is_free": True,
        "seller_email": "a.rahman@brookes.ac.uk",
        "image_file": "wardrobe.jpg",
        "is_sold": True,
        "buyer_email": "j.whitfield@brookes.ac.uk",
        "days_ago_claimed": 50,
        "days_active_before_claim": 5,
        "days_ago_listed": None,
    },
    {
        "title": "Spring Desk Brookes 2",
        "description": "Wooden writing desk.",
        "category": "Furniture",
        "condition": "Good",
        "price": 0.0,
        "is_free": True,
        "seller_email": "j.whitfield@brookes.ac.uk",
        "image_file": "desk.jpg",
        "is_sold": True,
        "buyer_email": "a.rahman@brookes.ac.uk",
        "days_ago_claimed": 52,
        "days_active_before_claim": 4,
        "days_ago_listed": None,
    },
    {
        "title": "Spring Sofa Brookes 3",
        "description": "Two-seater fabric sofa.",
        "category": "Furniture",
        "condition": "Good",
        "price": 0.0,
        "is_free": True,
        "seller_email": "p.nair@brookes.ac.uk",
        "image_file": "sofa.jpg",
        "is_sold": True,
        "buyer_email": "c.fraser@brookes.ac.uk",
        "days_ago_claimed": 54,
        "days_active_before_claim": 3,
        "days_ago_listed": None,
    },
    {
        "title": "Spring Bookshelf Brookes 4",
        "description": "Tall wooden bookshelf.",
        "category": "Furniture",
        "condition": "Good",
        "price": 0.0,
        "is_free": True,
        "seller_email": "c.fraser@brookes.ac.uk",
        "image_file": "bookshelf.jpg",
        "is_sold": True,
        "buyer_email": "p.nair@brookes.ac.uk",
        "days_ago_claimed": 56,
        "days_active_before_claim": 5,
        "days_ago_listed": None,
    },
    {
        "title": "Spring Armchair Brookes 5",
        "description": "Comfortable reading armchair.",
        "category": "Furniture",
        "condition": "Good",
        "price": 0.0,
        "is_free": True,
        "seller_email": "m.zhou@brookes.ac.uk",
        "image_file": "armchair.jpg",
        "is_sold": True,
        "buyer_email": "t.keller@brookes.ac.uk",
        "days_ago_claimed": 58,
        "days_active_before_claim": 4,
        "days_ago_listed": None,
    },
    {
        "title": "Spring Microwave Brookes 6",
        "description": "Digital microwave oven.",
        "category": "Electronics",
        "condition": "Good",
        "price": 0.0,
        "is_free": True,
        "seller_email": "t.keller@brookes.ac.uk",
        "image_file": "microwave.jpg",
        "is_sold": True,
        "buyer_email": "m.zhou@brookes.ac.uk",
        "days_ago_claimed": 48,
        "days_active_before_claim": 3,
        "days_ago_listed": None,
    },
    {
        "title": "Spring Monitor Brookes 7",
        "description": "24 inch HD monitor.",
        "category": "Electronics",
        "condition": "Good",
        "price": 0.0,
        "is_free": True,
        "seller_email": "f.alamin@brookes.ac.uk",
        "image_file": "monitor.jpg",
        "is_sold": True,
        "buyer_email": "s.osei@brookes.ac.uk",
        "days_ago_claimed": 51,
        "days_active_before_claim": 5,
        "days_ago_listed": None,
    },
    {
        "title": "Spring Vacuum Brookes 8",
        "description": "Cordless vacuum cleaner.",
        "category": "Electronics",
        "condition": "Good",
        "price": 0.0,
        "is_free": True,
        "seller_email": "s.osei@brookes.ac.uk",
        "image_file": "vacuum.jpg",
        "is_sold": True,
        "buyer_email": "f.alamin@brookes.ac.uk",
        "days_ago_claimed": 53,
        "days_active_before_claim": 4,
        "days_ago_listed": None,
    },
    {
        "title": "Spring Coffee Table Brookes 9",
        "description": "Small wooden coffee table.",
        "category": "Furniture",
        "condition": "Good",
        "price": 0.0,
        "is_free": True,
        "seller_email": "i.constantin@brookes.ac.uk",
        "image_file": "coffee_table.jpg",
        "is_sold": True,
        "buyer_email": "r.marsh@brookes.ac.uk",
        "days_ago_claimed": 55,
        "days_active_before_claim": 3,
        "days_ago_listed": None,
    },
    {
        "title": "Spring Dining Table Brookes 10",
        "description": "Dining table with four chairs.",
        "category": "Furniture",
        "condition": "Good",
        "price": 0.0,
        "is_free": True,
        "seller_email": "r.marsh@brookes.ac.uk",
        "image_file": "dining_table.jpg",
        "is_sold": True,
        "buyer_email": "i.constantin@brookes.ac.uk",
        "days_ago_claimed": 57,
        "days_active_before_claim": 5,
        "days_ago_listed": None,
    },
    {
        "title": "Spring Study Chair Oxford 1",
        "description": "Comfortable computer chair.",
        "category": "Furniture",
        "condition": "Good",
        "price": 0.0,
        "is_free": True,
        "seller_email": "m.thatcher@ox.ac.uk",
        "image_file": "study_chair.jpg",
        "is_sold": True,
        "buyer_email": "w.churchill@ox.ac.uk",
        "days_ago_claimed": 52,
        "days_active_before_claim": 4,
        "days_ago_listed": None,
    },
    {
        "title": "Spring Desk Lamp Oxford 2",
        "description": "Adjustable LED desk lamp.",
        "category": "Electronics",
        "condition": "Good",
        "price": 0.0,
        "is_free": True,
        "seller_email": "a.turing@ox.ac.uk",
        "image_file": "desk_lamp.jpg",
        "is_sold": True,
        "buyer_email": "m.thatcher@ox.ac.uk",
        "days_ago_claimed": 54,
        "days_active_before_claim": 3,
        "days_ago_listed": None,
    },
    # ── Autumn Term 2025 Past Season Items (between 210 and 300 days ago) ──
    {
        "title": "Autumn Wardrobe Brookes 1",
        "description": "Large double wardrobe.",
        "category": "Furniture",
        "condition": "Good",
        "price": 0.0,
        "is_free": True,
        "seller_email": "a.rahman@brookes.ac.uk",
        "image_file": "wardrobe_autumn.jpg",
        "is_sold": True,
        "buyer_email": "j.whitfield@brookes.ac.uk",
        "days_ago_claimed": 230,
        "days_active_before_claim": 5,
        "days_ago_listed": None,
    },
    {
        "title": "Autumn Writing Desk Brookes 2",
        "description": "Solid pine writing desk.",
        "category": "Furniture",
        "condition": "Good",
        "price": 0.0,
        "is_free": True,
        "seller_email": "j.whitfield@brookes.ac.uk",
        "image_file": "desk_autumn.jpg",
        "is_sold": True,
        "buyer_email": "a.rahman@brookes.ac.uk",
        "days_ago_claimed": 232,
        "days_active_before_claim": 4,
        "days_ago_listed": None,
    },
    {
        "title": "Autumn Chest of Drawers Brookes 3",
        "description": "3-drawer chest for clothing storage.",
        "category": "Furniture",
        "condition": "Good",
        "price": 0.0,
        "is_free": True,
        "seller_email": "p.nair@brookes.ac.uk",
        "image_file": "drawers_autumn.jpg",
        "is_sold": True,
        "buyer_email": "c.fraser@brookes.ac.uk",
        "days_ago_claimed": 234,
        "days_active_before_claim": 3,
        "days_ago_listed": None,
    },
    {
        "title": "Autumn Bedside Table Brookes 4",
        "description": "Small bedside table with drawer.",
        "category": "Furniture",
        "condition": "Good",
        "price": 0.0,
        "is_free": True,
        "seller_email": "c.fraser@brookes.ac.uk",
        "image_file": "table_autumn.jpg",
        "is_sold": True,
        "buyer_email": "p.nair@brookes.ac.uk",
        "days_ago_claimed": 236,
        "days_active_before_claim": 5,
        "days_ago_listed": None,
    },
    {
        "title": "Autumn Kettle Brookes 5",
        "description": "Electric water kettle.",
        "category": "Electronics",
        "condition": "Good",
        "price": 0.0,
        "is_free": True,
        "seller_email": "m.zhou@brookes.ac.uk",
        "image_file": "kettle_autumn.jpg",
        "is_sold": True,
        "buyer_email": "t.keller@brookes.ac.uk",
        "days_ago_claimed": 238,
        "days_active_before_claim": 4,
        "days_ago_listed": None,
    },
    {
        "title": "Autumn Toaster Brookes 6",
        "description": "2-slice bread toaster.",
        "category": "Electronics",
        "condition": "Good",
        "price": 0.0,
        "is_free": True,
        "seller_email": "t.keller@brookes.ac.uk",
        "image_file": "toaster_autumn.jpg",
        "is_sold": True,
        "buyer_email": "m.zhou@brookes.ac.uk",
        "days_ago_claimed": 240,
        "days_active_before_claim": 3,
        "days_ago_listed": None,
    },
    {
        "title": "Autumn Bookcase Oxford 1",
        "description": "Medium size oak bookcase.",
        "category": "Furniture",
        "condition": "Good",
        "price": 0.0,
        "is_free": True,
        "seller_email": "w.churchill@ox.ac.uk",
        "image_file": "bookcase_ox_autumn.jpg",
        "is_sold": True,
        "buyer_email": "m.thatcher@ox.ac.uk",
        "days_ago_claimed": 235,
        "days_active_before_claim": 5,
        "days_ago_listed": None,
    },
    {
        "title": "Autumn Study Table Cambridge 1",
        "description": "Foldable study table.",
        "category": "Furniture",
        "condition": "Good",
        "price": 0.0,
        "is_free": True,
        "seller_email": "i.newton@cam.ac.uk",
        "image_file": "table_cam_autumn.jpg",
        "is_sold": True,
        "buyer_email": "c.darwin@cam.ac.uk",
        "days_ago_claimed": 242,
        "days_active_before_claim": 4,
        "days_ago_listed": None,
    },
]

SAMPLE_CANCELLATIONS = [
    {
        # Clean cancellation: Mei-Ling briefly claimed the desk lamp then cancelled within 24h.
        # The item remains active/unsold — this is just a historical audit record.
        "item_title": "Ring LED Desk Lamp (USB-C)",
        "cancelled_by_email": "m.zhou@brookes.ac.uk",
        "other_party_email": "r.marsh@brookes.ac.uk",
        "hours_held": 12.0,
        "tier": "clean",
        "cancelled_by_role": "buyer",
        "hours_ago_claimed": 18,
        "hours_ago_cancelled": 6,
    },
    {
        # Late cancellation: Samuel claimed the mattress but cancelled after 52 hours (past 24h mark).
        # The item remains active/unsold — this is just a historical audit record.
        "item_title": "Single Mattress (Memory Foam, 3ft)",
        "cancelled_by_email": "s.osei@brookes.ac.uk",
        "other_party_email": "o.hurst@brookes.ac.uk",
        "hours_held": 52.0,
        "tier": "late",
        "cancelled_by_role": "buyer",
        "hours_ago_claimed": 62,
        "hours_ago_cancelled": 10,
    },
]


def seed():
    """Drop all tables and repopulate with demo data."""
    with app.app_context():
        random.seed(42)

        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()

        # Clean up existing files in the uploads folder or R2 bucket
        print("Cleaning up uploads directory...")
        if app.config.get("STORAGE_PROVIDER", "local") == "r2":
            cleanup_r2_uploads()
        elif os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"  [WARN] Failed to delete {file_path}: {e}")

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Create default university configs
        print("Seeding university configs...")
        brookes_cfg = UniversityConfig(
            domain="brookes.ac.uk",
            subdomain_slug="brookes",
            display_name="Oxford Brookes University",
            short_name="Brookes",
            email_domain="brookes.ac.uk",
            timezone="Europe/London",
            logo_status="fetched"
        )
        oxford_cfg = UniversityConfig(
            domain="ox.ac.uk",
            subdomain_slug="oxford",
            display_name="Oxford University",
            short_name="Oxford",
            email_domain="ox.ac.uk",
            timezone="Europe/London",
            logo_status="fetched"
        )
        cambridge_cfg = UniversityConfig(
            domain="cam.ac.uk",
            subdomain_slug="cambridge",
            display_name="Cambridge University",
            short_name="Cambridge",
            email_domain="cam.ac.uk",
            timezone="Europe/London",
            logo_status="fetched"
        )
        db.session.add_all([brookes_cfg, oxford_cfg, cambridge_cfg])

        # Create active seasons
        print("Seeding active seasons...")
        brookes_season = Season(
            university_domain="brookes.ac.uk",
            name="Autumn Term 2026",
            start_date=now - timedelta(days=30),
            end_date=now + timedelta(days=60),
            is_active=True,
            is_complete=False
        )
        oxford_season = Season(
            university_domain="ox.ac.uk",
            name="Autumn Term 2026",
            start_date=now - timedelta(days=30),
            end_date=now + timedelta(days=60),
            is_active=True,
            is_complete=False
        )
        cambridge_season = Season(
            university_domain="cam.ac.uk",
            name="Autumn Term 2026",
            start_date=now - timedelta(days=30),
            end_date=now + timedelta(days=60),
            is_active=True,
            is_complete=False
        )
        db.session.add_all([brookes_season, oxford_season, cambridge_season])

        # Create users
        users = {}  # dict mapping email -> User object

        for u_data in SAMPLE_USERS:
            domain = extract_university_domain(u_data["email"])

            # Determine created_at timestamp: must predate their oldest item activity
            min_days = 0
            for i_data in SAMPLE_ITEMS:
                if i_data["seller_email"] == u_data["email"]:
                    if i_data.get("is_sold"):
                        item_age = i_data["days_ago_claimed"] + i_data["days_active_before_claim"]
                    else:
                        item_age = i_data["days_ago_listed"]
                    min_days = max(min_days, item_age + 2)
                if i_data.get("buyer_email") == u_data["email"] and i_data.get("is_sold"):
                    claim_age = i_data["days_ago_claimed"]
                    min_days = max(min_days, claim_age + 2)

            if u_data["role"] == "admin":
                user_created_at = now - timedelta(days=max(90, min_days))
            elif u_data["role"] == "partner":
                user_created_at = now - timedelta(days=max(80, min_days))
            else:
                # Students: random spread across past 30 to 90 days
                start_days = max(30, min_days)
                end_days = max(90, start_days + 10)
                user_created_at = now - timedelta(days=random.randint(start_days, end_days))

            user = User(
                email=u_data["email"],
                name=u_data["name"],
                university_domain=domain,
                is_verified=True,
                role=u_data["role"],
                partner_university=u_data["partner_university"],
                is_active=True,
                created_at=user_created_at,
            )
            user.set_password(u_data["password"])
            db.session.add(user)
            users[u_data["email"]] = user
            print(f"  Created user: {u_data['email']} ({u_data['role']})")

        # Commit users, configs, and seasons so connection is not left idle in transaction
        db.session.commit()
        print(f"Committed {len(users)} users, configs, and seasons.")

        # Pre-process listing images outside active DB transaction to avoid PostgreSQL timeouts
        print("Preparing listing images...")
        item_images = {}
        for i_data in SAMPLE_ITEMS:
            item_images[i_data["title"]] = copy_seed_image(
                i_data["image_file"],
                i_data["category"],
                i_data["title"],
            )
        print(f"Prepared {len(item_images)} listing images.")

        # Create items
        items_by_title = {}  # dict mapping item title -> Item object

        for i_data in SAMPLE_ITEMS:
            seller = users[i_data["seller_email"]]
            kg = CATEGORY_WEIGHTS.get(i_data["category"], 1.0)
            image_filename = item_images[i_data["title"]]

            # Calculate timestamps
            if i_data["is_sold"]:
                # Claimed_at = now minus days_ago_claimed
                claimed_at = now - timedelta(days=i_data["days_ago_claimed"])
                # Item was listed days_active_before_claim before being claimed
                item_created_at = claimed_at - timedelta(days=i_data["days_active_before_claim"])
                buyer = users[i_data["buyer_email"]]
                buyer_id = buyer.id
            else:
                claimed_at = None
                item_created_at = now - timedelta(days=i_data["days_ago_listed"])
                buyer_id = None

            item = Item(
                title=i_data["title"],
                description=i_data["description"],
                category=i_data["category"],
                condition=i_data["condition"],
                price=i_data["price"],
                is_free=i_data["is_free"],
                image_filename=image_filename,
                kg_saved=kg,
                seller_id=seller.id,
                university_domain=seller.university_domain,
                is_sold=i_data["is_sold"],
                buyer_id=buyer_id,
                claimed_at=claimed_at,
                sold_at=claimed_at if i_data["is_sold"] else None,
                created_at=item_created_at,
            )
            db.session.add(item)
            items_by_title[i_data["title"]] = item
            status = "SOLD" if i_data["is_sold"] else "active"
            print(f"  Created item [{status}]: {i_data['title']}")

        # Commit items
        db.session.commit()
        print(f"Committed {len(items_by_title)} items.")

        # ── Dynamic Seeding for Leaderboard Edge Cases ──
        print("Dynamically seeding leaderboard test cases...")
        
        used_names = {u["name"] for u in SAMPLE_USERS}
        def get_unique_name():
            for _ in range(200):
                name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
                if name not in used_names:
                    used_names.add(name)
                    return name
            return f"Student {random.randint(1000, 9999)}"

        # 1. Cambridge (Small list: 2 users to suppress podium)
        cam_student1 = users["i.newton@cam.ac.uk"]
        cam_student2 = users["c.darwin@cam.ac.uk"]
        
        item_cam1 = Item(
            title="Physics Lab Ruler",
            description="30cm steel ruler.",
            category="Stationery",
            condition="Good",
            price=0.0,
            is_free=True,
            kg_saved=1.5,
            seller_id=cam_student1.id,
            buyer_id=cam_student2.id,
            claimed_at=now - timedelta(days=2, hours=4),
            university_domain="cam.ac.uk",
            is_sold=True,
            sold_at=now - timedelta(days=2),
            created_at=now - timedelta(days=5)
        )
        item_cam2 = Item(
            title="Biology Notebook",
            description="A4 spiral notebook.",
            category="Stationery",
            condition="Like New",
            price=0.0,
            is_free=True,
            kg_saved=0.8,
            seller_id=cam_student2.id,
            buyer_id=cam_student1.id,
            claimed_at=now - timedelta(days=3, hours=4),
            university_domain="cam.ac.uk",
            is_sold=True,
            sold_at=now - timedelta(days=3),
            created_at=now - timedelta(days=5)
        )
        db.session.add_all([item_cam1, item_cam2])
        
        # 2. Oxford (Medium list: 5 users to show podium and short list)
        ox_student1 = users["w.churchill@ox.ac.uk"]
        ox_student2 = users["m.thatcher@ox.ac.uk"]
        ox_student3 = users["a.turing@ox.ac.uk"]
        
        # Add current week transactions for existing Oxford students
        ox_students = [ox_student1, ox_student2, ox_student3]
        for i, u in enumerate(ox_students, start=1):
            buyer = ox_students[(i) % len(ox_students)]
            item_ox = Item(
                title=f"Oxford Study Guide {i}",
                description="Study materials for the term.",
                category="Books",
                condition="Good",
                price=0.0,
                is_free=True,
                kg_saved=4.0 + i,
                seller_id=u.id,
                buyer_id=buyer.id,
                claimed_at=now - timedelta(days=2, hours=4),
                university_domain="ox.ac.uk",
                is_sold=True,
                sold_at=now - timedelta(days=2),
                created_at=now - timedelta(days=5)
            )
            db.session.add(item_ox)
            
        # Dynamically create 2 more Oxford students and transactions
        for i in range(4, 6):
            name = get_unique_name()
            first, last = name.split()[0], name.split()[1]
            email = f"{first.lower()}.{last.lower()}{random.randint(10,99)}@ox.ac.uk"
            
            ox_u = User(
                email=email,
                name=name,
                university_domain="ox.ac.uk",
                is_verified=True,
                role="student",
                is_active=True,
                created_at=now - timedelta(days=40)
            )
            ox_u.set_password("BrookesDemo1")
            db.session.add(ox_u)
            db.session.flush()
            
            item_ox = Item(
                title=f"Oxford Study Accessory {i}",
                description="Stationery item.",
                category="Stationery",
                condition="Good",
                price=0.0,
                is_free=True,
                kg_saved=1.0 + (i * 0.2),
                seller_id=ox_u.id,
                buyer_id=ox_student1.id,
                claimed_at=now - timedelta(days=2, hours=4),
                university_domain="ox.ac.uk",
                is_sold=True,
                sold_at=now - timedelta(days=2),
                created_at=now - timedelta(days=5)
            )
            db.session.add(item_ox)
            
        # 3. Brookes (Large list: 50+ users to show pagination and podium)
        # Generate 45 additional Brookes students with transactions this week
        brookes_buyer_pool = [
            u for email, u in users.items() if email.endswith("@brookes.ac.uk") and u.role == "student"
        ]
        for i in range(1, 46):
            name = get_unique_name()
            first, last = name.split()[0], name.split()[1]
            email = f"{first.lower()}.{last.lower()}{random.randint(10,99)}@brookes.ac.uk"
            
            b_u = User(
                email=email,
                name=name,
                university_domain="brookes.ac.uk",
                is_verified=True,
                role="student",
                is_active=True,
                created_at=now - timedelta(days=40)
            )
            b_u.set_password("BrookesDemo1")
            db.session.add(b_u)
            db.session.flush()
            
            # Save between 1.5 and 5.0 kg
            kg = round(1.5 + (i * 0.08), 2)
            item_b = Item(
                title=f"Brookes Generated Item {i}",
                description="Household item from student dorm.",
                category="Kitchenware",
                condition="Good",
                price=0.0,
                is_free=True,
                kg_saved=kg,
                seller_id=b_u.id,
                buyer_id=random.choice(brookes_buyer_pool).id,
                claimed_at=now - timedelta(days=1, hours=4),
                university_domain="brookes.ac.uk",
                is_sold=True,
                sold_at=now - timedelta(days=1),
                created_at=now - timedelta(days=5)
            )
            db.session.add(item_b)

        db.session.commit()
        print("Committed leaderboard edge cases.")

        # Create cancellation records
        for c_data in SAMPLE_CANCELLATIONS:
            item = items_by_title[c_data["item_title"]]
            cancelled_by = users[c_data["cancelled_by_email"]]
            other_party = users[c_data["other_party_email"]]

            record = CancellationRecord(
                item_id=item.id,
                cancelled_by_id=cancelled_by.id,
                other_party_id=other_party.id,
                claimed_at=now - timedelta(hours=c_data["hours_ago_claimed"]),
                cancelled_at=now - timedelta(hours=c_data["hours_ago_cancelled"]),
                hours_held=c_data["hours_held"],
                tier=c_data["tier"],
                cancelled_by_role=c_data["cancelled_by_role"],
            )
            db.session.add(record)
            print(f"  Created cancellation record: {c_data['tier']} - {c_data['item_title']}")

        # Seed chat messages for demo items to demonstrate in-app messaging
        print("Seeding sample chat conversations...")
        sample_threads = [
            {
                "item_title": "MacBook Air M2 (2022) 8GB/256GB",
                "messages": [
                    ("j.whitfield@brookes.ac.uk", "Hi Aisha, is this still available to collect on campus?", 45),
                    ("a.rahman@brookes.ac.uk", "Hi Jack! Yes, I can meet at the Headington campus library entrance tomorrow afternoon.", 35),
                    ("j.whitfield@brookes.ac.uk", "That works for me! Say 2:30 PM?", 25),
                    ("a.rahman@brookes.ac.uk", "Perfect, see you then! I'll have the original box and charger ready.", 15),
                ],
            },
            {
                "item_title": "Casio fx-991EX ClassWiz Calculator",
                "messages": [
                    ("p.nair@brookes.ac.uk", "Hey Callum, I urgently need this for my maths module next week. When are you free?", 60),
                    ("c.fraser@brookes.ac.uk", "Hey Priya! I'm in the Clerici building until 4pm today if you're nearby.", 40),
                    ("p.nair@brookes.ac.uk", "Amazing! I'll head over to the ground floor cafe in 10 minutes.", 20),
                    ("c.fraser@brookes.ac.uk", "Sounds great, I'm wearing a green hoodie.", 15),
                ],
            },
            {
                "item_title": "IKEA KALLAX 4-Cube Shelf (White)",
                "messages": [
                    ("i.constantin@brookes.ac.uk", "Hi Jack, is the shelf already disassembled or will I need an Allen key?", 50),
                    ("j.whitfield@brookes.ac.uk", "Hi Ioana, it's already completely disassembled with all the screws in a bag!", 35),
                    ("i.constantin@brookes.ac.uk", "Awesome, thank you so much! I can swing by Harcourt Hill with a car around 5pm.", 25),
                    ("j.whitfield@brookes.ac.uk", "Great, I'll bring it down to the visitor parking bay.", 15),
                ],
            },
        ]

        for thread in sample_threads:
            item = items_by_title.get(thread["item_title"])
            if not item or not item.buyer_id:
                continue
            seller_id = item.seller_id
            buyer_id = item.buyer_id
            for sender_email, text, mins_ago in thread["messages"]:
                sender = users.get(sender_email)
                if not sender:
                    continue
                recipient_id = buyer_id if sender.id == seller_id else seller_id
                msg = Message(
                    item_id=item.id,
                    sender_id=sender.id,
                    recipient_id=recipient_id,
                    content=text,
                    is_read=True,
                    created_at=now - timedelta(minutes=mins_ago)
                )
                db.session.add(msg)
        db.session.commit()
        print("  Created sample chat message threads and committed.")

        # Update kg_saved_total on each user dynamically from DB sold items (Anti-drift)
        all_sold_items = Item.query.filter_by(is_sold=True).all()
        user_kg_totals = {}
        for item in all_sold_items:
            user_kg_totals[item.seller_id] = user_kg_totals.get(item.seller_id, 0.0) + float(item.kg_saved)

        all_users = User.query.all()
        for u in all_users:
            total_kg = user_kg_totals.get(u.id, 0.0)
            u.kg_saved_total = round(total_kg, 2)
            if total_kg > 0:
                print(f"  Updated kg_saved_total for {u.email}: {u.kg_saved_total} kg")

        # Seed completed season & historical snapshots for Hall of Fame demonstration
        print("Seeding completed seasons and snapshots for Hall of Fame...")
        past_season = Season(
            university_domain="brookes.ac.uk",
            name="Spring Term 2026",
            start_date=now - timedelta(days=120),
            end_date=now - timedelta(days=31),
            is_active=False,
            is_complete=True
        )
        past_season_ox = Season(
            university_domain="ox.ac.uk",
            name="Spring Term 2026",
            start_date=now - timedelta(days=120),
            end_date=now - timedelta(days=31),
            is_active=False,
            is_complete=True
        )
        past_season_cam = Season(
            university_domain="cam.ac.uk",
            name="Spring Term 2026",
            start_date=now - timedelta(days=120),
            end_date=now - timedelta(days=31),
            is_active=False,
            is_complete=True
        )
        # Autumn Term 2025 (Previous academic year)
        past_season_autumn = Season(
            university_domain="brookes.ac.uk",
            name="Autumn Term 2025",
            start_date=now - timedelta(days=300),
            end_date=now - timedelta(days=210),
            is_active=False,
            is_complete=True
        )
        past_season_autumn_ox = Season(
            university_domain="ox.ac.uk",
            name="Autumn Term 2025",
            start_date=now - timedelta(days=300),
            end_date=now - timedelta(days=210),
            is_active=False,
            is_complete=True
        )
        past_season_autumn_cam = Season(
            university_domain="cam.ac.uk",
            name="Autumn Term 2025",
            start_date=now - timedelta(days=300),
            end_date=now - timedelta(days=210),
            is_active=False,
            is_complete=True
        )
        db.session.add_all([
            past_season, past_season_ox, past_season_cam,
            past_season_autumn, past_season_autumn_ox, past_season_autumn_cam
        ])
        db.session.flush()

        # Seed seasonal snapshots for Spring Term 2026
        s_snap1 = SeasonalSnapshot(
            season_id=past_season.id,
            university_domain="brookes.ac.uk",
            user_id=users["j.whitfield@brookes.ac.uk"].id,
            display_name=users["j.whitfield@brookes.ac.uk"].name,
            kg_saved=84.5,
            transaction_count=12,
            rank=1
        )
        s_snap2 = SeasonalSnapshot(
            season_id=past_season.id,
            university_domain="brookes.ac.uk",
            user_id=users["s.osei@brookes.ac.uk"].id,
            display_name=users["s.osei@brookes.ac.uk"].name,
            kg_saved=62.0,
            transaction_count=8,
            rank=2
        )
        s_snap3 = SeasonalSnapshot(
            season_id=past_season.id,
            university_domain="brookes.ac.uk",
            user_id=users["a.rahman@brookes.ac.uk"].id,
            display_name=users["a.rahman@brookes.ac.uk"].name,
            kg_saved=48.2,
            transaction_count=6,
            rank=3
        )

        # Seed seasonal snapshots for Autumn Term 2025
        s_snap_autumn1 = SeasonalSnapshot(
            season_id=past_season_autumn.id,
            university_domain="brookes.ac.uk",
            user_id=users["p.nair@brookes.ac.uk"].id,
            display_name=users["p.nair@brookes.ac.uk"].name,
            kg_saved=82.1,
            transaction_count=15,
            rank=1
        )
        s_snap_autumn2 = SeasonalSnapshot(
            season_id=past_season_autumn.id,
            university_domain="brookes.ac.uk",
            user_id=users["a.rahman@brookes.ac.uk"].id,
            display_name=users["a.rahman@brookes.ac.uk"].name,
            kg_saved=59.4,
            transaction_count=10,
            rank=2
        )
        s_snap_autumn3 = SeasonalSnapshot(
            season_id=past_season_autumn.id,
            university_domain="brookes.ac.uk",
            user_id=users["s.osei@brookes.ac.uk"].id,
            display_name=users["s.osei@brookes.ac.uk"].name,
            kg_saved=41.0,
            transaction_count=6,
            rank=3
        )
        db.session.add_all([
            s_snap1, s_snap2, s_snap3,
            s_snap_autumn1, s_snap_autumn2, s_snap_autumn3
        ])

        # Seed weekly snapshots for Oxford Brookes (Multiple weeks)
        # Week 1: 7 days ago (June 29 - July 05)
        w_date = now - timedelta(days=7)
        w_start = w_date - timedelta(days=w_date.weekday())
        w_start = w_start.replace(hour=0, minute=0, second=0, microsecond=0)
        w_end = w_start + timedelta(days=6, hours=23, minutes=59, seconds=59)

        w_snap1 = WeeklySnapshot(
            university_domain="brookes.ac.uk",
            week_start=w_start,
            week_end=w_end,
            user_id=users["j.whitfield@brookes.ac.uk"].id,
            display_name=users["j.whitfield@brookes.ac.uk"].name,
            kg_saved=18.4,
            transaction_count=3,
            rank=1
        )
        w_snap2 = WeeklySnapshot(
            university_domain="brookes.ac.uk",
            week_start=w_start,
            week_end=w_end,
            user_id=users["s.osei@brookes.ac.uk"].id,
            display_name=users["s.osei@brookes.ac.uk"].name,
            kg_saved=12.2,
            transaction_count=2,
            rank=2
        )
        w_snap3 = WeeklySnapshot(
            university_domain="brookes.ac.uk",
            week_start=w_start,
            week_end=w_end,
            user_id=users["c.fraser@brookes.ac.uk"].id,
            display_name=users["c.fraser@brookes.ac.uk"].name,
            kg_saved=8.5,
            transaction_count=1,
            rank=3
        )

        # Week 2: 14 days ago (June 22 - June 28)
        w_date2 = now - timedelta(days=14)
        w_start2 = w_date2 - timedelta(days=w_date2.weekday())
        w_start2 = w_start2.replace(hour=0, minute=0, second=0, microsecond=0)
        w_end2 = w_start2 + timedelta(days=6, hours=23, minutes=59, seconds=59)

        w_snap_w2 = WeeklySnapshot(
            university_domain="brookes.ac.uk",
            week_start=w_start2,
            week_end=w_end2,
            user_id=users["a.rahman@brookes.ac.uk"].id,
            display_name=users["a.rahman@brookes.ac.uk"].name,
            kg_saved=21.5,
            transaction_count=4,
            rank=1
        )
        w_snap_w2_2 = WeeklySnapshot(
            university_domain="brookes.ac.uk",
            week_start=w_start2,
            week_end=w_end2,
            user_id=users["j.whitfield@brookes.ac.uk"].id,
            display_name=users["j.whitfield@brookes.ac.uk"].name,
            kg_saved=15.2,
            transaction_count=2,
            rank=2
        )
        w_snap_w2_3 = WeeklySnapshot(
            university_domain="brookes.ac.uk",
            week_start=w_start2,
            week_end=w_end2,
            user_id=users["c.fraser@brookes.ac.uk"].id,
            display_name=users["c.fraser@brookes.ac.uk"].name,
            kg_saved=10.0,
            transaction_count=1,
            rank=3
        )

        # Week 3: 21 days ago (June 15 - June 21)
        w_date3 = now - timedelta(days=21)
        w_start3 = w_date3 - timedelta(days=w_date3.weekday())
        w_start3 = w_start3.replace(hour=0, minute=0, second=0, microsecond=0)
        w_end3 = w_start3 + timedelta(days=6, hours=23, minutes=59, seconds=59)

        w_snap_w3 = WeeklySnapshot(
            university_domain="brookes.ac.uk",
            week_start=w_start3,
            week_end=w_end3,
            user_id=users["s.osei@brookes.ac.uk"].id,
            display_name=users["s.osei@brookes.ac.uk"].name,
            kg_saved=17.2,
            transaction_count=3,
            rank=1
        )
        w_snap_w3_2 = WeeklySnapshot(
            university_domain="brookes.ac.uk",
            week_start=w_start3,
            week_end=w_end3,
            user_id=users["p.nair@brookes.ac.uk"].id,
            display_name=users["p.nair@brookes.ac.uk"].name,
            kg_saved=13.5,
            transaction_count=2,
            rank=2
        )
        w_snap_w3_3 = WeeklySnapshot(
            university_domain="brookes.ac.uk",
            week_start=w_start3,
            week_end=w_end3,
            user_id=users["j.whitfield@brookes.ac.uk"].id,
            display_name=users["j.whitfield@brookes.ac.uk"].name,
            kg_saved=9.2,
            transaction_count=1,
            rank=3
        )

        # Week 4: 28 days ago (June 08 - June 14)
        w_date4 = now - timedelta(days=28)
        w_start4 = w_date4 - timedelta(days=w_date4.weekday())
        w_start4 = w_start4.replace(hour=0, minute=0, second=0, microsecond=0)
        w_end4 = w_start4 + timedelta(days=6, hours=23, minutes=59, seconds=59)

        w_snap_w4 = WeeklySnapshot(
            university_domain="brookes.ac.uk",
            week_start=w_start4,
            week_end=w_end4,
            user_id=users["p.nair@brookes.ac.uk"].id,
            display_name=users["p.nair@brookes.ac.uk"].name,
            kg_saved=14.0,
            transaction_count=2,
            rank=1
        )
        w_snap_w4_2 = WeeklySnapshot(
            university_domain="brookes.ac.uk",
            week_start=w_start4,
            week_end=w_end4,
            user_id=users["j.whitfield@brookes.ac.uk"].id,
            display_name=users["j.whitfield@brookes.ac.uk"].name,
            kg_saved=11.0,
            transaction_count=1,
            rank=2
        )
        w_snap_w4_3 = WeeklySnapshot(
            university_domain="brookes.ac.uk",
            week_start=w_start4,
            week_end=w_end4,
            user_id=users["s.osei@brookes.ac.uk"].id,
            display_name=users["s.osei@brookes.ac.uk"].name,
            kg_saved=8.0,
            transaction_count=1,
            rank=3
        )

        db.session.add_all([
            w_snap1, w_snap2, w_snap3,
            w_snap_w2, w_snap_w2_2, w_snap_w2_3,
            w_snap_w3, w_snap_w3_2, w_snap_w3_3,
            w_snap_w4, w_snap_w4_2, w_snap_w4_3
        ])

        db.session.commit()
        print("\n[SUCCESS] Database committed successfully.")

        # Count stats for summary directly from DB (Anti-drift)
        total_users = User.query.count()
        student_count = User.query.filter_by(role="student").count()
        partner_count = User.query.filter_by(role="partner").count()
        admin_count = User.query.filter_by(role="admin").count()
        sold_count = Item.query.filter_by(is_sold=True).count()
        active_count = Item.query.filter_by(is_sold=False, is_deleted=False).count()
        total_items = Item.query.filter_by(is_deleted=False).count()
        total_kg = db.session.query(db.func.sum(Item.kg_saved)).filter(Item.is_sold == True).scalar() or 0.0

        print()
        print("=" * 60)
        print("  REUNI DEMO SEED - COMPLETE")
        print("=" * 60)
        print(f"  Users:                {total_users} total ({student_count} students, {admin_count} admin, {partner_count} partner)")
        print(f"  Items:                {total_items} total ({active_count} active, {sold_count} sold)")
        print(f"  Cancellation records: {len(SAMPLE_CANCELLATIONS)}")
        print(f"  Total kg saved:       {round(total_kg, 1)} kg (from sold items)")
        print()
        print("  Demo accounts (password for all: BrookesDemo1)")
        print("  -" * 30)
        for u in SAMPLE_USERS:
            print(f"    [{u['role'].upper():8s}] {u['email']}")
        print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Seed the Reuni database with demo data."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Skip the environment check and existing-data check. "
            "Use this to seed a non-debug or already-populated database intentionally. "
            "WARNING: This will DROP ALL EXISTING DATA."
        ),
    )
    args = parser.parse_args()

    with app.app_context():
        # ── Level 1: Environment check ──
        if not app.debug and not args.force:
            sys.exit(
                "\nERROR: Refusing to seed in a non-debug environment.\n"
                "If this is intentional (e.g. a staging/demo server), run:\n"
                "    python seed.py --force\n"
            )

        # ── Level 2: Existing data check ──
        try:
            existing_users = User.query.count()
        except Exception:
            existing_users = 0

        if existing_users > 0 and not args.force:
            sys.exit(
                f"\nERROR: Database already contains {existing_users} user(s).\n"
                "Seeding would wipe ALL existing data.\n"
                "If this is intentional, run:\n"
                "    python seed.py --force\n"
            )

    seed()
