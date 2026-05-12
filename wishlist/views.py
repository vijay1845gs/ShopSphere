from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_POST

from products.models import Product
from .models import Wishlist


@login_required(login_url="login")
@require_POST
def toggle_wishlist(request, product_id):
    """POST-only. Adds or removes a product from the user's wishlist."""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)

    if wishlist.products.filter(id=product_id).exists():
        wishlist.products.remove(product)
        messages.info(request, f'"{product.name}" removed from wishlist.')
    else:
        wishlist.products.add(product)
        messages.success(request, f'"{product.name}" added to wishlist.')

    return redirect(request.META.get("HTTP_REFERER", "wishlist_detail"))


class WishlistView(LoginRequiredMixin, TemplateView):
    template_name = "wishlist/wishlist.html"
    login_url = "login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wishlist, _ = Wishlist.objects.get_or_create(user=self.request.user)
        context["wishlist_products"] = wishlist.products.select_related("category")
        return context
