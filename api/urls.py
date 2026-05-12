from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    RegisterAPIView,
    ProductListAPIView,
    ProductDetailAPIView,
    ProductReviewListCreateAPIView,
    OrderListAPIView,
    OrderDetailAPIView,
    WishlistAPIView,
    WishlistToggleAPIView,
)

urlpatterns = [
    # Auth
    path("auth/register/", RegisterAPIView.as_view(), name="api_register"),
    path("auth/token/", TokenObtainPairView.as_view(), name="api_token_obtain"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="api_token_refresh"),

    # Products
    path("products/", ProductListAPIView.as_view(), name="api_product_list"),
    path("products/<slug:slug>/", ProductDetailAPIView.as_view(), name="api_product_detail"),
    path("products/<slug:slug>/reviews/", ProductReviewListCreateAPIView.as_view(), name="api_product_reviews"),

    # Orders
    path("orders/", OrderListAPIView.as_view(), name="api_order_list"),
    path("orders/<int:pk>/", OrderDetailAPIView.as_view(), name="api_order_detail"),

    # Wishlist
    path("wishlist/", WishlistAPIView.as_view(), name="api_wishlist"),
    path("wishlist/toggle/<int:product_id>/", WishlistToggleAPIView.as_view(), name="api_wishlist_toggle"),
]
