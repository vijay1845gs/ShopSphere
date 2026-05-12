from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal

from products.models import Product, Category
from wishlist.models import Wishlist


def make_product():
    cat, _ = Category.objects.get_or_create(name="Test", defaults={"slug": "test"})
    return Product.objects.create(
        name="Test Product", slug="test-product", category=cat,
        price=Decimal("100.00"), stock=10, description="desc", is_active=True,
    )


class WishlistModelTest(TestCase):
    def test_wishlist_str_contains_username(self):
        user = User.objects.create_user(username="testuser")
        wishlist = Wishlist.objects.create(user=user)
        self.assertIn("testuser", str(wishlist))


class WishlistViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass123")
        self.product = make_product()
        self.wishlist = Wishlist.objects.create(user=self.user)

    def test_wishlist_view_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("wishlist_detail"))
        self.assertEqual(response.status_code, 302)  # redirect to login

    def test_wishlist_view_shows_products(self):
        self.client.login(username="testuser", password="pass123")
        self.wishlist.products.add(self.product)
        response = self.client.get(reverse("wishlist_detail"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)


class ToggleWishlistTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass123")
        self.product = make_product()
        self.client.login(username="testuser", password="pass123")

    def test_toggle_wishlist_adds_product(self):
        response = self.client.post(reverse("toggle_wishlist", kwargs={"product_id": self.product.id}))
        self.assertRedirects(response, reverse("wishlist_detail"))
        self.assertTrue(self.user.wishlist.products.filter(id=self.product.id).exists())

    def test_toggle_wishlist_removes_product(self):
        # Add first
        self.user.wishlist.products.add(self.product)
        self.assertTrue(self.user.wishlist.products.filter(id=self.product.id).exists())
        # Toggle again to remove
        response = self.client.post(reverse("toggle_wishlist", kwargs={"product_id": self.product.id}))
        self.assertRedirects(response, reverse("wishlist_detail"))
        self.assertFalse(self.user.wishlist.products.filter(id=self.product.id).exists())

    def test_toggle_wishlist_requires_login(self):
        self.client.logout()
        response = self.client.post(reverse("toggle_wishlist", kwargs={"product_id": self.product.id}))
        self.assertEqual(response.status_code, 302)  # redirect to login

    def test_toggle_wishlist_requires_post(self):
        response = self.client.get(reverse("toggle_wishlist", kwargs={"product_id": self.product.id}))
        self.assertEqual(response.status_code, 405)
