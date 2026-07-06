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
from app.models import User, Item, CancellationRecord, CATEGORY_WEIGHTS, CATEGORIES, CONDITION_CHOICES
from app.utils.email_validation import extract_university_domain

app = create_app()

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
                    is_uuid = False
                    if key.endswith(".webp"):
                        base = key[:-5]
                        if len(base) == 32:
                            try:
                                int(base, 16)
                                is_uuid = True
                            except ValueError:
                                pass
                    
                    if is_seed or is_uuid:
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
        "email": "w.churchill@oxford.ac.uk",
        "name": "Winston Churchill",
        "password": "OxfordDemo1",
        "role": "student",
        "partner_university": None,
    },
    {
        "email": "m.thatcher@oxford.ac.uk",
        "name": "Margaret Thatcher",
        "password": "OxfordDemo1",
        "role": "student",
        "partner_university": None,
    },
    {
        "email": "a.turing@oxford.ac.uk",
        "name": "Alan Turing",
        "password": "OxfordDemo1",
        "role": "student",
        "partner_university": None,
    },
    {
        "email": "admin@oxford.ac.uk",
        "name": "Oxford Admin",
        "password": "OxfordDemo1",
        "role": "admin",
        "partner_university": None,
    },
    {
        "email": "sustainability@oxford.ac.uk",
        "name": "Oxford Sustainability Office",
        "password": "OxfordDemo1",
        "role": "partner",
        "partner_university": "oxford.ac.uk",
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
        "seller_email": "w.churchill@oxford.ac.uk",
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
        "seller_email": "a.turing@oxford.ac.uk",
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
        "seller_email": "a.turing@oxford.ac.uk",
        "image_file": "keychron_keyboard.jpg",
        "is_sold": True,
        "buyer_email": "m.thatcher@oxford.ac.uk",
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
        "seller_email": "m.thatcher@oxford.ac.uk",
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
        "seller_email": "w.churchill@oxford.ac.uk",
        "image_file": "tea_set.jpg",
        "is_sold": False,
        "buyer_email": None,
        "days_ago_claimed": None,
        "days_active_before_claim": None,
        "days_ago_listed": 5,
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

        # Flush to assign user IDs
        db.session.flush()
        print(f"Flushed {len(users)} users.")

        # Create items
        items_by_title = {}  # dict mapping item title -> Item object

        for i_data in SAMPLE_ITEMS:
            seller = users[i_data["seller_email"]]
            kg = CATEGORY_WEIGHTS.get(i_data["category"], 1.0)

            # Copy real image from seed folder to static/uploads/
            image_filename = copy_seed_image(
                i_data["image_file"],
                i_data["category"],
                i_data["title"],
            )

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
                created_at=item_created_at,
            )
            db.session.add(item)
            items_by_title[i_data["title"]] = item
            status = "SOLD" if i_data["is_sold"] else "active"
            print(f"  Created item [{status}]: {i_data['title']}")

        # Flush to assign item IDs
        db.session.flush()
        print(f"Flushed {len(items_by_title)} items.")

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

        # Update kg_saved_total on each user
        seller_kg_totals = {}
        for i_data in SAMPLE_ITEMS:
            if i_data["is_sold"]:
                email = i_data["seller_email"]
                kg = CATEGORY_WEIGHTS.get(i_data["category"], 1.0)
                seller_kg_totals[email] = seller_kg_totals.get(email, 0.0) + kg

        for email, total_kg in seller_kg_totals.items():
            users[email].kg_saved_total = round(total_kg, 2)
            print(f"  Updated kg_saved_total for {email}: {round(total_kg, 2)} kg")

        db.session.commit()
        print("\n[SUCCESS] Database committed successfully.")

        # Count stats for summary
        total_users = len(SAMPLE_USERS)
        student_count = sum(1 for u in SAMPLE_USERS if u["role"] == "student")
        sold_count = sum(1 for i in SAMPLE_ITEMS if i["is_sold"])
        active_count = sum(1 for i in SAMPLE_ITEMS if not i["is_sold"])
        total_kg = sum(
            CATEGORY_WEIGHTS.get(i["category"], 1.0)
            for i in SAMPLE_ITEMS if i["is_sold"]
        )

        print()
        print("=" * 60)
        print("  REUNI DEMO SEED - COMPLETE")
        print("=" * 60)
        print(f"  Users:                {total_users} total ({student_count} students, 1 admin, 1 partner)")
        print(f"  Items:                {len(SAMPLE_ITEMS)} total ({active_count} active, {sold_count} sold)")
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
