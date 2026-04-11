"""
Datos mock hardcodeados para visualización del sistema sin base de datos.
Activar con USE_MOCK_DATA = True en settings.
"""
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace


def _mk_category(pk, name, description=None):
    return SimpleNamespace(pk=pk, id=pk, name=name, description=description or "")


def _mk_supplier(pk, name, contact_email=None, phone=None, is_active=True):
    return SimpleNamespace(
        pk=pk,
        id=pk,
        name=name,
        contact_email=contact_email or "",
        phone=phone or "",
        is_active=is_active,
    )


def _mk_product(pk, name, sku, category_id, supplier_id, unit_price, stock_quantity, minimum_stock, is_active=True):
    return SimpleNamespace(
        pk=pk,
        id=pk,
        name=name,
        sku=sku,
        category_id=category_id,
        supplier_id=supplier_id,
        unit_price=Decimal(str(unit_price)),
        stock_quantity=stock_quantity,
        minimum_stock=minimum_stock,
        is_active=is_active,
    )


def _mk_user(username="demo"):
    return SimpleNamespace(pk=1, id=1, username=username, is_authenticated=True)


def _mk_movement(mid, product_id, movement_type, quantity, reason, performed_by_username, created_at_str):
    return SimpleNamespace(
        id=mid,
        pk=mid,
        product_id=product_id,
        movement_type=movement_type,
        quantity=quantity,
        reason=reason or "",
        performed_by=_mk_user(performed_by_username),
        created_at=datetime.fromisoformat(created_at_str),
    )


# --- Datos crudos (ids y referencias) ---
MOCK_CATEGORIES = [
    _mk_category(1, "Electrónica", "Dispositivos y componentes"),
    _mk_category(2, "Oficina", "Material de oficina"),
    _mk_category(3, "Limpieza", "Productos de limpieza"),
]

MOCK_SUPPLIERS = [
    _mk_supplier(1, "Proveedor Norte", "norte@example.com", "+34 600 111 222"),
    _mk_supplier(2, "Suministros Sur", "sur@example.com", "+34 600 333 444"),
]

# product: pk, name, sku, category_id, supplier_id, unit_price, stock_quantity, minimum_stock
MOCK_PRODUCTS_RAW = [
    (1, "Monitor 24\"", "MON-001", 1, 1, 199.99, 15, 5),
    (2, "Teclado USB", "TEC-002", 1, 1, 29.50, 8, 10),
    (3, "Papel A4 (500 h)", "PAP-003", 2, 2, 4.99, 3, 10),
    (4, "Bolígrafo azul", "BOL-004", 2, 2, 0.45, 120, 50),
    (5, "Detergente 1L", "DET-005", 3, 2, 3.20, 2, 8),
    (6, "Ratón inalámbrico", "RAT-006", 1, 1, 19.99, 4, 5),
]

# movement: id, product_id, type, quantity, reason, user, created_at
MOCK_MOVEMENTS_RAW = [
    (1, 1, "ENTRY", 20, "Recepción pedido", "admin", "2025-02-20T10:00:00"),
    (2, 3, "EXIT", 5, "Salida oficina", "admin", "2025-02-21T11:30:00"),
    (3, 5, "ENTRY", 10, "Reposición", "demo", "2025-02-22T09:15:00"),
    (4, 2, "EXIT", 2, "Venta", "demo", "2025-02-22T14:00:00"),
    (5, 1, "EXIT", 5, "Ajuste inventario", "admin", "2025-02-23T08:45:00"),
]


def _build_products():
    by_id = {c.pk: c for c in MOCK_CATEGORIES}
    sup_by_id = {s.pk: s for s in MOCK_SUPPLIERS}
    products = []
    for row in MOCK_PRODUCTS_RAW:
        pk, name, sku, cat_id, sup_id, price, stock, min_stock = row
        p = _mk_product(pk, name, sku, cat_id, sup_id, price, stock, min_stock)
        p.category = by_id.get(cat_id)
        p.supplier = sup_by_id.get(sup_id)
        products.append(p)
    return products


def _build_movements():
    products_by_id = {p.id: p for p in _build_products()}
    movements = []
    for row in MOCK_MOVEMENTS_RAW:
        mid, pid, mtype, qty, reason, user, created = row
        m = _mk_movement(mid, pid, mtype, qty, reason, user, created)
        m.product = products_by_id.get(pid)
        movements.append(m)
    return movements


# Listas listas para usar (objetos con .product, .category, etc. resueltos)
MOCK_PRODUCTS = _build_products()
MOCK_MOVEMENTS = _build_movements()
_next_product_id = max((p.id for p in MOCK_PRODUCTS), default=0) + 1
_next_movement_id = max((m.id for m in MOCK_MOVEMENTS), default=0) + 1


def get_mock_products(active_only=True):
    if active_only:
        return [p for p in MOCK_PRODUCTS if p.is_active]
    return list(MOCK_PRODUCTS)


def get_mock_product_by_id(product_id):
    for p in MOCK_PRODUCTS:
        if p.id == int(product_id):
            return p
    return None


def get_mock_low_stock_products():
    return [p for p in MOCK_PRODUCTS if p.is_active and p.stock_quantity <= p.minimum_stock]


def get_mock_movements():
    # Siempre devolver copia ordenada, más reciente primero
    return sorted(MOCK_MOVEMENTS, key=lambda m: m.created_at, reverse=True)


def create_mock_product(
    *,
    name,
    sku,
    category_id=None,
    supplier_id=None,
    unit_price=0,
    stock_quantity=0,
    minimum_stock=0,
    is_active=True,
):
    """
    Crea un producto en memoria y lo añade a la lista MOCK_PRODUCTS.
    """
    global _next_product_id

    p = _mk_product(
        _next_product_id,
        name,
        sku,
        category_id,
        supplier_id,
        unit_price,
        stock_quantity,
        minimum_stock,
        is_active=is_active,
    )
    # Resolver relaciones para que las vistas puedan mostrar category / supplier
    p.category = None
    if category_id is not None:
        p.category = next((c for c in MOCK_CATEGORIES if c.id == category_id), None)
    p.supplier = None
    if supplier_id is not None:
        p.supplier = next((s for s in MOCK_SUPPLIERS if s.id == supplier_id), None)

    MOCK_PRODUCTS.append(p)
    _next_product_id += 1
    return p


def update_mock_product(
    product_id,
    *,
    name,
    sku,
    category_id=None,
    supplier_id=None,
    unit_price=0,
    stock_quantity=0,
    minimum_stock=0,
    is_active=True,
):
    """
    Actualiza un producto existente en MOCK_PRODUCTS en memoria.
    """
    product = get_mock_product_by_id(product_id)
    if product is None:
        raise ValueError("Producto no encontrado.")

    product.name = name
    product.sku = sku
    product.unit_price = unit_price
    product.stock_quantity = stock_quantity
    product.minimum_stock = minimum_stock
    product.is_active = is_active

    product.category_id = category_id
    product.category = None
    if category_id is not None:
        product.category = next((c for c in MOCK_CATEGORIES if c.id == category_id), None)

    product.supplier_id = supplier_id
    product.supplier = None
    if supplier_id is not None:
        product.supplier = next((s for s in MOCK_SUPPLIERS if s.id == supplier_id), None)

    return product


def create_mock_movement(*, product_id, movement_type, quantity, reason, user):
    """
    Crea un movimiento en memoria y actualiza el stock del producto asociado.
    No persiste nada en base de datos; se mantiene solo mientras dure el proceso.
    """
    from apps.inventory.models import StockMovement  # import local para evitar ciclos

    global _next_movement_id

    product = get_mock_product_by_id(product_id)
    if product is None:
        raise ValueError("Producto no encontrado.")

    if movement_type == StockMovement.EXIT and quantity > product.stock_quantity:
        raise ValueError(
            f"La salida excede el stock disponible. Stock actual: {product.stock_quantity}."
        )

    if movement_type == StockMovement.ENTRY:
        product.stock_quantity += quantity
    elif movement_type == StockMovement.EXIT:
        product.stock_quantity -= quantity
    elif movement_type == StockMovement.ADJUSTMENT:
        product.stock_quantity = quantity

    username = getattr(user, "username", str(user))
    movement = SimpleNamespace(
        id=_next_movement_id,
        pk=_next_movement_id,
        product_id=product_id,
        movement_type=movement_type,
        quantity=quantity,
        reason=reason or "",
        performed_by=_mk_user(username),
        created_at=datetime.now(),
    )
    movement.product = product

    MOCK_MOVEMENTS.append(movement)
    _next_movement_id += 1
    return movement
