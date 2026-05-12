from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test


def handler404(request, exception):
    return render(request, "404.html", status=404)


def handler500(request):
    return render(request, "500.html", status=500)


@login_required(login_url="login")
@user_passes_test(lambda u: u.is_staff, login_url="product_list")
def admin_dashboard(request):
    """Simple admin dashboard with key metrics."""
    from products.models import Product
    from orders.models import Order
    from django.contrib.auth.models import User
    
    stats = {
        "total_products": Product.objects.count(),
        "pending_orders": Order.objects.filter(status="pending").count(),
        "total_users": User.objects.count(),
        "delivered_orders": Order.objects.filter(status="delivered").count(),
    }
    return render(request, "dashboard.html", {"stats": stats})