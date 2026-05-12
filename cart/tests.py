"""
Tests for cart service layer.
Run with: python manage.py test cart
"""

from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.utils.text import slugify

from products.models import Product, Category
from cart import services as cart_services


def make_product(name="Widget", price=Decimal("100.00"), stock=10):
    cat, _ = Category.objects.get_or_create(name="Test", defaults={"slug": "test"})
    return Product.objects.create(
        name=name, slug=slugify(name), category=cat,
        price=price, stock=stock, description="desc", is_active=True,
    )


class CartServiceTest(TestCase):

    def setUp(self):
        self.product = make_product()
        self.session = {}

    def test_add_item_new(self):
        cart_services.add_item(self.session, self.product.id)
        self.assertEqual(self.session["cart"][str(self.product.id)], 1)

    def test_add_item_increments(self):
        cart_services.add_item(self.session, self.product.id)
        cart_services.add_item(self.session, self.product.id)
        self.assertEqual(self.session["cart"][str(self.product.id)], 2)

    def test_remove_item(self):
        cart_services.add_item(self.session, self.product.id)
        cart_services.remove_item(self.session, self.product.id)
        self.assertNotIn(str(self.product.id), self.session["cart"])

    def test_update_item_sets_quantity(self):
        cart_services.add_item(self.session, self.product.id)
        cart_services.update_item(self.session, self.product.id, 5)
        self.assertEqual(self.session["cart"][str(self.product.id)], 5)

    def test_update_item_zero_removes(self):
        cart_services.add_item(self.session, self.product.id)
        cart_services.update_item(self.session, self.product.id, 0)
        self.assertNotIn(str(self.product.id), self.session["cart"])

    def test_clear_cart(self):
        cart_services.add_item(self.session, self.product.id)
        cart_services.clear_cart(self.session)
        self.assertEqual(self.session["cart"], {})

    def test_build_cart_items_single_query(self):
        """build_cart_items should fetch all products in one query."""
        p2 = make_product(name="Gadget", price=Decimal("200.00"))
        cart_services.add_item(self.session, self.product.id)
        cart_services.add_item(self.session, p2.id)
        with self.assertNumQueries(1):
            items, total = cart_services.build_cart_items(self.session)
        self.assertEqual(len(items), 2)
        self.assertEqual(total, Decimal("300.00"))

    def test_build_cart_items_skips_inactive(self):
        inactive = make_product(name="Gone", stock=5)
        inactive.is_active = False
        inactive.save()
        cart_services.add_item(self.session, inactive.id)
        items, total = cart_services.build_cart_items(self.session)
        self.assertEqual(len(items), 0)

    def test_validate_cart_stock_passes(self):
        cart_services.add_item(self.session, self.product.id, 5)
        items, _ = cart_services.build_cart_items(self.session)
        errors = cart_services.validate_cart_stock(items)
        self.assertEqual(errors, [])

    def test_validate_cart_stock_fails(self):
        cart_services.add_item(self.session, self.product.id, 999)
        items, _ = cart_services.build_cart_items(self.session)
        errors = cart_services.validate_cart_stock(items)
        self.assertEqual(len(errors), 1)
        self.assertIn("Widget", errors[0])

    def test_get_cart_count(self):
        cart_services.add_item(self.session, self.product.id)
        cart_services.add_item(self.session, self.product.id + 1)
        self.assertEqual(cart_services.get_cart_count(self.session), 2)
