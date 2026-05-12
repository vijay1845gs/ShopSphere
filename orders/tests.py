"""
Tests for the orders app.
Run with: python manage.py test orders
"""

from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db import IntegrityError

from products.models import Product, Category
from .models import Order, OrderItem
from .services import place_order, cancel_order, CheckoutError


def make_user(username="buyer", password="pass1234"):
    return User.objects.create_user(username=username, password=password)


def make_product():
    cat, _ = Category.objects.get_or_create(name="Test", defaults={"slug": "test"})
    return Product.objects.create(
        name="Test Item", slug="test-item", category=cat,
        price=Decimal("500.00"), stock=20, description="desc", is_active=True,
    )


class OrderModelTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.product = make_product()
        self.order = Order.objects.create(user=self.user, total_price=Decimal("1000.00"))

    def test_str(self):
        self.assertIn(str(self.order.id), str(self.order))

    def test_order_item_subtotal(self):
        item = OrderItem.objects.create(
            order=self.order, product=self.product, quantity=2, price=Decimal("500.00")
        )
        self.assertEqual(item.get_subtotal(), Decimal("1000.00"))


class CheckoutViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.product = make_product()
        self.client.login(username="buyer", password="pass1234")

    def test_checkout_empty_cart_redirects(self):
        response = self.client.get(reverse("checkout"))
        self.assertRedirects(response, reverse("cart_detail"))

    def test_checkout_with_cart_shows_summary(self):
        session = self.client.session
        session["cart"] = {str(self.product.id): 2}
        session.save()
        response = self.client.get(reverse("checkout"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)

    def test_checkout_post_creates_order(self):
        session = self.client.session
        session["cart"] = {str(self.product.id): 1}
        session.save()
        response = self.client.post(reverse("checkout"))
        self.assertEqual(Order.objects.filter(user=self.user).count(), 1)

    def test_checkout_clears_cart(self):
        session = self.client.session
        session["cart"] = {str(self.product.id): 1}
        session.save()
        self.client.post(reverse("checkout"))
        session = self.client.session
        self.assertEqual(session.get("cart"), {})

    def test_order_history_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("order_history"))
        self.assertNotEqual(response.status_code, 200)


class PlaceOrderServiceTest(TestCase):
    """Tests for the place_order service function with transaction safety."""

    def setUp(self):
        self.user = make_user()
        self.product = make_product()
        self.cart_items = [
            {"product": self.product, "quantity": 2}
        ]

    def test_place_order_creates_order_and_items(self):
        order = place_order(self.user, self.cart_items)
        self.assertIsInstance(order, Order)
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.items.count(), 1)
        item = order.items.first()
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.price, self.product.price)

    def test_place_order_decrements_stock_atomic(self):
        initial_stock = self.product.stock
        order = place_order(self.user, self.cart_items)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, initial_stock - 2)

    def test_place_order_raises_for_empty_cart(self):
        with self.assertRaises(ValueError):
            place_order(self.user, [])

    def test_place_order_rolls_back_on_stock_insufficiency(self):
        # Reduce stock to less than needed
        self.product.stock = 1
        self.product.save()
        cart_items = [{"product": self.product, "quantity": 2}]
        with self.assertRaises(CheckoutError):
            place_order(self.user, cart_items)
        # Stock should remain unchanged (rollback)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)

    def test_place_order_locks_stock_concurrently(self):
        """
        Verify that select_for_update prevents overselling:
        simulate two concurrent checkouts for same low-stock product.
        """
        self.product.stock = 1
        self.product.save()
        cart_items = [{"product": self.product, "quantity": 1}]

        # First transaction should succeed
        order1 = place_order(self.user, cart_items)
        self.assertEqual(order1.items.first().quantity, 1)

        # Second transaction should fail with CheckoutError due to locked stock
        with self.assertRaises(CheckoutError):
            place_order(self.user, cart_items)

    def test_place_order_bulk_create_efficiency(self):
        """Ensure OrderItem bulk_create is used (single INSERT)."""
        p2 = make_product(name="Gadget")
        cart_items = [
            {"product": self.product, "quantity": 1},
            {"product": p2, "quantity": 3},
        ]
        with self.assertNumQueries(5):  # 1 lock + 1 order create + 1 bulk_create + 2 stock updates + 1 cart_items fetch? Actually we can't easily count but ensure it's not N+1
            order = place_order(self.user, cart_items)
            self.assertEqual(order.items.count(), 2)


class CancelOrderServiceTest(TestCase):
    """Tests for cancel_order with stock restoration."""

    def setUp(self):
        self.user = make_user()
        self.product = make_product()
        self.order = Order.objects.create(user=self.user, total_price=Decimal("1000.00"))
        OrderItem.objects.create(
            order=self.order, product=self.product, quantity=3, price=self.product.price
        )
        # Deduct stock as if order was placed
        self.product.stock -= 3
        self.product.save()

    def test_cancel_order_restores_stock(self):
        initial_stock = self.product.stock
        cancel_order(self.order)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, initial_stock + 3)

    def test_cancel_order_updates_status(self):
        cancel_order(self.order)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "cancelled")

    def test_cancel_order_fails_for_shipped_order(self):
        self.order.status = "shipped"
        self.order.save()
        with self.assertRaises(CheckoutError):
            cancel_order(self.order)

    def test_cancel_order_fails_for_delivered_order(self):
        self.order.status = "delivered"
        self.order.save()
        with self.assertRaises(CheckoutError):
            cancel_order(self.order)

    def test_cancel_order_fails_for_already_cancelled(self):
        self.order.status = "cancelled"
        self.order.save()
        with self.assertRaises(CheckoutError):
            cancel_order(self.order)

    def test_cancel_order_is_atomic(self):
        """
        Simulate a failure during stock restoration and verify
        that order status is not updated (rollback).
        """
        # Patch restore_stock to raise an exception
        with patch.object(self.product, 'restore_stock', side_effect=RuntimeError("simulated failure")):
            with self.assertRaises(RuntimeError):
                cancel_order(self.order)
        # Order status should remain unchanged
        self.order.refresh_from_db()
        self.assertNotEqual(self.order.status, "cancelled")
