"""
Product caching utilities
=========================

Centralized cache key generation and invalidation for products.
Uses Django's cache framework with Redis backend.

Cache Strategy:
- Product list pages: cache with pagination params (15 min TTL)
- Product detail: cache by slug (30 min TTL)
- Categories: cache queryset (1 hour TTL)
- Homepage/Featured: cache popular/trending (15 min TTL)
"""

import logging
from typing import Any, Callable
from django.core.cache import cache
from decouple import config

logger = logging.getLogger("django")

# TTL values in seconds
LIST_TTL = config("PRODUCT_LIST_TTL", default=900, cast=int)
CATEGORY_TTL = config("CATEGORY_CACHE_TTL", default=3600, cast=int)
PRODUCT_DETAIL_TTL = config("PRODUCT_CACHE_TTL", default=1800, cast=int)
HOMEPAGE_TTL = config("HOME_CACHE_TTL", default=900, cast=int)

KEY_PREFIX = "shopsphere"


def _key(*parts: str) -> str:
    """Build namespaced cache key. Example: products:list:active"""
    return ":".join([KEY_PREFIX, *parts])


def product_list_key(page: int = 1, filters: dict = None, sort: str = "") -> str:
    """Cache key for product list with pagination and filters."""
    filter_str = ""
    if filters:
        filter_str = ":".join(f"{k}={v}" for k, v in sorted(filters.items()))
    return _key("products", "list", sort or "default", f"page{page}", filter_str)


def product_detail_key(slug: str) -> str:
    """Cache key for individual product detail data."""
    return _key("product", "detail", slug)


def categories_key() -> str:
    """Cache key for all categories."""
    return _key("categories", "all")


def category_products_key(slug: str, page: int = 1) -> str:
    """Cache key for products filtered by category."""
    return _key("categories", slug, "products", f"page{page}")


def homepage_key() -> str:
    """Cache key for homepage featured/popular products."""
    return _key("homepage", "featured")


# Cache invalidation utilities
def _delete_pattern(pattern: str) -> int:
    """Delete by pattern when the backend supports it."""
    delete_pattern = getattr(cache, "delete_pattern", None)
    if callable(delete_pattern):
        return delete_pattern(pattern)
    cache.clear()
    return 0


def invalidate_product(product_id: int = None, product_slug: str = None):
    """
    Invalidate all caches related to a product.
    Call this on product update/delete.
    """
    _delete_pattern(f"{KEY_PREFIX}:product:*")
    _delete_pattern(f"{KEY_PREFIX}:products:*")
    if product_slug:
        cache.delete(product_detail_key(product_slug))
    logger.info(f"[CACHE INVALIDATED] product:{product_slug or product_id}")


def invalidate_category(category_slug: str = None):
    """
    Invalidate category-related caches.
    Call this on category change or product category update.
    """
    _delete_pattern(f"{KEY_PREFIX}:categories:*")
    if category_slug:
        cache.delete(category_products_key(category_slug))
        _delete_pattern(f"{KEY_PREFIX}:products:*")
    logger.info(f"[CACHE INVALIDATED] category:{category_slug}")


def invalidate_homepage():
    """Invalidate homepage fragment caches."""
    _delete_pattern(f"{KEY_PREFIX}:homepage:*")
    logger.info("[CACHE INVALIDATED] homepage")


def invalidate_all():
    """Nuclear option — clear entire cache."""
    cache.clear()
    logger.info("[CACHE INVALIDATED] all")


# Cache helper functions
def cached_queryset(timeout: int, key_func: Callable, queryset_func: Callable) -> Any:
    """Execute a queryset function with caching."""
    def wrapper(*args, **kwargs):
        cache_key = key_func(*args, **kwargs)
        data = cache.get(cache_key)
        if data is None:
            data = queryset_func(*args, **kwargs)
            cache.set(cache_key, data, timeout)
            logger.info(f"[CACHE MISS] {cache_key}")
        else:
            logger.info(f"[CACHE HIT] {cache_key}")
        return data
    return wrapper


def warmup_product_cache(slugs: list):
    """Pre-warm product cache with commonly accessed products."""
    from products.models import Product
    for slug in slugs:
        key = product_detail_key(slug)
        if not cache.get(key):
            try:
                product = Product.objects.filter(slug=slug).first()
                if product:
                    cache.set(key, product, PRODUCT_DETAIL_TTL)
            except Exception:
                pass