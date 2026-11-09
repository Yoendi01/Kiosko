"""
Tests de modelos: creación, str, propiedades, validaciones,
señales de guardado y lógica de negocio.
"""
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from tienda.models import Categoria, Producto, Inventario, Venta, DetalleVenta
from tienda.tests.test_utils import (
    crear_categoria, crear_producto, crear_inventario,
    crear_venta, crear_detalle, crear_escenario_completo,
)


class CategoriaModelTest(TestCase):
    """Tests del modelo Categoria."""

    def test_creacion_basica(self):
        cat = Categoria.objects.create(nombre="Bebidas")
        self.assertEqual(cat.nombre, "Bebidas")
        self.assertEqual(cat.color, "#6366f1")  # default
        self.assertIsNotNone(cat.creado)

    def test_str_devuelve_nombre(self):
        cat = crear_categoria(nombre="Lácteos")
        self.assertEqual(str(cat), "Lácteos")

    def test_nombre_unico(self):
        crear_categoria(nombre="Única")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Categoria.objects.create(nombre="Única")

    def test_ordering_por_nombre(self):
        Categoria.objects.create(nombre="Zeta")
        Categoria.objects.create(nombre="Alfa")
        Categoria.objects.create(nombre="Mango")
        nombres = list(Categoria.objects.values_list('nombre', flat=True))
        self.assertEqual(nombres, ["Alfa", "Mango", "Zeta"])

    def test_descripcion_opcional(self):
        cat = Categoria.objects.create(nombre="Sin desc")
        self.assertIsNone(cat.descripcion)

    def test_verbose_name(self):
        self.assertEqual(Categoria._meta.verbose_name, "Categoría")
        self.assertEqual(Categoria._meta.verbose_name_plural, "Categorías")


class ProductoModelTest(TestCase):
    """Tests del modelo Producto."""

    def setUp(self):
        self.categoria = crear_categoria()

    def test_creacion_basica(self):
        prod = Producto.objects.create(
            nombre="Agua", precio_venta=Decimal("10.00"),
            categoria=self.categoria,
        )
        self.assertEqual(prod.nombre, "Agua")
        self.assertEqual(prod.precio_venta, Decimal("10.00"))

    def test_str_devuelve_nombre(self):
        prod = crear_producto(nombre="Refresco",categoria=self.categoria)
        self.assertEqual(str(prod), "Refresco")

    def test_precio_negativo_falla_validacion(self):
        prod = Producto(
            nombre="Malo", precio_venta=Decimal("-5.00"),
            categoria=self.categoria,
        )
        with self.assertRaises(ValidationError):
            prod.full_clean()

    def test_precio_cero_es_valido(self):
        prod = Producto(
            nombre="Gratis", precio_venta=Decimal("0.00"),
            categoria=self.categoria,
        )
        prod.full_clean()  # No debe lanzar

    def test_stock_sin_inventario_es_cero(self):
        prod = crear_producto(nombre="Sin stock",categoria=self.categoria)
        self.assertEqual(prod.stock, 0)

    def test_stock_con_inventario(self):
        prod = crear_producto(categoria=self.categoria)
        crear_inventario(producto=prod, cantidad=42)
        self.assertEqual(prod.stock, 42)

    def test_categoria_eliminada_elimina_productos(self):
        prod = crear_producto(nombre="A borrar",categoria=self.categoria)
        self.categoria.delete()
        self.assertFalse(Producto.objects.filter(nombre="A borrar").exists())

    def test_ordering_por_nombre(self):
        Producto.objects.create(nombre="Zanahoria", precio_venta=Decimal("1"), categoria=self.categoria)
        Producto.objects.create(nombre="Arroz", precio_venta=Decimal("2"), categoria=self.categoria)
        nombres = list(Producto.objects.values_list('nombre', flat=True))
        self.assertEqual(nombres, ["Arroz", "Zanahoria"])

    def test_related_name_productos(self):
        crear_producto(categoria=self.categoria)
        crear_producto(categoria=self.categoria, nombre="Otro")
        self.assertEqual(self.categoria.productos.count(), 2)


class InventarioModelTest(TestCase):
    """Tests del modelo Inventario."""

    def test_creacion_basica(self):
        inv = crear_inventario(cantidad=15, stock_minimo=3)
        self.assertEqual(inv.cantidad, 15)
        self.assertEqual(inv.stock_minimo, 3)

    def test_str(self):
        inv = crear_inventario()
        self.assertIn(inv.producto.nombre, str(inv))
        self.assertIn(str(inv.cantidad), str(inv))

    def test_bajo_stock_verdadero(self):
        inv = crear_inventario(cantidad=5, stock_minimo=5)
        self.assertTrue(inv.bajo_stock)

    def test_bajo_stock_falso(self):
        inv = crear_inventario(cantidad=10, stock_minimo=5)
        self.assertFalse(inv.bajo_stock)

    def test_bajo_stock_en_cero(self):
        inv = crear_inventario(cantidad=0, stock_minimo=5)
        self.assertTrue(inv.bajo_stock)

    def test_stock_minimo_default(self):
        prod = crear_producto()
        inv = Inventario.objects.create(producto=prod, cantidad=10)
        self.assertEqual(inv.stock_minimo, 5)

    def test_producto_eliminado_elimina_inventario(self):
        inv = crear_inventario()
        pk = inv.pk
        inv.producto.delete()
        self.assertFalse(Inventario.objects.filter(pk=pk).exists())

    def test_actualizado_cambia_al_modificar(self):
        inv = crear_inventario()
        viejo = inv.actualizado
        inv.cantidad = 999
        inv.save()
        inv.refresh_from_db()
        self.assertGreaterEqual(inv.actualizado, viejo)


class VentaModelTest(TestCase):
    """Tests del modelo Venta."""

    def setUp(self):
        self.categoria = crear_categoria(nombre="Comida")

    def test_folio_autogenerado(self):
        venta = Venta.objects.create()
        self.assertTrue(venta.folio.startswith("V"))
        self.assertEqual(len(venta.folio), 7)  # V + 6 dígitos

    def test_folio_incrementa(self):
        v1 = Venta.objects.create()
        v2 = Venta.objects.create()
        self.assertNotEqual(v1.folio, v2.folio)
        self.assertEqual(v1.folio, "V000001")
        self.assertEqual(v2.folio, "V000002")

    def test_folio_no_se_sobrescribe_al_guardar(self):
        venta = Venta.objects.create()
        folio_original = venta.folio
        venta.notas = "Modificada"
        venta.save()
        venta.refresh_from_db()
        self.assertEqual(venta.folio, folio_original)

    def test_total_default_cero(self):
        venta = Venta.objects.create()
        self.assertEqual(venta.total, Decimal("0"))

    def test_str(self):
        venta = Venta.objects.create()
        self.assertIn(venta.folio, str(venta))

    def test_recalcular_total(self):
        venta = crear_venta()
        prod1 = crear_producto(precio="10.00", nombre="P1",categoria=self.categoria)
        prod2 = crear_producto(precio="20.00", nombre="P2",categoria=self.categoria)
        crear_detalle(venta=venta, producto=prod1, cantidad=2, precio=Decimal("10.00"))
        crear_detalle(venta=venta, producto=prod2, cantidad=1, precio=Decimal("20.00"))
        venta.recalcular_total()
        venta.refresh_from_db()
        self.assertEqual(venta.total, Decimal("40.00"))

    def test_ordering_por_fecha_desc(self):
        v1 = Venta.objects.create()
        v2 = Venta.objects.create()
        ventas = list(Venta.objects.all())
        self.assertEqual(ventas[0].id, v2.id)  # más reciente primero


class DetalleVentaModelTest(TestCase):
    """Tests del modelo DetalleVenta."""

    def test_creacion_basica(self):
        d = crear_detalle(cantidad=3)
        self.assertEqual(d.cantidad, 3)

    def test_subtotal(self):
        d = crear_detalle(cantidad=3, precio=Decimal("5.00"))
        self.assertEqual(d.subtotal, Decimal("15.00"))

    def test_str(self):
        d = crear_detalle(cantidad=2)
        self.assertIn(d.producto.nombre, str(d))
        self.assertIn("2", str(d))

    def test_cantidad_cero_falla_validacion(self):
        d = DetalleVenta(
            venta=crear_venta(),
            producto=crear_producto(),
            cantidad=0,
            precio_unitario=Decimal("10.00"),
        )
        with self.assertRaises(ValidationError):
            d.full_clean()

    def test_cantidad_negativa_falla(self):
        d = DetalleVenta(
            venta=crear_venta(),
            producto=crear_producto(),
            cantidad=-1,
            precio_unitario=Decimal("10.00"),
        )
        with self.assertRaises(ValidationError):
            d.full_clean()

    def test_venta_eliminada_cascada(self):
        venta = crear_venta()
        crear_detalle(venta=venta)
        venta.delete()
        self.assertEqual(DetalleVenta.objects.count(), 0)



class LogicaNegocioTest(TestCase):
    """Tests de lógica de negocio combinada."""

    def test_escenario_completo(self):
        cat, prod, inv = crear_escenario_completo()
        self.assertEqual(prod.categoria, cat)
        self.assertEqual(prod.stock, 20)

    def test_vender_reduce_stock_manual(self):
        cat, prod, inv = crear_escenario_completo()
        venta = crear_venta()
        cantidad = 5
        inv.cantidad -= cantidad
        inv.save()
        crear_detalle(venta=venta, producto=prod, cantidad=cantidad)
        venta.recalcular_total()
        prod.refresh_from_db()
        self.assertEqual(prod.stock, 15)
        self.assertEqual(venta.total, Decimal("75.00"))
