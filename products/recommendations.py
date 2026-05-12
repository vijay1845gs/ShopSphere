"""
Product Recommendation Service
============================
Simple, database-native recommendation logic for product detail pages.

Algorithm Priority:
1. Same category (excluding current product)
2. Shared tags (excluding already selected)
3. Similar price (±20%)
4. High-rated products (fallback)
"""

from django.db.models import Avg
from .models import Product


def get_recommendations(product, limit=6):
    """
    Get recommended products for a given product.
    
    Args:
        product: The Product instance to get recommendations for
        limit: Maximum number of recommendations (default 6)
    
    Returns:
        List of Product instances with annotations
    """
    if limit <= 0:
        return []
    
    recommended_ids = set()
    recommendations = []
    
    # Priority 1: Same category (highest relevance)
    if product.category:
        same_category = list(
            Product.objects.active()
            .select_related("category")
            .prefetch_related("tags")
            .exclude(id=product.id)
            .filter(category=product.category)
            .annotate(avg_rating=Avg("reviews__rating"))
            [:limit]
        )
        for p in same_category:
            if p.id not in recommended_ids:
                recommended_ids.add(p.id)
                recommendations.append(p)
    
    # Priority 2: Shared tags
    if len(recommendations) < limit and product.tags.exists():
        tag_ids = product.tags.values_list("id", flat=True)
        same_tags = list(
            Product.objects.active()
            .select_related("category")
            .prefetch_related("tags")
            .exclude(id=product.id)
            .filter(tags__in=tag_ids)
            .exclude(id__in=recommended_ids)
            .annotate(avg_rating=Avg("reviews__rating"))
            .distinct()
            [:limit * 2]  # Get more to filter
        )
        for p in same_tags:
            if p.id not in recommended_ids and len(recommendations) < limit:
                recommended_ids.add(p.id)
                recommendations.append(p)
    
    # Priority 3: Similar price range (±20%)
    if len(recommendations) < limit:
        price_min = product.price * 0.8
        price_max = product.price * 1.2
        similar_price = list(
            Product.objects.active()
            .select_related("category")
            .prefetch_related("tags")
            .exclude(id=product.id)
            .exclude(id__in=recommended_ids)
            .filter(price__gte=price_min, price__lte=price_max)
            .annotate(avg_rating=Avg("reviews__rating"))
            [:limit * 2]
        )
        for p in similar_price:
            if p.id not in recommended_ids and len(recommendations) < limit:
                recommended_ids.add(p.id)
                recommendations.append(p)
    
    # Priority 4: High-rated products (fallback for diversity)
    if len(recommendations) < limit:
        high_rated = list(
            Product.objects.active()
            .select_related("category")
            .prefetch_related("tags")
            .exclude(id=product.id)
            .exclude(id__in=recommended_ids)
            .annotate(avg_rating=Avg("reviews__rating"))
            .filter(avg_rating__gte=4)
            .order_by("-avg_rating")
            [:limit]
        )
        for p in high_rated:
            if p.id not in recommended_ids and len(recommendations) < limit:
                recommended_ids.add(p.id)
                recommendations.append(p)
    
    return recommendations