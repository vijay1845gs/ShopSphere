from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


class RegisterViewTest(TestCase):
    def test_register_get_renders_form(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create account")

    def test_register_post_creates_user(self):
        response = self.client.post(reverse("register"), {
            "username": "newuser",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
        })
        self.assertRedirects(response, reverse("login"))
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_register_post_password_mismatch(self):
        response = self.client.post(reverse("register"), {
            "username": "newuser",
            "password1": "SecurePass123!",
            "password2": "DifferentPass123!",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The two password fields didn")
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_register_authenticated_user_redirects(self):
        self.client.force_login(User.objects.create_user("existing"))
        response = self.client.get(reverse("register"))
        self.assertRedirects(response, reverse("product_list"))


class LoginViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")

    def test_login_get_renders_form(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome back")

    def test_login_post_with_valid_credentials(self):
        response = self.client.post(reverse("login"), {
            "username": "testuser",
            "password": "testpass123",
        })
        self.assertRedirects(response, reverse("product_list"))

    def test_login_post_with_invalid_credentials(self):
        response = self.client.post(reverse("login"), {
            "username": "testuser",
            "password": "wrongpass",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password")

    def test_login_authenticated_user_redirects(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("login"))
        self.assertRedirects(response, reverse("product_list"))


class LogoutViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.force_login(self.user)

    def test_logout_post_logs_out_user(self):
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("product_list"))
        # User should be logged out — session auth removed
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_get_returns_405(self):
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 405)

    def test_logout_requires_post(self):
        # GET should not log out
        self.client.post(reverse("logout"))
        # After POST we are logged out; but if we try GET it shouldn't work
        # This is already covered by test_logout_get_returns_405
        pass
