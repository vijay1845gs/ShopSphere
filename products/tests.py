"""
Tests for the products app.
Run with: python manage.py test products
"""

from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.text import slugify

from .models import Category, Product, Tag


def make_product(name="Test Product", price=Decimal("999.00"), stock=10, is_active=True):
    """Helper factory to create a product without repeating boilerplate."""
    cat, _ = Category.objects.get_or_create(name="Test Category", defaults={"slug": "test-category"})
    return Product.objects.create(
        name=name,
        slug=slugify(name),
        category=cat,
        price=price,
        stock=stock,
        description="A test product.",
        is_active=is_active,
    )


class CategoryModelTest(TestCase):
    def test_str(self):
        cat = Category.objects.create(name="Electronics", slug="electronics")
        self.assertEqual(str(cat), "Electronics")


class ProductModelTest(TestCase):
    def setUp(self):
        self.product = make_product()

    def test_str(self):
        self.assertEqual(str(self.product), "Test Product")

    def test_is_in_stock(self):
        self.assertTrue(self.product.is_in_stock())

    def test_out_of_stock(self):
        self.product.stock = 0
        self.assertFalse(self.product.is_in_stock())

    def test_get_absolute_url(self):
        url = self.product.get_absolute_url()
        self.assertIn(self.product.slug, url)

    def test_get_meta_title_fallback(self):
        self.assertEqual(self.product.get_meta_title(), self.product.name)

    def test_price_is_decimal(self):
        self.assertIsInstance(self.product.price, Decimal)


class ProductListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = make_product()

    def test_list_returns_200(self):
        response = self.client.get(reverse("product_list"))
        self.assertEqual(response.status_code, 200)

    def test_inactive_product_not_shown(self):
        make_product(name="Hidden Product", is_active=False)
        response = self.client.get(reverse("product_list"))
        self.assertNotContains(response, "Hidden Product")

    def test_search_filter(self):
        response = self.client.get(reverse("product_list") + "?q=Test")
        self.assertContains(response, "Test Product")

    def test_search_no_results(self):
        response = self.client.get(reverse("product_list") + "?q=xyznotexist")
        self.assertContains(response, "No products found")


class ProductDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = make_product()

    def test_detail_returns_200(self):
        response = self.client.get(reverse("product_detail", kwargs={"slug": self.product.slug}))
        self.assertEqual(response.status_code, 200)

    def test_detail_contains_product_name(self):
        response = self.client.get(reverse("product_detail", kwargs={"slug": self.product.slug}))
        self.assertContains(response, self.product.name)

    def test_inactive_product_returns_404(self):
        p = make_product(name="Inactive", is_active=False)
        response = self.client.get(reverse("product_detail", kwargs={"slug": p.slug}))
        self.assertEqual(response.status_code, 404)


class ProductAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = make_product()
        self.user = User.objects.create_user(username="testuser", password="testpass123")

    def test_api_product_list(self):
        response = self.client.get("/api/v1/products/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.json())

    def test_api_product_detail(self):
        response = self.client.get(f"/api/v1/products/{self.product.slug}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], self.product.name)

    def test_api_jwt_obtain(self):
        response = self.client.post(
            "/api/v1/auth/token/",
            {"username": "testuser", "password": "testpass123"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())

    def test_api_register(self):
        response = self.client.post(
            "/api/v1/auth/register/",
            {"username": "newuser", "email": "new@test.com", "password": "securepass123"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
