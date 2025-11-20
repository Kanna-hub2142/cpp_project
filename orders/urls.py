from django.urls import path
from . import views

urlpatterns = [
    path("", views.product_list_view, name="product_list"),
    path("orders/", views.order_list_view, name="order_list"),
    path("orders/create/", views.order_create_view, name="order_create"),
    path("orders/create/<int:product_id>/", views.order_create_view, name="order_create_for_product"),
    path("orders/<int:pk>/", views.order_detail_view, name="order_detail"),
    path("orders/<int:pk>/edit/", views.order_update_view, name="order_update"),
    path("orders/<int:pk>/delete/", views.order_delete_view, name="order_delete"),
    path("staff/orders/<int:pk>/status/", views.admin_order_status_update_view, name="admin_order_status"),
    path("staff/orders/dashboard/", views.admin_dashboard_view, name="admin_dashboard"),
]
