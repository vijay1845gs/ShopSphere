"""
Custom management command: python manage.py seed_data
Populates the database with sample data including images.
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from products.models import Category, Tag, Product
import random
from decimal import Decimal


CATEGORIES = ["Electronics", "Clothing", "Books", "Home & Kitchen", "Sports"]
TAGS = ["new-arrival", "bestseller", "sale", "featured", "limited-edition"]

# (name, category, price, stock, image_filename, description)
SAMPLE_PRODUCTS = [
    ("Wireless Bluetooth Headphones", "Electronics", Decimal("2499.00"), 50,  "headphones.jpg",
     "Premium over-ear headphones with 30-hour battery life, active noise cancellation, and deep bass sound."),
    ("USB-C Fast Charger 65W",        "Electronics", Decimal("899.00"),  120, "charger.jpg",
     "GaN technology 65W fast charger compatible with laptops, phones, and tablets. Charges 3x faster."),
    ("Mechanical Keyboard RGB",       "Electronics", Decimal("3499.00"), 30,  "keyboard.jpg",
     "Tactile mechanical switches with per-key RGB lighting. Perfect for gaming and productivity."),
    ("Noise Cancelling Earbuds",      "Electronics", Decimal("1799.00"), 90,  "earbuds.jpg",
     "True wireless earbuds with hybrid ANC, 24-hour total battery, and IPX4 water resistance."),
    ("Smart Watch Pro",               "Electronics", Decimal("5999.00"), 40,  "smartwatch.jpg",
     "Health tracking smartwatch with SpO2, heart rate monitor, GPS, and 7-day battery life."),
    ("Men's Running Shoes",           "Sports",      Decimal("1999.00"), 80,  "running-shoes.jpg",
     "Lightweight breathable mesh upper with responsive foam cushioning for long-distance runs."),
    ("Yoga Mat Non-Slip",             "Sports",      Decimal("699.00"),  200, "yoga-mat.jpg",
     "6mm thick eco-friendly TPE yoga mat with alignment lines and carrying strap included."),
    ("Premium Sneakers",              "Sports",      Decimal("2499.00"), 60,  "sneakers.jpg",
     "Versatile everyday sneakers with memory foam insole and durable rubber outsole."),
    ("Python Crash Course Book",      "Books",       Decimal("499.00"),  60,  "python-book.jpg",
     "Best-selling beginner Python programming book. Covers fundamentals to building real projects."),
    ("Clean Code by Robert Martin",   "Books",       Decimal("599.00"),  45,  "clean-code.jpg",
     "A handbook of agile software craftsmanship. Essential reading for every serious developer."),
    ("The Alchemist Novel",           "Books",       Decimal("299.00"),  100, "novel-book.jpg",
     "Paulo Coelho's masterpiece about following your dreams. Over 65 million copies sold worldwide."),
    ("Stainless Steel Water Bottle",  "Home & Kitchen", Decimal("349.00"), 150, "water-bottle.jpg",
     "Double-wall vacuum insulated bottle keeps drinks cold 24hrs and hot 12hrs. BPA-free."),
    ("Air Fryer 4L",                  "Home & Kitchen", Decimal("4999.00"), 25, "air-fryer.jpg",
     "Digital air fryer with 8 preset cooking modes. Cooks with 85% less oil for healthier meals."),
    ("Minimalist Desk Lamp",          "Home & Kitchen", Decimal("1299.00"), 70, "desk-lamp.jpg",
     "LED desk lamp with 5 brightness levels, USB charging port, and touch-sensitive controls."),
    ("Ceramic Coffee Mug",            "Home & Kitchen", Decimal("399.00"), 200, "coffee-mug.jpg",
     "350ml premium ceramic mug with comfortable grip handle. Microwave and dishwasher safe."),
    ("Cotton Casual T-Shirt",         "Clothing",    Decimal("299.00"),  300, "tshirt.jpg",
     "100% organic cotton crew-neck t-shirt. Pre-shrunk, breathable, and available in 8 colors."),
    ("Denim Jacket",                  "Clothing",    Decimal("1499.00"), 70,  "denim-jacket.jpg",
     "Classic washed denim jacket with button closure and two chest pockets. Unisex fit."),
    ("Polarised Sunglasses",          "Clothing",    Decimal("899.00"),  90,  "sunglasses.jpg",
     "UV400 polarised lenses with lightweight TR90 frame. Reduces glare for driving and outdoors."),
    ("Travel Backpack 30L",           "Sports",      Decimal("1799.00"), 55,  "backpack.jpg",
     "Water-resistant 30L backpack with laptop compartment, USB charging port, and ergonomic straps."),
    ("Laptop Sleeve Bag",             "Electronics", Decimal("599.00"),  110, "laptop-bag.jpg",
     "Neoprene protective sleeve for 13–15 inch laptops with accessory pocket and handle."),
]


class Command(BaseCommand):
    help = "Seeds the database with sample products, categories, tags, and images."

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Clear existing products before seeding.")

    def handle(self, *args, **options):
        if options["clear"]:
            Product.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing products."))

        # Categories
        categories = {}
        for name in CATEGORIES:
            cat, _ = Category.objects.get_or_create(name=name, defaults={"slug": slugify(name)})
            categories[name] = cat

        # Tags
        tags = []
        for name in TAGS:
            tag, _ = Tag.objects.get_or_create(name=name, defaults={"slug": slugify(name)})
            tags.append(tag)

        created = updated = 0

        for name, cat_name, price, stock, image_file, description in SAMPLE_PRODUCTS:
            slug = slugify(name)
            product, is_new = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "category": categories[cat_name],
                    "price": price,
                    "stock": stock,
                    "description": description,
                    "is_active": True,
                }
            )

            # Always update image and description even on existing products
            product.image = f"products/{image_file}"
            product.description = description
            product.category = categories[cat_name]
            product.save()

            if not product.tags.exists():
                product.tags.set(random.sample(tags, k=random.randint(1, 2)))

            if is_new:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done — {created} products created, {updated} products updated with images."
        ))
