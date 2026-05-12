from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from urllib.parse import urlencode, urlparse

from products.models import Product
from . import services as cart_services


@require_POST
def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        # Save pending action
        request.session['pending_cart_action'] = {'action': 'add', 'product_id': product_id}
        login_url = f"{reverse('login')}?{urlencode({'next': reverse('cart_detail')})}"
        return redirect(login_url)

    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart_services.add_item(request.session, product_id)
    messages.success(request, f'"{product.name}" added to cart.')
    return redirect(request.META.get("HTTP_REFERER", "product_list"))


@require_POST
def buy_now(request, product_id):
    if not request.user.is_authenticated:
        # Save pending action
        request.session['pending_cart_action'] = {'action': 'buy', 'product_id': product_id}
        login_url = f"{reverse('login')}?{urlencode({'next': reverse('checkout')})}"
        return redirect(login_url)

    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart_services.add_item(request.session, product_id)
    return redirect('checkout')


@login_required(login_url="login")
def cart_detail(request):
    """Display cart contents. Read-only view."""
    cart_items, total = cart_services.build_cart_items(request.session)
    return render(request, "cart.html", {"cart_items": cart_items, "total": total})


@login_required(login_url="login")
@require_POST
def update_cart(request, product_id):
    """POST-only. Updates quantity for a specific product."""
    try:
        quantity = int(request.POST.get("quantity", 1))
    except (ValueError, TypeError):
        quantity = 1
    cart_services.update_item(request.session, product_id, quantity)
    messages.success(request, "Cart updated.")
    return redirect("cart_detail")


@login_required(login_url="login")
@require_POST
def remove_from_cart(request, product_id):
    """POST-only. Removes a product from the cart entirely."""
    cart_services.remove_item(request.session, product_id)
    messages.success(request, "Item removed from cart.")
    return redirect("cart_detail")
