"""
Tests de formularios: validación de campos, widgets y guardado.
"""
from decimal import Decimal
from django.test import TestCase

from tienda.forms import (
    CategoriaForm, ProductoForm, InventarioForm,
    VentaForm, DetalleVentaForm,
)
from tienda.tests.test_utils import (
    crear_categoria, crear_producto, crear_inventario, crear_venta,
)


class CategoriaFormTest(TestCase):

    def test_form_valido(self):
        form = CategoriaForm(data={
            'nombre': 'Bebidas',
            'descripcion': 'Refrescos y jugos',
            'color': '#ff0000',
        })
        self.assertTrue(form.is_valid())

    def test_form_sin_nombre_es_invalido(self):
        form = CategoriaForm(data={'nombre': '', 'color': '#000000'})
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_form_nombre_duplicado_falla(self):
        crear_categoria(nombre="Duplicada")
        form = CategoriaForm(data={'nombre': 'Duplicada'})
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_widgets_css_aplicados(self):
        form = CategoriaForm()
        self.assertIn('form-input', form.fields['nombre'].widget.attrs.get('class', ''))



class ProductoFormTest(TestCase):

    def setUp(self):
        self.cat = crear_categoria()

    def test_form_valido(self):
        form = ProductoForm(data={
            'nombre': 'Sabritas',
            'precio_venta': '18.50',
            'categoria': self.cat.pk,
        })
        self.assertTrue(form.is_valid())

    def test_precio_negativo_falla(self):
        form = ProductoForm(data={
            'nombre': 'Malo',
            'precio_venta': '-5.00',
            'categoria': self.cat.pk,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('precio_venta', form.errors)

    def test_sin_categoria_falla(self):
        form = ProductoForm(data={
            'nombre': 'X',
            'precio_venta': '10.00',
        })
        self.assertFalse(form.is_valid())

    def test_precio_cero_valido(self):
        form = ProductoForm(data={
            'nombre': 'Gratis',
            'precio_venta': '0.00',
            'categoria': self.cat.pk,
        })
        self.assertTrue(form.is_valid())

    def test_guardar_crea_producto(self):
        form = ProductoForm(data={
            'nombre': 'Nuevo',
            'precio_venta': '12.00',
            'categoria': self.cat.pk,
        })
        self.assertTrue(form.is_valid())
        prod = form.save()
        self.assertEqual(prod.nombre, 'Nuevo')
        self.assertEqual(prod.precio_venta, Decimal('12.00'))


class InventarioFormTest(TestCase):

    def setUp(self):
        self.prod = crear_producto()

    def test_form_valido(self):
        form = InventarioForm(data={
            'producto': self.prod.pk,
            'cantidad': 25,
            'stock_minimo': 5,
        })
        self.assertTrue(form.is_valid())

    def test_cantidad_negativa_falla(self):
        form = InventarioForm(data={
            'producto': self.prod.pk,
            'cantidad': -3,
            'stock_minimo': 5,
        })
        self.assertFalse(form.is_valid())

    def test_sin_producto_falla(self):
        form = InventarioForm(data={'cantidad': 10, 'stock_minimo': 5})
        self.assertFalse(form.is_valid())

    def test_crear_inventario(self):
        
        cat = crear_categoria("test")
        prod = crear_producto(cat,"test")
        inv = crear_inventario(prod,10)
        self.assertEqual(inv.cantidad,10)
        self.assertEqual(inv.producto.nombre,'test')


class VentaFormTest(TestCase):

    def test_form_notas_opcionales(self):
        form = VentaForm(data={'notas': ''})
        self.assertTrue(form.is_valid())

    def test_form_crea_venta(self):
        form = VentaForm(data={'notas': 'Primera venta'})
        self.assertTrue(form.is_valid())
        venta = form.save()
        self.assertTrue(venta.folio.startswith('V'))


class DetalleVentaFormTest(TestCase):

    def setUp(self):
        self.prod = crear_producto(precio="15.00")

    def test_form_valido(self):
        form = DetalleVentaForm(data={
            'producto': self.prod.pk,
            'cantidad': 2,
            'precio_unitario': '15.00',
        })
        self.assertTrue(form.is_valid())

    def test_cantidad_cero_falla(self):
        form = DetalleVentaForm(data={
            'producto': self.prod.pk,
            'cantidad': 0,
            'precio_unitario': '15.00',
        })
        self.assertFalse(form.is_valid())

    def test_label_incluye_precio(self):
        form = DetalleVentaForm()
        label = form.fields['producto'].label_from_instance(self.prod)
        self.assertIn(self.prod.nombre, label)
        self.assertIn('15.00', label)

    def test_precio_requerido(self):
        form = DetalleVentaForm(data={
            'producto': self.prod.pk,
            'cantidad': 1,
            'precio_unitario': '',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('precio_unitario', form.errors)

    def test_crear_venta(self):

        venta = crear_venta("Venta 1")
        self.assertEqual(venta.folio,"V000001")
        self.assertEqual(venta.notas,"Venta 1")
