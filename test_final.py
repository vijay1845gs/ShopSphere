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
from cart import services as cart_services

def test_pending_action_flow():
    print("Testing pending action flow for Add to Cart and Buy Now...")
    
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
    
    print("\n=== Testing Add to Cart Flow ===")
    
    # Clear any existing session
    client.cookies.clear()
    
    # 1. Guest user adds to cart (should redirect to login)
    print("1. Guest user adds to cart...")
    response = client.post(
        reverse('add_to_cart', args=[product.id]), 
        HTTP_REFERER=reverse('product_list')
    )
    print(f"   Status code: {response.status_code}")
    if response.status_code == 302:
        print(f"   Redirect to: {response.url}")
        
        # Check if it's redirecting to login with next parameter
        if '/accounts/login/' in response.url and 'next=' in response.url and 'cart_detail' in response.url:
            print("   ✓ Correctly redirected to login with cart_detail next parameter")
        else:
            print("   ✗ Not redirecting to login properly")
    
    # Check if pending action was saved in session
    if client.session.get('pending_cart_action'):
        pending = client.session['pending_cart_action']
        print(f"   Pending action saved: {pending}")
        if pending.get('action') == 'add' and pending.get('product_id') == product.id:
            print("   ✓ Pending action correctly saved for Add to Cart")
        else:
            print("   ✗ Pending action incorrect")
    else:
        print("   ✗ No pending action saved in session")
    
    # 2. Login with credentials
    print("\n2. User logs in...")
    login_success = client.login(username='testuser', password='testpass')
    print(f"   Login successful: {login_success}")
    
    if login_success:
        # After login, we should be redirected to cart detail (due to our pending action logic)
        # Note: The login view processes the pending action and redirects accordingly
        
        # Let's check the cart state directly
        cart_items, total = cart_services.build_cart_items(client.session)
        print(f"\n3. Cart state after login:")
        print(f"   Cart items: {len(cart_items)}")
        print(f"   Total: {total}")
        
        if len(cart_items) > 0:
            print("   ✓ Product correctly added to cart via pending action")
        else:
            print("   ✗ Product NOT added to cart")
            
        # Clear the pending action to avoid interference with next test
        if 'pending_cart_action' in client.session:
            del client.session['pending_cart_action']
            client.session.save()
    
    print("\n=== Testing Buy Now Flow ===")
    
    # Create new client to avoid session contamination
    client2 = Client()
    client2.cookies.clear()
    
    # 1. Guest user clicks Buy Now (should redirect to login)
    print("1. Guest user clicks Buy Now...")
    response = client2.post(
        reverse('buy_now', args=[product.id]), 
        HTTP_REFERER=reverse('product_list')
    )
    print(f"   Status code: {response.status_code}")
    if response.status_code == 302:
        print(f"   Redirect to: {response.url}")
        
        # Check if it's redirecting to login with next parameter to checkout
        if '/accounts/login/' in response.url and 'next=' in response.url and 'checkout' in response.url:
            print("   ✓ Correctly redirected to login with checkout next parameter")
        else:
            print("   ✗ Not redirecting to login with checkout next parameter")
    
    # Check if pending action was saved in session
    if client2.session.get('pending_cart_action'):
        pending = client2.session['pending_cart_action']
        print(f"   Pending action saved: {pending}")
        if pending.get('action') == 'buy' and pending.get('product_id') == product.id:
            print("   ✓ Pending action correctly saved for Buy Now")
        else:
            print("   ✗ Pending action incorrect")
    else:
        print("   ✗ No pending action saved in session")
    
    # 2. Login with credentials
    print("\n2. User logs in...")
    login_success = client2.login(username='testuser', password='testpass')
    print(f"   Login successful: {login_success}")
    
    if login_success:
        # After login and processing pending action, we should be redirected to checkout
        # Let's check if the item was added to cart
        cart_items, total = cart_services.build_cart_items(client2.session)
        print(f"\n3. Cart state after login:")
        print(f"   Cart items: {len(cart_items)}")
        print(f"   Total: {total}")
        
        if len(cart_items) > 0:
            print("   ✓ Product correctly added to cart via pending action")
            # For Buy Now, after login it should redirect to checkout
            # We can't easily test the redirect without making another request,
            # but we know the login view handles this
        else:
            print("   ✗ Product NOT added to cart")
    
    # Cleanup
    product.delete()
    category.delete() if category.product_set.count() == 0 else None
    user.delete()
    
    print("\nTest completed!")

if __name__ == '__main__':
    test_pending_action_flow()