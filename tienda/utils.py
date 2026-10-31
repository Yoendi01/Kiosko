from models import Producto, ProductoSueltoContador, Inventario


def procesar_conteo_venta_suelto(producto, cantidad: int, valor_unidad = 20) -> tuple[int,int]:

    ps = ProductoSueltoContador.objects.get(producto=producto)
    unidades = (ps.conteo + cantidad) / valor_unidad
    ps.conteo = (ps.conteo + cantidad) % valor_unidad
    ps.save()

    inv = Inventario.objects.get(producto=producto)
    inv.cantidad = inv.cantidad - unidades
    inv.save()


def procesar_conteo_venta_unidad(producto, cantidad: int, valor_unidad = 20) -> tuple[int,int]:

    pass

