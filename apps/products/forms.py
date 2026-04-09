from django import forms
from django.conf import settings

from .models import Product, Category, Supplier


# ── Category ──────────────────────────────────────────────────────────────────

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ej. Electrónicos"}),
            "description": forms.Textarea(attrs={"rows": 3, "placeholder": "Descripción opcional"}),
        }


# ── Supplier ──────────────────────────────────────────────────────────────────

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["name", "contact_email", "phone"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ej. TechDistrib RD"}),
            "contact_email": forms.EmailInput(attrs={"placeholder": "contacto@empresa.com"}),
            "phone": forms.TextInput(attrs={"placeholder": "809-000-0000"}),
        }


# ── Product ───────────────────────────────────────────────────────────────────

def get_product_form(data=None, *, instance=None):
    if getattr(settings, "USE_MOCK_DATA", False):
        return ProductFormMock(data=data, instance=instance)
    return ProductForm(data=data, instance=instance)


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name", "sku", "category", "supplier",
            "unit_price", "stock_quantity", "minimum_stock", "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.all().order_by("name")
        self.fields["category"].required = False
        self.fields["supplier"].queryset = Supplier.objects.all().order_by("name")
        self.fields["supplier"].required = False


class ProductFormMock(forms.Form):
    """Formulario de producto en modo mock (sin BD)."""

    name = forms.CharField(label="Nombre", max_length=200)
    sku = forms.CharField(label="SKU", max_length=50)
    category = forms.TypedChoiceField(
        label="Categoría", choices=[], coerce=lambda v: int(v) if v not in (None, "") else None,
        required=False, empty_value=None,
    )
    supplier = forms.TypedChoiceField(
        label="Proveedor", choices=[], coerce=lambda v: int(v) if v not in (None, "") else None,
        required=False, empty_value=None,
    )
    unit_price = forms.DecimalField(label="Precio unitario", max_digits=10, decimal_places=2, min_value=0)
    stock_quantity = forms.IntegerField(label="Stock", min_value=0)
    minimum_stock = forms.IntegerField(label="Stock mínimo", min_value=0)
    is_active = forms.BooleanField(label="Activo", required=False, initial=True)

    def __init__(self, data=None, *, instance=None, **kwargs):
        super().__init__(data=data, **kwargs)
        from config.mock_data import MOCK_CATEGORIES, MOCK_SUPPLIERS
        self.fields["category"].choices = [("", "Sin categoría")] + [(c.id, c.name) for c in MOCK_CATEGORIES]
        self.fields["supplier"].choices = [("", "Sin proveedor")] + [(s.id, s.name) for s in MOCK_SUPPLIERS]
        if instance is not None and not data:
            self.initial.update({
                "name": getattr(instance, "name", ""),
                "sku": getattr(instance, "sku", ""),
                "category": getattr(instance, "category_id", None),
                "supplier": getattr(instance, "supplier_id", None),
                "unit_price": getattr(instance, "unit_price", 0),
                "stock_quantity": getattr(instance, "stock_quantity", 0),
                "minimum_stock": getattr(instance, "minimum_stock", 0),
                "is_active": getattr(instance, "is_active", True),
            })
