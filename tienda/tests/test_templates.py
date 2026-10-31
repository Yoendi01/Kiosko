"""
Tests de templates: contenido HTML, elementos clave, clases CSS, mensajes.
"""
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse

from tienda.tests.test_utils import (
    crear_categoria, crear_producto, crear_inventario,
    crear_venta, crear_detalle,
)


class BaseTemplateTest(TestCase):
    """El template base debe tener la estructura del layout."""

    def setUp(self):
        self.client = Client()

    def test_sidebar_presente(self):
        r = self.client.get(reverse('dashboard'))
        self.assertContains(r, 'class="sidebar"')

    def test_nav_links_presentes(self):
        r = self.client.get(reverse('dashboard'))
        for nombre in ['Dashboard', 'Productos', 'Categorías', 'Inventario', 'Ventas']:
            self.assertContains(r, nombre)

    def test_css_cargado(self):
        r = self.client.get(reverse('dashboard'))
        self.assertContains(r, 'style.css')

    def test_link_activo_segun_seccion(self):
        r = self.client.get(reverse('producto_lista'))
        self.assertContains(r, 'nav-link active')


class DashboardTemplateTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_stat_cards_presentes(self):
        r = self.client.get(reverse('dashboard'))
        self.assertContains(r, 'stat-card')

    def test_titulo_dashboard(self):
        r = self.client.get(reverse('dashboard'))
        self.assertContains(r, 'Dashboard')

    def test_tabla_bajo_stock(self):
        prod = crear_producto(nombre="Bajito")
        crear_inventario(producto=prod, cantidad=1, stock_minimo=5)
        r = self.client.get(reverse('dashboard'))
        self.assertContains(r, 'Bajito')
        self.assertContains(r, 'badge-warning')


class CategoriaTemplateTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_empty_state_sin_categorias(self):
        r = self.client.get(reverse('categoria_lista'))
        self.assertContains(r, 'empty-state')
        self.assertContains(r, 'Sin categorías')

    def test_tabla_con_categoria(self):
        crear_categoria(nombre="TestCat")
        r = self.client.get(reverse('categoria_lista'))
        self.assertContains(r, 'TestCat')
        self.assertContains(r, '<table')

    def test_form_renderiza_campos(self):
        r = self.client.get(reverse('categoria_crear'))
        self.assertContains(r, 'name="nombre"')
        self.assertContains(r, 'name="descripcion"')
        self.assertContains(r, 'name="color"')


class ProductoTemplateTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_badge_con_color_categoria(self):
        cat = crear_categoria(nombre="Verde", color="#00ff00")
        crear_producto(categoria=cat, nombre="Lechuga")
        r = self.client.get(reverse('producto_lista'))
        self.assertContains(r, '#00ff00')

    def test_precio_formateado(self):
        cat = crear_categoria()
        crear_producto(categoria=cat, nombre="Pan", precio="25.50")
        r = self.client.get(reverse('producto_lista'))
        self.assertContains(r, '25.50')


class VentaTemplateTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_detalle_muestra_total_box(self):
        venta = crear_venta()
        venta.total = Decimal("99.99")
        venta.save()
        r = self.client.get(reverse('venta_detalle', args=[venta.pk]))
        self.assertContains(r, 'venta-total-box')
        self.assertContains(r, '99.99')

    def test_detalle_muestra_form_agregar(self):
        venta = crear_venta()
        r = self.client.get(reverse('venta_detalle', args=[venta.pk]))
        self.assertContains(r, 'Agregar producto')
        self.assertContains(r, 'id_producto')
        self.assertContains(r, 'id_precio_unitario')

    def test_detalle_incluye_script_autocompletar(self):
        """Verifica que el JS de autocompletado esté en el HTML."""
        venta = crear_venta()
        r = self.client.get(reverse('venta_detalle', args=[venta.pk]))
        self.assertContains(r, 'api/producto/')
        self.assertContains(r, 'fetch(')
        self.assertContains(r, 'id_precio_unitario')

    def test_detalle_muestra_stock_info(self):
        venta = crear_venta()
        r = self.client.get(reverse('venta_detalle', args=[venta.pk]))
        self.assertContains(r, 'stock-info')

    def test_tabla_detalles_con_productos(self):
        venta = crear_venta()
        prod = crear_producto(nombre="ItemX", precio="5.00",
                              categoria=crear_categoria(nombre="CatX"))
        crear_detalle(venta=venta, producto=prod, cantidad=2, precio=Decimal("5.00"))
        r = self.client.get(reverse('venta_detalle', args=[venta.pk]))
        self.assertContains(r, 'ItemX')


class MensajesTemplateTest(TestCase):
    """Verifica que los mensajes flash se rendericen correctamente."""

    def setUp(self):
        self.client = Client()

    def test_mensaje_success_visible(self):
        r = self.client.post(reverse('categoria_crear'), {
            'nombre': 'NuevaCat', 'color': '#000000',
        }, follow=True)
        self.assertContains(r, 'message success')
        self.assertContains(r, 'Categoría creada')

    def test_mensaje_error_stock(self):
        venta = crear_venta()
        prod = crear_producto(nombre="X", categoria=crear_categoria(nombre="CX"))
        crear_inventario(producto=prod, cantidad=1)
        r = self.client.post(
            reverse('venta_detalle', args=[venta.pk]),
            {'producto': prod.pk, 'cantidad': 99, 'precio_unitario': '10.00'},
            follow=True,
        )
        self.assertContains(r, 'message error')
