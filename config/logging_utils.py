"""
Logging utilities for ShopSphere.
Provides logger instances and structured logging methods.
"""

import logging
from typing import Any


# Pre-configured loggers for different domains
auth_logger = logging.getLogger("shopsphere.auth")
order_logger = logging.getLogger("shopsphere.orders")
security_logger = logging.getLogger("shopsphere.security")
celery_logger = logging.getLogger("celery.task")


# Authentication logging
def log_login_success(user_id: int, username: str, ip: str = "") -> None:
    """Log successful login attempt."""
    auth_logger.info(
        f"Login success | user_id={user_id} | username={username} | ip={ip}"
    )


def log_login_failure(username: str, ip: str = "", reason: str = "invalid_credentials") -> None:
    """Log failed login attempt."""
    auth_logger.warning(
        f"Login failure | username={username} | ip={ip} | reason={reason}"
    )


def log_suspicious_login(user_id: int, ip: str, details: str) -> None:
    """Log suspicious login activity."""
    security_logger.warning(
        f"Suspicious login | user_id={user_id} | ip={ip} | details={details}"
    )


# Order logging
def log_order_created(order_id: int, user_id: int, total: float, item_count: int) -> None:
    """Log order creation."""
    order_logger.info(
        f"Order created | order_id={order_id} | user_id={user_id} | total={total} | items={item_count}"
    )


def log_order_cancelled(order_id: int, user_id: int, reason: str = "") -> None:
    """Log order cancellation."""
    order_logger.info(
        f"Order cancelled | order_id={order_id} | user_id={user_id} | reason={reason}"
    )


def log_order_failure(order_id: int, user_id: int, error: str) -> None:
    """Log order processing failure."""
    order_logger.error(
        f"Order failure | order_id={order_id} | user_id={user_id} | error={error}"
    )


# Error logging
def log_api_exception(endpoint: str, method: str, error: str, user_id: int = None) -> None:
    """Log API exception."""
    extra = f"user_id={user_id} | " if user_id else ""
    logging.getLogger("django").error(
        f"API exception | {extra}endpoint={endpoint} | method={method} | error={error}"
    )


def log_db_failure(operation: str, model: str, error: str) -> None:
    """Log database failure."""
    logging.getLogger("django").error(
        f"DB failure | operation={operation} | model={model} | error={error}"
    )


def log_server_exception(error: str, path: str = "") -> None:
    """Log server exception."""
    logging.getLogger("django").critical(
        f"Server exception | path={path} | error={error}"
    )


# Security logging
def log_unauthorized_access(user_id: int, path: str, method: str) -> None:
    """Log unauthorized access attempt."""
    security_logger.warning(
        f"Unauthorized access | user_id={user_id} | path={path} | method={method}"
    )


def log_jwt_failure(user_id: int = None, error: str = "") -> None:
    """Log JWT authentication failure."""
    extra = f"user_id={user_id} | " if user_id else ""
    security_logger.warning(f"JWT failure | {extra}error={error}")


def log_admin_activity(user_id: int, action: str, model: str, object_id: int = None) -> None:
    """Log admin panel activity."""
    extra = f"object_id={object_id} | " if object_id else ""
    security_logger.info(
        f"Admin activity | user_id={user_id} | action={action} | model={model} | {extra}"
    )