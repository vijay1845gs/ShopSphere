#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('/Users/VIJAY SALVATORE/Desktop/Projects/ShopSphere')
django.setup()

from django.contrib.sessions.backends.db import SessionStore
from django.contrib.auth.models import User
from products.models import Product, Category
from cart import services as cart_services

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
    
    # Test session
    session = SessionStore()
    session.save()
    
    # Simulate guest adding to cart
    print("1. Simulating guest Add to Cart...")
    request = type('Request', (), {})()
    request.session = session
    request.user.is_authenticated = False
    
    # Call add_to_cart view (should redirect to login)
    from cart.views import add_to_cart
    try:
        response = add_to_cart(request, product.id)
        print(f"   Response type: {type(response)}")
        if hasattr(response, 'url'):
            print(f"   Redirect URL: {response.url}")
        
        # Check if pending action was saved
        pending_action = request.session.get('pending_cart_action')
        print(f"   Pending action saved: {pending_action}")
        
        if pending_action:
            print("   ✓ Pending action correctly saved")
        else:
            print("   ✗ Pending action NOT saved")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Simulate login and processing pending action
    print("\n2. Simulating login processing...")
    # Create and login user
    user = User.objects.create_user(username='testuser', password='testpass')
    user.is_staff = False
    user.save()
    
    # Simulate login view processing pending action
    from accounts.views import login_view
    from django.contrib.auth.forms import AuthenticationForm
    
    login_request = type('Request', (), {})()
    login_request.method = 'POST'
    login_request.POST = {'username': 'testuser', 'password': 'testpass'}
    login_request.session = session
    login_request.META = {'REMOTE_ADDR': '127.0.0.1'}
    login_request.user = type('User', (), {'is_authenticated': False})()
    
    # Mock the form
    class MockForm:
        def __init__(self, *args, **kwargs):
            pass
        def is_valid(self):
            return True
        def get_user(self):
            return user
    
    # Temporarily replace AuthenticationForm
    original_form = AuthenticationForm
    try:
        # We can't easily mock the import, so let's test the logic directly
        print("   Testing pending action processing logic...")
        
        # Simulate what happens in login_view after successful auth
        pending_action = login_request.session.pop('pending_cart_action', None)
        print(f"   Pending action retrieved: {pending_action}")
        
        if pending_action:
            product_id = pending_action.get('product_id')
            action_type = pending_action.get('action')
            print(f"   Product ID: {product_id}, Action: {action_type}")
            
            if product_id and action_type in ['add', 'buy']:
                try:
                    product_obj = Product.objects.get(id=product_id, is_active=True)
                    cart_services.add_item(login_request.session, product_id)
                    print(f"   ✓ Item added to cart via pending action")
                    if action_type == 'buy':
                        print("   → Would redirect to checkout")
                    else:
                        print("   → Would redirect to cart")
                except Product.DoesNotExist:
                    print("   Product no longer available")
            else:
                print("   Invalid pending action")
        else:
            print("   No pending action to process")
            
    finally:
        # Restore original form
        pass
    
    # Check final cart state
    cart_items, total = cart_services.build_cart_items(login_request.session)
    print(f"\n3. Final cart state:")
    print(f"   Cart items: {len(cart_items)}")
    print(f"   Total: {total}")
    
    # Cleanup
    product.delete()
    category.delete() if category.product_set.count() == 0 else None
    user.delete()
    session.delete()
    
    print("\nTest completed!")

if __name__ == '__main__':
    test_pending_action_flow()