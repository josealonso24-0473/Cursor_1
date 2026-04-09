from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import ListView, TemplateView

from apps.inventory.forms import get_stock_movement_form
from apps.inventory.models import StockMovement
from apps.inventory.observers.base import StockSubject
from apps.inventory.observers.stock_alert_observer import LowStockAlertObserver
from apps.inventory.services.inventory_service import InventoryService, InsufficientStockError
from apps.products.services.product_service import ProductService
from config.data_source import get_product_repository
from config.mock_data import create_mock_movement, get_mock_movements


@method_decorator(login_required, name="dispatch")
class MovementListView(ListView):
    model = StockMovement
    template_name = "inventory/movement_list.html"
    context_object_name = "movements"
    paginate_by = 20

    def get_queryset(self):
        if getattr(settings, "USE_MOCK_DATA", False):
            movements = get_mock_movements()
            mov_type = self.request.GET.get("type")
            if mov_type:
                movements = [m for m in movements if m.movement_type == mov_type]
            return movements
        qs = StockMovement.objects.select_related("product", "performed_by").all()
        mov_type = self.request.GET.get("type")
        if mov_type:
            qs = qs.filter(movement_type=mov_type)
        return qs


@login_required
def movement_create_view(request):
    # Pre-select product from querystring
    initial_product = request.GET.get("product")
    form = get_stock_movement_form(request.POST or None)

    if request.method == "POST" and form.is_valid():
        if getattr(settings, "USE_MOCK_DATA", False):
            try:
                create_mock_movement(
                    product_id=form.cleaned_data["product"],
                    movement_type=form.cleaned_data["movement_type"],
                    quantity=form.cleaned_data["quantity"],
                    reason=form.cleaned_data.get("reason") or "",
                    user=request.user,
                )
            except ValueError as exc:
                form.add_error(None, str(exc))
            else:
                messages.success(request, "Movimiento registrado correctamente (modo demo).")
                return redirect("inventory:movements")
        else:
            repo = get_product_repository()
            subject = StockSubject()
            subject.attach(LowStockAlertObserver())
            service = InventoryService(repo, subject)
            product_id = form.cleaned_data["product"]
            if hasattr(product_id, "id"):
                product_id = product_id.id
            try:
                service.register_movement(
                    product_id=product_id,
                    movement_type=form.cleaned_data["movement_type"],
                    quantity=form.cleaned_data["quantity"],
                    reason=form.cleaned_data.get("reason") or "",
                    user=request.user,
                )
            except InsufficientStockError as exc:
                form.add_error(None, str(exc))
            else:
                messages.success(request, "Movimiento registrado correctamente.")
                return redirect("inventory:movements")

    return render(request, "inventory/movement_form.html", {"form": form, "initial_product": initial_product})


@method_decorator(login_required, name="dispatch")
class DashboardView(TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        repo = get_product_repository()
        product_service = ProductService(repo)
        low_stock_products = product_service.get_low_stock_products()

        if getattr(settings, "USE_MOCK_DATA", False):
            from config.mock_data import MOCK_PRODUCTS, MOCK_CATEGORIES
            recent_movements = get_mock_movements()[:10]
            total_products = sum(1 for p in MOCK_PRODUCTS if p.is_active)
            total_movements = len(get_mock_movements())
            total_categories = len(MOCK_CATEGORIES)
        else:
            recent_movements = StockMovement.objects.select_related("product").all()[:10]
            from apps.products.models import Product, Category
            total_products = Product.objects.filter(is_active=True).count()
            total_movements = StockMovement.objects.count()
            total_categories = Category.objects.count()

        context.update({
            "low_stock_products": low_stock_products,
            "recent_movements": recent_movements,
            "total_products": total_products,
            "total_movements": total_movements,
            "total_categories": total_categories,
        })
        return context
