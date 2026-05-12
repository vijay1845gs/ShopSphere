"""
Order Service Layer
===================
Handles the entire checkout pipeline in a single atomic transaction.

Architecture decisions:
- transaction.atomic() wraps the entire checkout — if anything fails,
  the DB rolls back completely. No partial orders, no ghost records.
- select_for_update() locks product rows at the DB level during the
  transaction. This prevents two concurrent checkouts from both reading
  stock=1 and both succeeding (overselling / race condition).
- Stock is decremented inside the same transaction as order creation.
  They are atomically linked — you cannot have one without the other.
- Raises CheckoutError (a domain exception) for business rule violations.
  Views catch this and show user-friendly messages without exposing
  internal implementation details.
"""

from decimal import Decimal
from django.db import transaction
from django.contrib.auth.models import User

from products.models import Product
from orders.models import Order, OrderItem


class CheckoutError(Exception):
    """
    Domain exception for checkout business rule violations.
    Raised inside the atomic block so the transaction rolls back.
    Views catch this and display the message to the user.
    """
    pass


@transaction.atomic
def place_order(user: User, cart_items: list[dict]) -> Order:
    """
    Create an Order atomically with stock locking and decrement.

    Flow:
    1. Lock all product rows with SELECT FOR UPDATE (prevents race conditions)
    2. Re-validate stock against the locked rows (not the pre-lock snapshot)
    3. Create Order record
    4. Create OrderItem records via bulk_create (single INSERT vs N INSERTs)
    5. Decrement stock for each product
    6. Return the created Order

    Args:
        user: The authenticated user placing the order
        cart_items: Output of cart.services.build_cart_items()

    Returns:
        Order instance

    Raises:
        CheckoutError: If any product is out of stock at lock time
        ValueError: If cart_items is empty
    """
    if not cart_items:
        raise ValueError("Cannot place an order with an empty cart.")

    product_ids = [item["product"].id for item in cart_items]

    # --- Step 1: Lock rows ---
    # select_for_update() issues SELECT ... FOR UPDATE in PostgreSQL.
    # Any other transaction trying to read these rows will WAIT until
    # this transaction commits or rolls back. This is the correct way
    # to prevent overselling in a concurrent environment.
    locked_products = {
        p.id: p
        for p in Product.objects.select_for_update().filter(id__in=product_ids)
    }

    # --- Step 2: Re-validate stock against locked data ---
    # We re-validate here (not just in the view) because between the
    # view's pre-check and this transaction, another request could have
    # decremented stock. The locked rows give us the true current state.
    stock_errors = []
    for item in cart_items:
        product = locked_products.get(item["product"].id)
        if not product or product.stock < item["quantity"]:
            available = product.stock if product else 0
            stock_errors.append(
                f'"{item["product"].name}" — requested {item["quantity"]}, '
                f'only {available} available.'
            )

    if stock_errors:
        # Raising inside atomic() triggers automatic rollback.
        raise CheckoutError(
            "Some items are no longer available:\n" + "\n".join(stock_errors)
        )

    # --- Step 3: Calculate total from locked prices ---
    total = sum(
        locked_products[item["product"].id].price * item["quantity"]
        for item in cart_items
    )

    # --- Step 4: Create Order ---
    order = Order.objects.create(user=user, total_price=total)

    # --- Step 5: bulk_create OrderItems ---
    # One INSERT statement instead of N. Significantly faster for large carts.
    order_items = [
        OrderItem(
            order=order,
            product=locked_products[item["product"].id],
            quantity=item["quantity"],
            price=locked_products[item["product"].id].price,  # price snapshot
        )
        for item in cart_items
    ]
    OrderItem.objects.bulk_create(order_items)

    # --- Step 6: Decrement stock using model method ---
    # Done after order creation so if bulk_create fails, stock is not touched.
    for item in cart_items:
        product = locked_products[item["product"].id]
        product.decrement_stock(item["quantity"])

    return order


@transaction.atomic
def cancel_order(order: Order) -> None:
    """
    Cancel an order and restore stock.

    Only pending/processing orders can be cancelled.
    Stock is restored atomically with the status change.

    Args:
        order: The Order instance to cancel

    Raises:
        CheckoutError: If the order is already shipped/delivered/cancelled
    """
    if order.status in ("shipped", "delivered", "cancelled"):
        raise CheckoutError(
            f"Order #{order.id} cannot be cancelled — current status: {order.get_status_display()}."
        )

    # Lock the order items first, then lock their products separately
    # Cannot use select_related with select_for_update due to PostgreSQL restriction:
    # "FOR UPDATE cannot be applied to the nullable side of an outer join"
    items = list(order.items.select_for_update().all())
    product_ids = [item.product_id for item in items if item.product_id]
    products = {
        p.id: p
        for p in Product.objects.select_for_update().filter(id__in=product_ids)
    }

    for item in items:
        product = products.get(item.product_id)
        if product:
            product.restore_stock(item.quantity)

    order.status = "cancelled"
    order.save(update_fields=["status", "updated_at"])
