"""
Unit tests for ProductService.
Uses an in-memory FakeRepository — no database required.
"""
from types import SimpleNamespace
from django.test import SimpleTestCase

from apps.products.repositories.base import AbstractProductRepository
from apps.products.services.product_service import ProductService


def make_product(**kwargs):
    defaults = dict(
        id=1, name="Widget", sku="WID-001", is_active=True,
        stock_quantity=10, minimum_stock=5,
        category_id=None, supplier_id=None,
        category=None, supplier=None,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class FakeRepository(AbstractProductRepository):
    def __init__(self, products=None):
        self._products = list(products or [])

    def get_all(self):
        return list(self._products)

    def get_by_id(self, product_id):
        for p in self._products:
            if p.id == product_id:
                return p
        raise LookupError(f"Product {product_id} not found")

    def get_by_sku(self, sku):
        for p in self._products:
            if p.sku == sku:
                return p
        return None

    def get_low_stock(self):
        return [p for p in self._products if p.stock_quantity <= p.minimum_stock]

    def save(self, product):
        if product not in self._products:
            self._products.append(product)
        return product

    def delete(self, product):
        self._products.remove(product)


class TestProductServiceListProducts(SimpleTestCase):
    def setUp(self):
        self.products = [
            make_product(id=1, name="A", sku="A-001", is_active=True, category_id=10, supplier_id=20, stock_quantity=3, minimum_stock=5),
            make_product(id=2, name="B", sku="B-002", is_active=True, category_id=10, supplier_id=99, stock_quantity=20, minimum_stock=5),
            make_product(id=3, name="C", sku="C-003", is_active=False, category_id=99, supplier_id=20, stock_quantity=0, minimum_stock=5),
        ]
        self.service = ProductService(FakeRepository(self.products))

    def test_list_active_by_default(self):
        result = list(self.service.list_products())
        self.assertEqual(len(result), 2)
        self.assertTrue(all(p.is_active for p in result))

    def test_list_inactive(self):
        result = list(self.service.list_products(active_filter="inactive"))
        self.assertEqual(len(result), 1)
        self.assertFalse(result[0].is_active)

    def test_list_all(self):
        result = list(self.service.list_products(active_filter="all"))
        self.assertEqual(len(result), 3)

    def test_filter_by_category(self):
        result = list(self.service.list_products(active_filter="all", category_id=10))
        self.assertEqual(len(result), 2)

    def test_filter_by_supplier(self):
        result = list(self.service.list_products(active_filter="all", supplier_id=20))
        self.assertEqual(len(result), 2)

    def test_low_stock_only(self):
        result = list(self.service.list_products(low_stock_only=True))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].sku, "A-001")


class TestProductServiceMutations(SimpleTestCase):
    def setUp(self):
        self.product = make_product(id=1, name="Widget", sku="WID-001", is_active=True, stock_quantity=10)
        self.repo = FakeRepository([self.product])
        self.service = ProductService(self.repo)

    def test_update_product_changes_fields(self):
        updated = self.service.update_product(self.product, name="Super Widget", stock_quantity=50)
        self.assertEqual(updated.name, "Super Widget")
        self.assertEqual(updated.stock_quantity, 50)

    def test_deactivate_product_sets_is_active_false(self):
        result = self.service.deactivate_product(self.product)
        self.assertFalse(result.is_active)

    def test_get_low_stock_products(self):
        low = make_product(id=2, sku="LOW-001", stock_quantity=2, minimum_stock=10)
        self.repo._products.append(low)
        result = list(self.service.get_low_stock_products())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].sku, "LOW-001")
