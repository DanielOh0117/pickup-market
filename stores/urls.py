from django.urls import path

from . import views


app_name = "stores"

urlpatterns = [
    path(
        "<int:store_id>/products/",
        views.product_list,
        name="product_list",
    ),
    path(
        "<int:store_id>/cart/",
        views.cart_detail,
        name="cart_detail",
    ),
    path(
        "owner/products/",
        views.owner_product_list,
        name="owner_product_list",
    ),
    path(
        "owner/products/add/",
        views.owner_product_create,
        name="owner_product_create",
    ),
    path(
        "owner/products/<int:product_id>/edit/",
        views.owner_product_update,
        name="owner_product_update",
    ),
]