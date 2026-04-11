"""
Repositorio que usa datos mock (config.mock_data) en lugar de la BD.
Se usa cuando USE_MOCK_DATA = True.
"""
from typing import Iterable

from config.mock_data import (
    get_mock_low_stock_products,
    get_mock_product_by_id,
    get_mock_products,
)


class MockProductRepository:
    """Devuelve objetos mock con los mismos atributos que Product para las vistas."""

    def get_all(self) -> Iterable:
        return get_mock_products(active_only=False)

    def get_by_id(self, product_id: int):
        return get_mock_product_by_id(product_id)

    def get_by_sku(self, sku: str):
        for p in get_mock_products(active_only=True):
            if p.sku == sku:
                return p
        return None

    def get_low_stock(self) -> Iterable:
        return get_mock_low_stock_products()

    def save(self, product) -> None:
        # Solo visualización: no persistir
        pass

    def delete(self, product) -> None:
        # Solo visualización: no persistir
        pass
