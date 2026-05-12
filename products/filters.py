import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):
    """
    Declarative filter set for the product listing page.
    django-filter handles all query param parsing and validation automatically.
    """

    q = django_filters.CharFilter(field_name="name", lookup_expr="icontains", label="Search")
    category = django_filters.CharFilter(
        field_name="category__slug",
        lookup_expr="exact",
        label="Category",
    )
    tag = django_filters.CharFilter(
        field_name="tags__slug",
        lookup_expr="exact",
        label="Tag",
    )
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte", label="Min Price")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte", label="Max Price")
    ordering = django_filters.OrderingFilter(
        fields=(
            ("price", "price"),
            ("-price", "-price"),
            ("name", "name"),
            ("-created_at", "newest"),
        ),
        field_labels={
            "price": "Price: Low to High",
            "-price": "Price: High to Low",
            "name": "Name: A–Z",
            "newest": "Newest First",
        },
        label="Sort By",
    )

    class Meta:
        model = Product
        fields = ["q", "category", "tag", "min_price", "max_price"]
