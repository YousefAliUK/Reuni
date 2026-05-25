"""
UniCycle — Seed Script
Populates the database with test users and sample items (with placeholder images).

Usage:
    python seed.py

Requires Pillow (already in requirements.txt).
"""

import os
import sys
import uuid

from PIL import Image as PILImage, ImageDraw, ImageFont

# ── Bootstrap the Flask app so we can use the DB ──
from app import create_app, db
from app.models import User, Item, CATEGORY_WEIGHTS, CATEGORIES, CONDITION_CHOICES

app = create_app()

# ── Placeholder image generation ──
UPLOAD_DIR = os.path.join(app.static_folder, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Colours that look nice on the item cards (background, text)
CATEGORY_COLOURS = {
    "Electronics":  ("#6366f1", "#ffffff"),   # indigo
    "Furniture":    ("#f59e0b", "#1e293b"),   # amber
    "Kitchenware":  ("#ef4444", "#ffffff"),   # red
    "Clothing":     ("#ec4899", "#ffffff"),   # pink
    "Books":        ("#0ea5e9", "#ffffff"),   # sky
    "Stationery":   ("#8b5cf6", "#ffffff"),   # violet
    "Sports":       ("#10b981", "#ffffff"),   # emerald
    "Other":        ("#64748b", "#ffffff"),   # slate
}


def make_placeholder(category, title):
    """Generate a simple coloured placeholder image for a given category."""
    bg, fg = CATEGORY_COLOURS.get(category, ("#64748b", "#ffffff"))
    img = PILImage.new("RGB", (800, 600), bg)
    draw = ImageDraw.Draw(img)

    # Try to use a built-in font, fall back to default
    try:
        font_large = ImageFont.truetype("arial.ttf", 48)
        font_small = ImageFont.truetype("arial.ttf", 28)
    except (IOError, OSError):
        font_large = ImageFont.load_default()
        font_small = font_large

    # Draw category emoji + name
    draw.text((400, 240), category, fill=fg, font=font_large, anchor="mm")
    # Draw item title below
    short_title = title if len(title) <= 30 else title[:27] + "…"
    draw.text((400, 320), short_title, fill=fg, font=font_small, anchor="mm")

    filename = f"{uuid.uuid4().hex}.jpg"
    img.save(os.path.join(UPLOAD_DIR, filename), "JPEG", quality=85)
    return filename


# ── Sample Data ──
SAMPLE_USERS = [
    {"email": "alice@university.ac.uk", "name": "Alice Chen",  "password": "password123", "phone_number": "+447700100001"},
    {"email": "bob@university.ac.uk",   "name": "Bob Taylor",  "password": "password123", "phone_number": "+447700100002"},
    {"email": "cara@university.ac.uk",  "name": "Cara Mensah", "password": "password123", "phone_number": "+447700100003"},
]

SAMPLE_ITEMS = [
    {
        "title": "MacBook Air M1 (2020)",
        "description": "Great condition, barely used. Comes with charger. Perfect for lectures and coding.",
        "category": "Electronics",
        "condition": "Like New",
        "price": 450.00,
        "is_free": False,
        "seller_email": "alice@university.ac.uk",
        "seed_image": "macbook.jpg",
    },
    {
        "title": "Organic Chemistry — Bruice, 8th Ed.",
        "description": "Highlighted in places but perfectly usable. Essential for second-year chem students.",
        "category": "Books",
        "condition": "Good",
        "price": 15.00,
        "is_free": False,
        "seller_email": "alice@university.ac.uk",
        "seed_image": "chemistry_book.jpg",
    },
    {
        "title": "IKEA KALLAX Shelf Unit",
        "description": "White, 4-cube. Dismantled and ready for collection. Small scratch on one side.",
        "category": "Furniture",
        "condition": "Fair",
        "price": 0,
        "is_free": True,
        "seller_email": "bob@university.ac.uk",
        "seed_image": "kallax.jpg",
    },
    {
        "title": "Full Kitchen Starter Set",
        "description": "Pots, pans, utensils, and plates. Everything a fresher needs. Moving out, need gone ASAP.",
        "category": "Kitchenware",
        "condition": "Good",
        "price": 25.00,
        "is_free": False,
        "seller_email": "bob@university.ac.uk",
        "seed_image": "kitchen_set.jpg",
    },
    {
        "title": "Nike Running Shoes (UK 9)",
        "description": "Worn for one term. Still have plenty of life left. UK size 9.",
        "category": "Sports",
        "condition": "Good",
        "price": 20.00,
        "is_free": False,
        "seller_email": "cara@university.ac.uk",
        "seed_image": "nike_shoes.jpg",
    },
    {
        "title": "Graphic Calculator (Casio fx-9860GII)",
        "description": "Required for maths and engineering modules. Works perfectly, includes cover.",
        "category": "Electronics",
        "condition": "Like New",
        "price": 35.00,
        "is_free": False,
        "seller_email": "cara@university.ac.uk",
        "seed_image": "calculator.jpg",
    },
    {
        "title": "Winter Jacket — North Face (M)",
        "description": "Warm, waterproof, barely worn. Selling because I received another as a gift.",
        "category": "Clothing",
        "condition": "Like New",
        "price": 40.00,
        "is_free": False,
        "seller_email": "alice@university.ac.uk",
        "seed_image": "winter_jacket.jpg",
    },
    {
        "title": "Stationery Bundle (Pens, Notebooks, Folders)",
        "description": "Box of unused pens, A4 notebooks, and ring binders. Free to a good home!",
        "category": "Stationery",
        "condition": "New",
        "price": 0,
        "is_free": True,
        "seller_email": "bob@university.ac.uk",
        "seed_image": "stationery.jpg",
    },
]


def seed():
    """Drop existing data and re-seed the database."""
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        db.create_all()

        # Create users
        users = {}
        for u_data in SAMPLE_USERS:
            user = User(email=u_data["email"], name=u_data["name"], phone_number=u_data["phone_number"])
            user.set_password(u_data["password"])
            db.session.add(user)
            users[u_data["email"]] = user

        db.session.flush()  # assign IDs

        # Create items with placeholder images or copy actual seed images
        for i_data in SAMPLE_ITEMS:
            seller = users[i_data["seller_email"]]
            kg = CATEGORY_WEIGHTS.get(i_data["category"], 1.0)
            
            seed_image = i_data.get("seed_image")
            seed_images_dir = os.path.join(app.static_folder, "seed_images")
            
            if seed_image and os.path.exists(os.path.join(seed_images_dir, seed_image)):
                import shutil
                image_ext = os.path.splitext(seed_image)[1]
                image_filename = f"{uuid.uuid4().hex}{image_ext}"
                shutil.copy2(
                    os.path.join(seed_images_dir, seed_image),
                    os.path.join(UPLOAD_DIR, image_filename)
                )
            else:
                image_filename = make_placeholder(i_data["category"], i_data["title"])

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
            )
            db.session.add(item)

        db.session.commit()

        print(f"Seeded {len(SAMPLE_USERS)} users and {len(SAMPLE_ITEMS)} items.")
        print(f"Images saved to: {UPLOAD_DIR}")
        print()
        print("Test accounts (all passwords: password123):")
        for u in SAMPLE_USERS:
            print(f"   * {u['email']}  ({u['name']})")


if __name__ == "__main__":
    seed()
