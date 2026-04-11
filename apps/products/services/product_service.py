from typing import Iterable, Literal, Optional

from apps.products.models import Product
from apps.products.repositories.base import AbstractProductRepository

ActiveFilter = Literal["active", "inactive", "all"]


class ProductService:
    def __init__(self, repository: AbstractProductRepository) -> None:
        self._repository = repository

    def list_products(
        self,
        *,
        category_id: Optional[int] = None,
        supplier_id: Optional[int] = None,
        low_stock_only: bool = False,
        active_filter: ActiveFilter = "active",
    ) -> Iterable[Product]:
        qs = self._repository.get_all()
        # Soporte para listas (modo mock) sin .filter()
        if not hasattr(qs, "filter"):
            items = list(qs)
            if active_filter == "active":
                items = [p for p in items if getattr(p, "is_active", True)]
            elif active_filter == "inactive":
                items = [p for p in items if not getattr(p, "is_active", True)]
            if category_id is not None:
                items = [
                    p
                    for p in items
                    if getattr(p, "category_id", None) == category_id
                    or (
                        getattr(p, "category", None)
                        and getattr(p.category, "id", getattr(p.category, "pk", None)) == category_id
                    )
                ]
            if supplier_id is not None:
                items = [
                    p
                    for p in items
                    if getattr(p, "supplier_id", None) == supplier_id
                    or (
                        getattr(p, "supplier", None)
                        and getattr(p.supplier, "id", getattr(p.supplier, "pk", None)) == supplier_id
                    )
                ]
            if low_stock_only:
                items = [
                    p
                    for p in items
                    if getattr(p, "stock_quantity", 0) <= getattr(p, "minimum_stock", 0)
                ]
            return items
        if active_filter == "active":
            qs = qs.filter(is_active=True)
        elif active_filter == "inactive":
            qs = qs.filter(is_active=False)
        if category_id is not None:
            qs = qs.filter(category_id=category_id)
        if supplier_id is not None:
            qs = qs.filter(supplier_id=supplier_id)
        if low_stock_only:
            from django.db.models import F

            qs = qs.filter(stock_quantity__lte=F("minimum_stock"))
        return qs

    def create_product(self, **data) -> Product:
        product = Product(**data)
        return self._repository.save(product)

    def update_product(self, product: Product, **data) -> Product:
        for field, value in data.items():
            setattr(product, field, value)
        return self._repository.save(product)

    def deactivate_product(self, product: Product) -> Product:
        product.is_active = False
        return self._repository.save(product)

    def get_low_stock_products(self) -> Iterable[Product]:
        return self._repository.get_low_stock()

