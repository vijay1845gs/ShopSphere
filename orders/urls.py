from django.urls import path
from . import views

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("history/", views.OrderHistoryView.as_view(), name="order_history"),
    path("<int:pk>/", views.OrderDetailView.as_view(), name="order_detail"),
    path("<int:pk>/cancel/", views.cancel_order_view, name="cancel_order"),
]
