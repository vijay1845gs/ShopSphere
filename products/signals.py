"""
Product cache invalidation signals
Connect these signals to automatically clear cache when products/categories change.
"""

from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.core.cache import cache

from .models import Product, Category
from .cache import invalidate_product, invalidate_category, invalidate_homepage


@receiver(post_save, sender=Product)
def product_saved(sender, instance, **kwargs):
    """Clear product-related caches on save (create or update)."""
    invalidate_product(product_id=instance.id, product_slug=instance.slug)


@receiver(post_delete, sender=Product)
def product_deleted(sender, instance, **kwargs):
    """Clear product-related caches on delete."""
    invalidate_product(product_id=instance.id, product_slug=instance.slug)


@receiver(post_save, sender=Category)
def category_saved(sender, instance, **kwargs):
    """Clear category caches on save."""
    invalidate_category(category_slug=instance.slug)


@receiver(post_delete, sender=Category)
def category_deleted(sender, instance, **kwargs):
    """Clear category caches on delete."""
    invalidate_category(category_slug=instance.slug)


# Invalidate on ManyToMany changes (product tags affect filtering)
@receiver(m2m_changed, sender=Product.tags.through)
def product_tags_changed(sender, instance, **kwargs):
    """Product tag changes affect product list filters."""
    invalidate_product(product_id=instance.id, product_slug=instance.slug)
    invalidate_category(category_slug=instance.category.slug if instance.category else None)
