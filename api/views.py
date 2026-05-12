from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema, OpenApiParameter

from products.models import Product
from products.filters import ProductFilter
from orders.models import Order
from reviews.models import Review
from wishlist.models import Wishlist

from .serializers import (
    ProductListSerializer,
    ProductDetailSerializer,
    OrderSerializer,
    ReviewSerializer,
    WishlistSerializer,
    UserRegisterSerializer,
)


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterAPIView(generics.CreateAPIView):
    """POST /api/auth/register/ — create a new user account."""
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]


# ── Products ──────────────────────────────────────────────────────────────────

class ProductListAPIView(generics.ListAPIView):
    """
    GET /api/products/
    Supports: ?q=, ?category=, ?min_price=, ?max_price=, ?ordering=
    """
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["name", "description"]
    ordering_fields = ["price", "name", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            Product.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related("tags")
        )


class ProductDetailAPIView(generics.RetrieveAPIView):
    """GET /api/products/<slug>/"""
    serializer_class = ProductDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"
    queryset = Product.objects.filter(is_active=True).select_related("category").prefetch_related("tags")


# ── Reviews ───────────────────────────────────────────────────────────────────

class ProductReviewListCreateAPIView(generics.ListCreateAPIView):
    """
    GET  /api/products/<slug>/reviews/ — list reviews
    POST /api/products/<slug>/reviews/ — submit a review (auth required)
    """
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        # Safe for schema generation using .none() when swagger_fake_view
        if getattr(self, "swagger_fake_view", False):
            return Review.objects.none()
        product = get_object_or_404(Product, slug=self.kwargs["slug"])
        return Review.objects.filter(product=product).select_related("user")

    def perform_create(self, serializer):
        product = get_object_or_404(Product, slug=self.kwargs["slug"])
        Review.objects.update_or_create(
            product=product,
            user=self.request.user,
            defaults={
                "rating": serializer.validated_data["rating"],
                "comment": serializer.validated_data.get("comment", ""),
            },
        )


# ── Orders ────────────────────────────────────────────────────────────────────

class OrderListAPIView(generics.ListAPIView):
    """GET /api/orders/ — authenticated user's order history."""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related("items__product")
        )


class OrderDetailAPIView(generics.RetrieveAPIView):
    """GET /api/orders/<id>/ — single order, scoped to request.user."""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        return Order.objects.filter(user=self.request.user).prefetch_related("items__product")


# ── Wishlist ──────────────────────────────────────────────────────────────────

@extend_schema(responses=WishlistSerializer)
class WishlistAPIView(APIView):
    """
    GET    /api/wishlist/              — view wishlist
    POST   /api/wishlist/toggle/<id>/  — add or remove product
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        serializer = WishlistSerializer(wishlist)
        return Response(serializer.data)


@extend_schema(
    request=None,
    responses={
        200: {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["added", "removed"]}
            }
        }
    }
)
class WishlistToggleAPIView(APIView):
    """POST /api/wishlist/toggle/<product_id>/"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id, is_active=True)
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)

        if product in wishlist.products.all():
            wishlist.products.remove(product)
            return Response({"status": "removed"}, status=status.HTTP_200_OK)

        wishlist.products.add(product)
        return Response({"status": "added"}, status=status.HTTP_200_OK)
