from django.urls import path

from .views import (
    ProductListView,
    product_create_view,
    product_update_view,
    category_list_view,
    category_create_view,
    category_update_view,
    category_delete_view,
    supplier_list_view,
    supplier_create_view,
    supplier_update_view,
    supplier_toggle_active_view,
)

app_name = "products"

urlpatterns = [
    # Products
    path("", ProductListView.as_view(), name="list"),
    path("new/", product_create_view, name="create"),
    path("<int:pk>/edit/", product_update_view, name="update"),

    # Categories
    path("categories/", category_list_view, name="category_list"),
    path("categories/new/", category_create_view, name="category_create"),
    path("categories/<int:pk>/delete/", category_delete_view, name="category_delete"),
    path("categories/<int:pk>/edit/", category_update_view, name="category_update"),

    # Suppliers
    path("suppliers/", supplier_list_view, name="supplier_list"),
    path("suppliers/new/", supplier_create_view, name="supplier_create"),
    path(
        "suppliers/<int:pk>/toggle-active/",
        supplier_toggle_active_view,
        name="supplier_toggle_active",
    ),
    path("suppliers/<int:pk>/edit/", supplier_update_view, name="supplier_update"),
]
