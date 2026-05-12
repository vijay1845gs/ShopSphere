"""
Tests for the reviews app.
Run with: python manage.py test reviews
"""

from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.text import slugify

from products.models import Product, Category
from .models import Review


def make_product():
    cat, _ = Category.objects.get_or_create(name="Test", defaults={"slug": "test"})
    return Product.objects.create(
        name="Review Product", slug="review-product", category=cat,
        price=Decimal("100.00"), stock=5, description="desc", is_active=True,
    )


class ReviewModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="reviewer", password="pass1234")
        self.product = make_product()

    def test_unique_review_per_user_per_product(self):
        Review.objects.create(product=self.product, user=self.user, rating=4)
        with self.assertRaises(Exception):
            Review.objects.create(product=self.product, user=self.user, rating=5)

    def test_str(self):
        review = Review.objects.create(product=self.product, user=self.user, rating=3)
        self.assertIn("reviewer", str(review))


class ReviewSubmitViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="reviewer", password="pass1234")
        self.product = make_product()
        self.client.login(username="reviewer", password="pass1234")

    def test_submit_review(self):
        response = self.client.post(
            reverse("submit_review", kwargs={"product_id": self.product.id}),
            {"rating": 5, "comment": "Excellent!"},
        )
        self.assertEqual(Review.objects.count(), 1)

    def test_update_existing_review(self):
        Review.objects.create(product=self.product, user=self.user, rating=3)
        self.client.post(
            reverse("submit_review", kwargs={"product_id": self.product.id}),
            {"rating": 5, "comment": "Updated"},
        )
        self.assertEqual(Review.objects.get(product=self.product, user=self.user).rating, 5)

    def test_invalid_rating_rejected(self):
        self.client.post(
            reverse("submit_review", kwargs={"product_id": self.product.id}),
            {"rating": 9},
        )
        self.assertEqual(Review.objects.count(), 0)
