"""
Order-related asynchronous tasks
=================================
Background tasks for order processing, notifications, and maintenance.
"""

import logging
from datetime import date

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.db.models import Sum, Count, Q

from celery import shared_task
from celery.utils.log import get_task_logger
from orders.models import Order
from products.models import Product

task_logger = get_task_logger(__name__)


# ============================================================================
# EMAIL NOTIFICATIONS
# ============================================================================

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_confirmation_email(self, order_id: int):
    """
    Send order confirmation email asynchronously.
    Retries up to 3 times with exponential backoff on failure.
    """
    try:
        order = Order.objects.select_related("user").prefetch_related("items__product").get(id=order_id)
    except Order.DoesNotExist:
        return {"status": "skipped", "reason": "order_deleted"}

    try:
        order_url = f"{settings.SITE_URL}{reverse('order_detail', args=[order.id])}"
        context = {
            "order": order,
            "order_url": order_url,
            "items": order.items.all(),
            "total": order.total_price,
        }

        subject = f"Your ShopSphere Order Confirmation #{order.id}"
        html_message = render_to_string("emails/order_confirmation.html", context)
        plain_message = render_to_string("emails/order_confirmation.txt", context)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            html_message=html_message,
            fail_silently=False,
        )

        task_logger.info(f"[TASK SUCCESS] Order confirmation email sent for order {order_id}")
        return {"status": "sent", "order_id": order_id, "user_id": order.user_id}
    except Exception as exc:
        task_logger.error(f"[TASK FAILURE] Failed to send order confirmation for {order_id}: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_cancellation_email(self, order_id: int, reason: str = ""):
    """Send order cancellation notification email."""
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return {"status": "skipped", "reason": "order_deleted"}

    context = {"order": order, "reason": reason}
    subject = f"Order #{order.id} Cancellation Confirmation"
    
    try:
        html_message = render_to_string("emails/order_cancelled.html", context)
        plain_message = render_to_string("emails/order_cancelled.txt", context)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        task_logger.info(f"[TASK SUCCESS] Order cancellation email sent for order {order_id}")
        return {"status": "sent", "order_id": order_id}
    except Exception as exc:
        task_logger.error(f"[TASK FAILURE] Failed to send cancellation email for {order_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


# ============================================================================
# LOW STOCK ALERT
# ============================================================================

@shared_task
def send_low_stock_alert(threshold: int = 10):
    """
    Check for products below stock threshold and send admin alerts.
    Scheduled hourly via Celery Beat.
    """
    low_stock_products = list(Product.objects.filter(
        stock__lte=threshold,
        is_active=True
    ).values("name", "stock", "slug"))
    
    if not low_stock_products:
        task_logger.info("[TASK SUCCESS] Low stock alert check: no low stock products")
        return {"status": "no_alerts", "count": 0}

    product_list = "\n".join(
        f"- {p['name']} (stock: {p['stock']})" for p in low_stock_products
    )
    
    subject = f"Low Stock Alert - {len(low_stock_products)} products need attention"
    
    try:
        send_mail(
            subject=subject,
            message=f"The following products are running low on stock:\n\n{product_list}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[getattr(settings, "ADMIN_EMAIL", settings.DEFAULT_FROM_EMAIL)],
            fail_silently=True,
        )
        
        task_logger.info(f"[TASK SUCCESS] Low stock alert sent for {len(low_stock_products)} products")
        return {"status": "alerted", "count": len(low_stock_products)}
    except Exception as exc:
        task_logger.error(f"[TASK FAILURE] Failed to send low stock alert: {exc}")
        return {"status": "failed", "error": str(exc)}


# ============================================================================
# MAINTENANCE
# ============================================================================

@shared_task
def cleanup_expired_sessions():
    """
    Clean up expired sessions from the database.
    Daily scheduled task.
    """
    from django.contrib.sessions.models import Session
    
    expired_count, _ = Session.objects.filter(expire_date__lt=date.today()).delete()
    
    task_logger.info(f"[TASK SUCCESS] Cleaned up {expired_count} expired sessions")
    return {"status": "cleaned", "sessions_removed": expired_count}


# ============================================================================
# ANALYTICS
# ============================================================================

@shared_task
def generate_daily_analytics():
    """
    Generate daily analytics summary.
    Runs daily at midnight via Celery Beat.
    """
    today = date.today()
    
    stats = Order.objects.filter(
        created_at__date=today
    ).aggregate(
        total_orders=Count("id"),
        total_revenue=Sum("total_price"),
        pending_orders=Count("id", filter=Q(status="pending")),
        shipped_orders=Count("id", filter=Q(status="shipped")),
        delivered_orders=Count("id", filter=Q(status="delivered")),
    )
    
    low_stock_count = Product.objects.filter(
        stock__lte=5,
        is_active=True
    ).count()
    
    task_logger.info(
        f"[TASK SUCCESS] Daily analytics — "
        f"Orders: {stats['total_orders']}, "
        f"Revenue: ${stats['total_revenue'] or 0:.2f}, "
        f"Low stock: {low_stock_count}"
    )
    
    return {
        "date": str(today),
        "orders": stats["total_orders"],
        "revenue": float(stats["total_revenue"] or 0),
        "status_breakdown": {
            "pending": stats["pending_orders"],
            "shipped": stats["shipped_orders"],
            "delivered": stats["delivered_orders"],
        },
        "low_stock_products": low_stock_count,
    }
