from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from django.conf import settings

from apps.products.forms import CategoryForm, ProductForm, SupplierForm, get_product_form
from apps.products.models import Category, Product, Supplier
from apps.products.services.product_service import ProductService
from config.data_source import get_product_repository
from config.mock_data import (
    create_mock_product,
    get_mock_product_by_id,
    update_mock_product,
)


def _safe_int(value):
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


# ── Products ─────────────────────────────────────────────────────────────────

@method_decorator(login_required, name="dispatch")
class ProductListView(ListView):
    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"
    paginate_by = 20

    def get_queryset(self):
        repo = get_product_repository()
        service = ProductService(repo)
        category_id = self.request.GET.get("category")
        supplier_id = self.request.GET.get("supplier")
        low_stock_only = self.request.GET.get("low_stock") == "1"
        product_state = self.request.GET.get("product_state", "active") or "active"
        if product_state not in ("active", "inactive", "all"):
            product_state = "active"
        qs = service.list_products(
            category_id=_safe_int(category_id),
            supplier_id=_safe_int(supplier_id),
            low_stock_only=low_stock_only,
            active_filter=product_state,
        )
        q = self.request.GET.get("q", "").strip()
        if q and hasattr(qs, "filter"):
            qs = qs.filter(name__icontains=q) | qs.filter(sku__icontains=q)  # type: ignore[union-attr]
        elif q:
            qs = [p for p in qs if q.lower() in p.name.lower() or q.lower() in p.sku.lower()]
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if getattr(settings, "USE_MOCK_DATA", False):
            from config.mock_data import MOCK_CATEGORIES, MOCK_SUPPLIERS
            ctx["categories"] = MOCK_CATEGORIES
            ctx["suppliers"] = sorted(MOCK_SUPPLIERS, key=lambda s: s.name.lower())
        else:
            ctx["categories"] = Category.objects.all().order_by("name")
            ctx["suppliers"] = Supplier.objects.all().order_by("name")
        return ctx


@login_required
def product_create_view(request):
    form = get_product_form(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if getattr(settings, "USE_MOCK_DATA", False):
            create_mock_product(
                name=form.cleaned_data["name"],
                sku=form.cleaned_data["sku"],
                category_id=form.cleaned_data.get("category"),
                supplier_id=form.cleaned_data.get("supplier"),
                unit_price=form.cleaned_data["unit_price"],
                stock_quantity=form.cleaned_data["stock_quantity"],
                minimum_stock=form.cleaned_data["minimum_stock"],
                is_active=form.cleaned_data.get("is_active", True),
            )
            messages.success(request, "Producto creado correctamente (modo demo).")
            return redirect("products:list")
        repo = get_product_repository()
        service = ProductService(repo)
        service.create_product(**form.cleaned_data)
        messages.success(request, "Producto creado correctamente.")
        return redirect("products:list")
    return render(request, "products/product_form.html", {"form": form, "title": "Nuevo producto"})


@login_required
def product_update_view(request, pk):
    if getattr(settings, "USE_MOCK_DATA", False):
        product = get_mock_product_by_id(pk)
        if product is None:
            messages.error(request, "Producto no encontrado.")
            return redirect("products:list")
        form = get_product_form(request.POST or None, instance=product)
        if request.method == "POST" and form.is_valid():
            update_mock_product(
                pk,
                name=form.cleaned_data["name"],
                sku=form.cleaned_data["sku"],
                category_id=form.cleaned_data.get("category"),
                supplier_id=form.cleaned_data.get("supplier"),
                unit_price=form.cleaned_data["unit_price"],
                stock_quantity=form.cleaned_data["stock_quantity"],
                minimum_stock=form.cleaned_data["minimum_stock"],
                is_active=form.cleaned_data.get("is_active", True),
            )
            messages.success(request, "Producto actualizado correctamente (modo demo).")
            return redirect("products:list")
        return render(request, "products/product_form.html", {"form": form, "title": "Editar producto", "product": product})

    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)
    if request.method == "POST" and form.is_valid():
        repo = get_product_repository()
        service = ProductService(repo)
        service.update_product(product, **form.cleaned_data)
        messages.success(request, "Producto actualizado correctamente.")
        return redirect("products:list")
    return render(request, "products/product_form.html", {"form": form, "title": "Editar producto", "product": product})


# ── Categories ───────────────────────────────────────────────────────────────

@login_required
def category_list_view(request):
    if getattr(settings, "USE_MOCK_DATA", False):
        from config.mock_data import MOCK_CATEGORIES, MOCK_PRODUCTS
        cats = []
        for c in MOCK_CATEGORIES:
            c.product_count = sum(1 for p in MOCK_PRODUCTS if p.category_id == c.id)
            c.created_at = None
            cats.append(c)
        return render(request, "categories/category_list.html", {"categories": cats})
    categories = Category.objects.annotate(product_count=Count("products")).order_by("name")
    return render(request, "categories/category_list.html", {"categories": categories})


@login_required
def category_create_view(request):
    if getattr(settings, "USE_MOCK_DATA", False):
        from config.mock_data import MOCK_CATEGORIES, _mk_category
        if request.method == "POST":
            name = request.POST.get("name", "").strip()
            desc = request.POST.get("description", "").strip()
            if name:
                new_id = max((c.id for c in MOCK_CATEGORIES), default=0) + 1
                MOCK_CATEGORIES.append(_mk_category(new_id, name, desc))
                messages.success(request, "Categoría creada (modo demo).")
                return redirect("products:category_list")
        form = CategoryForm()
        return render(request, "categories/category_form.html", {"form": form, "title": "Nueva categoría"})

    form = CategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Categoría creada correctamente.")
        return redirect("products:category_list")
    return render(request, "categories/category_form.html", {"form": form, "title": "Nueva categoría"})


@login_required
def category_update_view(request, pk):
    if getattr(settings, "USE_MOCK_DATA", False):
        from config.mock_data import MOCK_CATEGORIES
        cat = next((c for c in MOCK_CATEGORIES if c.id == pk), None)
        if cat is None:
            messages.error(request, "Categoría no encontrada.")
            return redirect("products:category_list")
        if request.method == "POST":
            cat.name = request.POST.get("name", cat.name).strip()
            cat.description = request.POST.get("description", "").strip()
            messages.success(request, "Categoría actualizada (modo demo).")
            return redirect("products:category_list")
        form = CategoryForm(initial={"name": cat.name, "description": cat.description})
        return render(request, "categories/category_form.html", {"form": form, "title": "Editar categoría", "category": cat})

    category = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=category)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Categoría actualizada correctamente.")
        return redirect("products:category_list")
    return render(request, "categories/category_form.html", {"form": form, "title": "Editar categoría", "category": category})


@login_required
def category_delete_view(request, pk):
    if request.method != "POST":
        messages.warning(
            request,
            "Usa el botón Eliminar en la lista de categorías.",
        )
        return redirect("products:category_list")
    if getattr(settings, "USE_MOCK_DATA", False):
        from config.mock_data import MOCK_CATEGORIES, MOCK_PRODUCTS
        cat = next((c for c in MOCK_CATEGORIES if c.id == pk), None)
        if cat is None:
            messages.error(request, "Categoría no encontrada.")
            return redirect("products:category_list")
        for p in MOCK_PRODUCTS:
            if getattr(p, "category_id", None) == pk:
                p.category_id = None
                p.category = None
        MOCK_CATEGORIES[:] = [c for c in MOCK_CATEGORIES if c.id != pk]
        messages.success(request, "Categoría eliminada (modo demo).")
        return redirect("products:category_list")
    category = get_object_or_404(Category, pk=pk)
    name = category.name
    category.delete()
    messages.success(request, f"Categoría «{name}» eliminada. Los productos asociados quedaron sin categoría.")
    return redirect("products:category_list")


# ── Suppliers ────────────────────────────────────────────────────────────────

@login_required
def supplier_toggle_active_view(request, pk):
    if request.method != "POST":
        messages.warning(
            request,
            "Usa el botón en la lista para cambiar el estado del proveedor.",
        )
        return redirect("products:supplier_list")
    if getattr(settings, "USE_MOCK_DATA", False):
        from config.mock_data import MOCK_SUPPLIERS
        sup = next((s for s in MOCK_SUPPLIERS if s.id == pk), None)
        if sup is None:
            messages.error(request, "Proveedor no encontrado.")
            return redirect("products:supplier_list")
        sup.is_active = not getattr(sup, "is_active", True)
        messages.success(
            request,
            "Proveedor habilitado." if sup.is_active else "Proveedor inhabilitado.",
        )
        return redirect("products:supplier_list")
    supplier = get_object_or_404(Supplier, pk=pk)
    supplier.is_active = not supplier.is_active
    supplier.save(update_fields=["is_active"])
    messages.success(
        request,
        "Proveedor habilitado." if supplier.is_active else "Proveedor inhabilitado.",
    )
    return redirect("products:supplier_list")


@login_required
def supplier_list_view(request):
    if getattr(settings, "USE_MOCK_DATA", False):
        from config.mock_data import MOCK_SUPPLIERS, MOCK_PRODUCTS
        sups = []
        for s in MOCK_SUPPLIERS:
            s.product_count = sum(1 for p in MOCK_PRODUCTS if p.supplier_id == s.id)
            s.created_at = None
            sups.append(s)
        return render(request, "suppliers/supplier_list.html", {"suppliers": sups})
    suppliers = Supplier.objects.annotate(product_count=Count("products")).order_by("name")
    return render(request, "suppliers/supplier_list.html", {"suppliers": suppliers})


@login_required
def supplier_create_view(request):
    if getattr(settings, "USE_MOCK_DATA", False):
        from config.mock_data import MOCK_SUPPLIERS, _mk_supplier
        if request.method == "POST":
            name = request.POST.get("name", "").strip()
            email = request.POST.get("contact_email", "").strip()
            phone = request.POST.get("phone", "").strip()
            if name:
                new_id = max((s.id for s in MOCK_SUPPLIERS), default=0) + 1
                MOCK_SUPPLIERS.append(_mk_supplier(new_id, name, email, phone))
                messages.success(request, "Proveedor creado (modo demo).")
                return redirect("products:supplier_list")
        form = SupplierForm()
        return render(request, "suppliers/supplier_form.html", {"form": form, "title": "Nuevo proveedor"})

    form = SupplierForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Proveedor creado correctamente.")
        return redirect("products:supplier_list")
    return render(request, "suppliers/supplier_form.html", {"form": form, "title": "Nuevo proveedor"})


@login_required
def supplier_update_view(request, pk):
    if getattr(settings, "USE_MOCK_DATA", False):
        from config.mock_data import MOCK_SUPPLIERS
        sup = next((s for s in MOCK_SUPPLIERS if s.id == pk), None)
        if sup is None:
            messages.error(request, "Proveedor no encontrado.")
            return redirect("products:supplier_list")
        if request.method == "POST":
            sup.name = request.POST.get("name", sup.name).strip()
            sup.contact_email = request.POST.get("contact_email", "").strip()
            sup.phone = request.POST.get("phone", "").strip()
            messages.success(request, "Proveedor actualizado (modo demo).")
            return redirect("products:supplier_list")
        form = SupplierForm(initial={"name": sup.name, "contact_email": sup.contact_email, "phone": sup.phone})
        return render(request, "suppliers/supplier_form.html", {"form": form, "title": "Editar proveedor", "supplier": sup})

    supplier = get_object_or_404(Supplier, pk=pk)
    form = SupplierForm(request.POST or None, instance=supplier)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Proveedor actualizado correctamente.")
        return redirect("products:supplier_list")
    return render(request, "suppliers/supplier_form.html", {"form": form, "title": "Editar proveedor", "supplier": supplier})
