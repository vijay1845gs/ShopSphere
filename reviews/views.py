from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from products.models import Product
from .models import Review


@login_required(login_url="login")
def submit_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method != "POST":
        return redirect("product_detail", slug=product.slug)

    rating = request.POST.get("rating")
    comment = request.POST.get("comment", "").strip()

    if not rating or not rating.isdigit() or not (1 <= int(rating) <= 5):
        messages.error(request, "Please provide a valid rating between 1 and 5.")
        return redirect("product_detail", slug=product.slug)

    _, created = Review.objects.update_or_create(
        product=product,
        user=request.user,
        defaults={"rating": int(rating), "comment": comment},
    )

    if created:
        messages.success(request, "Review submitted!")
    else:
        messages.info(request, "Your review has been updated.")

    return redirect("product_detail", slug=product.slug)
