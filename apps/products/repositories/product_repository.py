from typing import Iterable

from django.db.models import F

from apps.products.models import Product
from .base import AbstractProductRepository


class DjangoProductRepository(AbstractProductRepository):
    def get_all(self) -> Iterable[Product]:
        return Product.objects.all()

    def get_by_id(self, product_id: int) -> Product:
        return Product.objects.get(pk=product_id, is_active=True)

    def get_by_sku(self, sku: str) -> Product:
        return Product.objects.get(sku=sku, is_active=True)

    def get_low_stock(self) -> Iterable[Product]:
        return Product.objects.filter(
            is_active=True,
            stock_quantity__lte=F("minimum_stock"),
        )

    def save(self, product: Product) -> Product:
        product.save()
        return product

    def delete(self, product: Product) -> None:
        product.is_active = False
        product.save(update_fields=["is_active"])

