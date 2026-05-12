"""
Cart Service Layer
==================
All cart business logic lives here. Views only call these functions.

Design decisions:
- Stateless functions that take session data as input — easy to test without requests
- Returns structured dicts instead of raw session data — views don't parse sessions
- Validation is centralised — stock checks happen in one place
"""

from decimal import Decimal
from django.shortcuts import get_object_or_404
from products.models import Product


def get_cart(session: dict) -> dict:
    """Return the raw cart dict from session, defaulting to empty."""
    return session.get("cart", {})


def save_cart(session: dict, cart: dict) -> None:
    """Persist cart back to session and mark it as modified."""
    session["cart"] = cart
    # Only set modified if the session has this attribute (like Django's session)
    if hasattr(session, 'modified'):
        session.modified = True


def add_item(session: dict, product_id: int, quantity: int = 1) -> None:
    """
    Add quantity to a product in the cart.
    Does not validate stock — call validate_cart_stock() before checkout.
    """
    cart = get_cart(session)
    key = str(product_id)
    cart[key] = cart.get(key, 0) + quantity
    save_cart(session, cart)


def remove_item(session: dict, product_id: int) -> None:
    """Remove a product entirely from the cart."""
    cart = get_cart(session)
    cart.pop(str(product_id), None)
    save_cart(session, cart)


def update_item(session: dict, product_id: int, quantity: int) -> None:
    """Set exact quantity for a product. Removes item if quantity <= 0."""
    cart = get_cart(session)
    if quantity > 0:
        cart[str(product_id)] = quantity
    else:
        cart.pop(str(product_id), None)
    save_cart(session, cart)


def clear_cart(session: dict) -> None:
    """Empty the cart — called after successful checkout."""
    save_cart(session, {})


def build_cart_items(session: dict) -> tuple[list[dict], Decimal]:
    """
    Resolve cart session data into full product objects with subtotals.

    Returns:
        (cart_items, total) where cart_items is a list of dicts:
        [{"product": Product, "quantity": int, "subtotal": Decimal}]

    ORM note: fetches all products in a single query using
    Product.objects.filter(id__in=...) instead of one query per item.
    This eliminates the N+1 query problem in the original view.
    """
    cart = get_cart(session)
    if not cart:
        return [], Decimal("0.00")

    product_ids = [int(k) for k in cart.keys()]
    products = {
        str(p.id): p
        for p in Product.objects.filter(id__in=product_ids, is_active=True).select_related("category")
    }

    cart_items = []
    total = Decimal("0.00")

    for product_id, quantity in cart.items():
        product = products.get(product_id)
        if not product:
            continue  # product was deleted or deactivated — skip silently
        subtotal = product.price * quantity
        total += subtotal
        cart_items.append({
            "product": product,
            "quantity": quantity,
            "subtotal": subtotal,
            "item_total": subtotal,  # alias kept for template compatibility
        })

    return cart_items, total


def validate_cart_stock(cart_items: list[dict]) -> list[str]:
    """
    Validate that every item in the cart has sufficient stock.

    Returns a list of error strings. Empty list means all items are valid.
    Called before checkout to give user-friendly errors before entering
    the atomic transaction block.
    """
    errors = []
    for item in cart_items:
        product = item["product"]
        quantity = item["quantity"]
        if product.stock < quantity:
            if product.stock == 0:
                errors.append(f'"{product.name}" is out of stock.')
            else:
                errors.append(
                    f'"{product.name}" only has {product.stock} unit(s) available '
                    f'but you requested {quantity}.'
                )
    return errors


def get_cart_count(session: dict) -> int:
    """Return total number of distinct items in cart — used in navbar badge."""
    return len(get_cart(session))
