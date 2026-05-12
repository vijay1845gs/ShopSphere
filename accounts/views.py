from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404

from config.logging_utils import (
    log_login_success,
    log_login_failure,
)

from products.models import Product
from cart import services as cart_services


def register_view(request):
    """
    Uses Django's built-in UserCreationForm which includes:
    - username uniqueness validation
    - password strength validation
    - password confirmation matching
    """
    if request.user.is_authenticated:
        return redirect("product_list")

    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Account created! Please log in.")
        return redirect("login")

    return render(request, "register.html", {"form": form})


def login_view(request):
    """Uses Django's AuthenticationForm for validated credential handling."""
    if request.user.is_authenticated:
        return redirect("product_list")

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            ip = request.META.get("REMOTE_ADDR", "")
            log_login_success(
                user_id=user.id,
                username=user.username,
                ip=ip
            )
            # Handle pending cart actions (Add to Cart or Buy Now) for guest users
            pending_action = request.session.pop('pending_cart_action', None)
            if pending_action:
                product_id = pending_action.get('product_id')
                action_type = pending_action.get('action')
                if product_id and action_type in ['add', 'buy']:
                    try:
                        product = Product.objects.get(id=product_id, is_active=True)
                        from cart import services as cart_services
                        cart_services.add_item(request.session, product_id)
                        if action_type == 'buy':
                            return redirect('checkout')
                        else:  # add
                            messages.success(request, f'"{product.name}" added to cart.')
                            return redirect('cart_detail')
                    except Product.DoesNotExist:
                        pass  # Product no longer available, continue with normal redirect
            
            # Role-based redirect: admin -> dashboard, customer -> product_list
            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)
            if user.is_staff:
                return redirect("admin_dashboard")
            return redirect("product_list")
        messages.error(request, "Invalid username or password.")
        log_login_failure(
            username=request.POST.get("username", ""),
            ip=request.META.get("REMOTE_ADDR", ""),
        )

    return render(request, "login.html", {"form": form})


@require_POST
def logout_view(request):
    """POST-only logout — prevents CSRF-based forced logout attacks."""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("product_list")