"""
Integration tests for product and authentication views.
Tests the full request/response cycle with the Django test client.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.products.models import Category, Product, Supplier

User = get_user_model()


class TestLoginView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", password="secret123")
        self.url = reverse("accounts:login")

    def test_login_page_renders(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_valid_credentials_redirect_to_dashboard(self):
        response = self.client.post(self.url, {"username": "admin", "password": "secret123"})
        self.assertRedirects(response, reverse("dashboard:index"), fetch_redirect_response=False)

    def test_invalid_credentials_stay_on_login(self):
        response = self.client.post(self.url, {"username": "admin", "password": "wrong"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "")  # page re-renders (no redirect)
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class TestProductListViewAuthentication(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", password="secret123")
        self.url = reverse("products:list")

    def test_unauthenticated_redirects_to_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={self.url}",
            fetch_redirect_response=False,
        )

    def test_authenticated_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class TestProductListFilters(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", password="secret123")
        self.client.force_login(self.user)
        self.cat = Category.objects.create(name="Electrónica")
        Product.objects.create(name="Laptop", sku="LAP-001", unit_price="999", stock_quantity=5, minimum_stock=2, category=self.cat)
        Product.objects.create(name="Silla",  sku="SIL-001", unit_price="150", stock_quantity=3, minimum_stock=1)

    def test_product_list_shows_active_products(self):
        response = self.client.get(reverse("products:list"))
        self.assertContains(response, "Laptop")
        self.assertContains(response, "Silla")

    def test_filter_by_category_returns_matching(self):
        response = self.client.get(reverse("products:list"), {"category": self.cat.pk})
        self.assertContains(response, "Laptop")
        self.assertNotContains(response, "Silla")

    def test_inactive_product_not_shown_by_default(self):
        Product.objects.filter(sku="SIL-001").update(is_active=False)
        response = self.client.get(reverse("products:list"))
        self.assertNotContains(response, "Silla")


class TestDashboardView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", password="secret123")
        self.client.force_login(self.user)

    def test_dashboard_returns_200(self):
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 200)


class TestCategoryViews(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", password="secret123")
        self.client.force_login(self.user)

    def test_create_category(self):
        response = self.client.post(
            reverse("products:category_create"),
            {"name": "Herramientas", "description": "Herramientas de trabajo"},
        )
        self.assertEqual(Category.objects.filter(name="Herramientas").count(), 1)

    def test_delete_category(self):
        cat = Category.objects.create(name="Temporal")
        self.client.post(reverse("products:category_delete", args=[cat.pk]))
        self.assertFalse(Category.objects.filter(pk=cat.pk).exists())


class TestSupplierViews(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", password="secret123")
        self.client.force_login(self.user)

    def test_supplier_list_returns_200(self):
        response = self.client.get(reverse("products:supplier_list"))
        self.assertEqual(response.status_code, 200)

    def test_toggle_supplier_active_status(self):
        supplier = Supplier.objects.create(name="Proveedor Test", is_active=True)
        self.client.post(reverse("products:supplier_toggle_active", args=[supplier.pk]))
        supplier.refresh_from_db()
        self.assertFalse(supplier.is_active)
