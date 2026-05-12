#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('/Users/VIJAY SALVATORE/Desktop/Projects/ShopSphere')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from products.models import Product, Category
from django.urls import reverse

def test_pending_action_flow():
    print("Testing pending action flow...")
    
    # Create test data
    category, _ = Category.objects.get_or_create(name="Test", defaults={"slug": "test"})
    product = Product.objects.create(
        name="Test Product",
        slug="test-product",
        category=category,
        price=100.00,
        stock=10,
        description="Test description",
        is_active=True,
    )
    
    # Create test user
    user = User.objects.create_user(username='testuser', password='testpass')
    user.is_staff = False
    user.save()
    
    # Test client
    client = Client()
    
    # Clear any existing session
    client.cookies.clear()
    
    print("\n1. Testing Add to Cart for guest user:")
    # Guest user adds to cart (should redirect to login)
    response = client.post(
        reverse('add_to_cart', args=[product.id]), 
        HTTP_REFERER=reverse('product_list')
    )
    print(f"   Status code: {response.status_code}")
    if response.status_code == 302:
        print(f"   Redirect to: {response.url}")
        
        # Check if it's redirecting to login with next parameter
        if '/accounts/login/' in response.url and 'next=' in response.url:
            print("   ✓ Correctly redirected to login with next parameter")
        else:
            print("   ✗ Not redirecting to login properly")
    
    print("\n2. Testing login process:")
    # Login with credentials
    login_success = client.login(username='testuser', password='testpass')
    print(f"   Login successful: {login_success}")
    
    if login_success:
        # Now test the add to cart again (should work and redirect to cart)
        response = client.post(
            reverse('add_to_cart', args=[product.id]), 
            HTTP_REFERER=reverse('product_list')
        )
        print(f"   Add to cart after login status: {response.status_code}")
        if response.status_code == 302:
            print(f"   Redirect after login: {response.url}")
            if 'cart' in response.url:
                print("   ✓ Correctly redirected to cart after login")
            else:
                print("   ✗ Not redirected to cart after login")
    
    print("\n3. Testing Buy Now for guest user:")
    # Create new client to avoid session contamination
    client2 = Client()
    client2.cookies.clear()
    
    response = client2.post(
        reverse('buy_now', args=[product.id]), 
        HTTP_REFERER=reverse('product_list')
    )
    print(f"   Buy Now status code: {response.status_code}")
    if response.status_code == 302:
        print(f"   Redirect to: {response.url}")
        
        # Check if it's redirecting to login with next parameter to checkout
        if '/accounts/login/' in response.url and 'next=' in response.url and 'checkout' in response.url:
            print("   ✓ Correctly redirected to login with checkout next parameter")
        else:
            print("   ✗ Not redirecting to login with checkout next parameter")
    
    print("\n4. Testing login after Buy Now:")
    login_success = client2.login(username='testuser', password='testpass')
    print(f"   Login successful: {login_success}")
    
    if login_success:
        # Test buy now again (should go to checkout)
        response = client2.post(
            reverse('buy_now', args=[product.id]), 
            HTTP_REFERER=reverse('product_list')
        )
        print(f"   Buy Now after login status: {response.status_code}")
        if response.status_code == 302:
            print(f"   Redirect after login: {response.url}")
            if 'checkout' in response.url:
                print("   ✓ Correctly redirected to checkout after login")
            else:
                print("   ✗ Not redirected to checkout after login")
    
    # Cleanup
    product.delete()
    category.delete() if category.product_set.count() == 0 else None
    user.delete()
    
    print("\nTest completed!")

if __name__ == '__main__':
    test_pending_action_flow()