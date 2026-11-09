"""
Utilidades y factories de prueba reutilizables por toda la suite.
No contiene tests en sí, solo helpers.
"""
from decimal import Decimal
from tienda.models import Categoria, Producto, Inventario, Venta, DetalleVenta


def crear_categoria(nombre="Bebidas", **kwargs):
    return Categoria.objects.create(
        nombre=nombre,
        descripcion=kwargs.get('descripcion', 'Categoría de prueba'),
        color=kwargs.get('color', '#6366f1'),
    )


def crear_producto(categoria=None, nombre="Coca-Cola", precio="25.50", **kwargs):
    if categoria is None:
        categoria = crear_categoria()
    return Producto.objects.create(
        nombre=nombre,
        precio_venta=Decimal(precio),
        categoria=categoria,
        **kwargs
    )


def crear_inventario(producto=None, cantidad=10, stock_minimo=5):
    if producto is None:
        producto = crear_producto()
    return Inventario.objects.create(
        producto=producto,
        cantidad=cantidad,
        stock_minimo=stock_minimo,
    )


def crear_venta(notas="Venta de prueba"):
    return Venta.objects.create(notas=notas)


def crear_detalle(venta=None, producto=None, cantidad=2, precio=None):
    if venta is None:
        venta = crear_venta()
    if producto is None:
        producto = crear_producto()
    if precio is None:
        precio = producto.precio_venta
    return DetalleVenta.objects.create(
        venta=venta,
        producto=producto,
        cantidad=cantidad,
        precio_unitario=precio,
    )


def crear_escenario_completo():
    """Crea categoría + producto + inventario listos para vender."""
    cat = crear_categoria(nombre="Snacks")
    prod = crear_producto(categoria=cat, nombre="Papas", precio="15.00")
    inv = crear_inventario(producto=prod, cantidad=20, stock_minimo=5)
    return cat, prod, inv
