from django.urls import path
from . import views

urlpatterns = [
    path("", views.WishlistView.as_view(), name="wishlist_detail"),
    path("toggle/<int:product_id>/", views.toggle_wishlist, name="toggle_wishlist"),
]
