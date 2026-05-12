import logging
from django.views.generic import ListView, DetailView
from django.db.models import Avg, Count

from .models import Product, Category
from .filters import ProductFilter
from .cache import (
    categories_key,
    CATEGORY_TTL,
    product_detail_key,
    PRODUCT_DETAIL_TTL,
    product_list_key,
    LIST_TTL,
)
from .recommendations import get_recommendations
from django.core.cache import cache

logger = logging.getLogger("django")


class ProductListView(ListView):
    model = Product
    template_name = "products.html"
    context_object_name = "products"
    paginate_by = 9

    def get_queryset(self):
        queryset = (
            Product.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related("tags")
            .annotate(avg_rating=Avg("reviews__rating"))
        )
        self.filterset = ProductFilter(self.request.GET, queryset=queryset)
        qs = self.filterset.qs
        if not qs.ordered:
            qs = qs.order_by("-created_at")
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filterset"] = self.filterset

        # Build cache key including page and filters
        page = self.request.GET.get("page", 1)
        filters = {k: v for k, v in self.request.GET.items() if k not in ["page"]}
        cache_key = product_list_key(page=int(page), filters=filters, sort="created")

        products = cache.get(cache_key)
        if products is None:
            products = list(self.get_queryset())
            cache.set(cache_key, products, LIST_TTL)
            logger.info(f"[CACHE MISS] {cache_key}")
        else:
            logger.info(f"[CACHE HIT] {cache_key}")
        context["products"] = products
        context["is_cached"] = products is not None

        # Cache categories queryset (rarely changes)
        cat_cache_key = categories_key()
        categories = cache.get(cat_cache_key)
        if categories is None:
            categories = list(Category.objects.all())
            cache.set(cat_cache_key, categories, CATEGORY_TTL)
            logger.info(f"[CACHE MISS] {cat_cache_key}")
        else:
            logger.info(f"[CACHE HIT] {cat_cache_key}")
        context["categories"] = categories

        if self.request.user.is_authenticated:
            from wishlist.models import Wishlist
            wishlist, _ = Wishlist.objects.get_or_create(user=self.request.user)
            context["wishlist_ids"] = set(wishlist.products.values_list("id", flat=True))
        else:
            context["wishlist_ids"] = set()
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = "product_detail.html"
    context_object_name = "product"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related("category").prefetch_related("tags")

    def get_object(self, queryset=None):
        product = super().get_object(queryset)
        
        # Try cache for product detail
        cache_key = product_detail_key(product.slug)
        cached_product = cache.get(cache_key)
        if cached_product:
            logger.info(f"[CACHE HIT] {cache_key}")
            return cached_product
        
        # Cache the product with related data
        cache.set(cache_key, product, PRODUCT_DETAIL_TTL)
        logger.info(f"[CACHE MISS] {cache_key}")
        return product

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        reviews = product.reviews.select_related("user")
        agg = reviews.aggregate(avg=Avg("rating"), count=Count("id"))

        context["reviews"] = reviews
        context["avg_rating"] = round(agg["avg"]) if agg["avg"] else None
        context["review_count"] = agg["count"]
        context["meta_title"] = product.get_meta_title()
        context["meta_description"] = product.get_meta_description()
        context["recommendations"] = get_recommendations(product, limit=6)

        if self.request.user.is_authenticated:
            context["user_review"] = reviews.filter(user=self.request.user).first()
            from wishlist.models import Wishlist
            wishlist, _ = Wishlist.objects.get_or_create(user=self.request.user)
            context["in_wishlist"] = wishlist.products.filter(id=product.id).exists()

        return context