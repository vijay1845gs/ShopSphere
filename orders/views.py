from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_POST

from .models import Order
from .services import place_order, cancel_order, CheckoutError
from .tasks import (
    send_order_confirmation_email,
    send_order_cancellation_email,
)
from cart import services as cart_services
from config.logging_utils import (
    log_order_created,
    log_order_cancelled,
    log_order_failure,
)


@login_required(login_url="login")
def checkout(request):
    """
    GET  — show order summary from current cart
    POST — place the order atomically via order service
    """
    cart_items, total = cart_services.build_cart_items(request.session)

    if not cart_items:
        messages.warning(request, "Your cart is empty.")
        return redirect("cart_detail")

    if request.method == "POST":
        # Pre-flight stock check — gives user-friendly errors before
        # entering the atomic transaction block
        stock_errors = cart_services.validate_cart_stock(cart_items)
        if stock_errors:
            for error in stock_errors:
                messages.error(request, error)
            return redirect("cart_detail")

        try:
            order = place_order(user=request.user, cart_items=cart_items)
            cart_services.clear_cart(request.session)
            messages.success(request, f"Order #{order.id} placed successfully!")

            log_order_created(
                order_id=order.id,
                user_id=order.user_id,
                total=float(order.total_price),
                item_count=order.items.count(),
            )

            # Trigger async order confirmation email
            send_order_confirmation_email.delay(order.id)

            return redirect("order_detail", pk=order.id)

        except CheckoutError as e:
            log_order_failure(
                order_id=0,  # order not created
                user_id=request.user.id,
                error=str(e),
            )
            messages.error(request, str(e))
            return redirect("cart_detail")

    return render(request, "orders/checkout.html", {
        "cart_items": cart_items,
        "total": total,
    })


@login_required(login_url="login")
@require_POST
def cancel_order_view(request, pk):
    """POST-only. Cancel an order and restore stock."""
    try:
        order = Order.objects.get(pk=pk, user=request.user)
        cancel_order(order)
        messages.success(request, f"Order #{order.id} has been cancelled.")

        log_order_cancelled(
            order_id=order.id,
            user_id=order.user_id,
        )

        # Notify user via async email
        send_order_cancellation_email.delay(order.id)
    except Order.DoesNotExist:
        messages.error(request, "Order not found.")
    except CheckoutError as e:
        log_order_failure(
            order_id=pk,
            user_id=request.user.id,
            error=str(e),
        )
        messages.error(request, str(e))
    return redirect("order_detail", pk=pk)


class OrderHistoryView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "orders/order_history.html"
    context_object_name = "orders"
    login_url = "login"

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related("items__product")
        )


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "orders/order_detail.html"
    context_object_name = "order"
    login_url = "login"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related("items__product")
