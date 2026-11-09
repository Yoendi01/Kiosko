"""
Tests de resolución de URLs: rutas, nombres, parámetros.
"""
from django.test import TestCase
from django.urls import reverse, resolve


class UrlsTest(TestCase):

    def test_dashboard_url(self):
        self.assertEqual(reverse('dashboard'), '/')

    def test_categoria_urls(self):
        self.assertEqual(reverse('categoria_lista'), '/categorias/')
        self.assertEqual(reverse('categoria_crear'), '/categorias/crear/')
        self.assertEqual(reverse('categoria_editar', args=[1]), '/categorias/1/editar/')
        self.assertEqual(reverse('categoria_eliminar', args=[1]), '/categorias/1/eliminar/')

    def test_producto_urls(self):
        self.assertEqual(reverse('producto_lista'), '/productos/')
        self.assertEqual(reverse('producto_crear'), '/productos/crear/')
        self.assertEqual(reverse('producto_editar', args=[1]), '/productos/1/editar/')
        self.assertEqual(reverse('producto_eliminar', args=[1]), '/productos/1/eliminar/')

    def test_inventario_urls(self):
        self.assertEqual(reverse('inventario_lista'), '/inventario/')
        self.assertEqual(reverse('inventario_crear'), '/inventario/crear/')
        self.assertEqual(reverse('inventario_editar', args=[1]), '/inventario/1/editar/')
        self.assertEqual(reverse('inventario_eliminar', args=[1]), '/inventario/1/eliminar/')

    def test_venta_urls(self):
        self.assertEqual(reverse('venta_lista'), '/ventas/')
        self.assertEqual(reverse('venta_crear'), '/ventas/crear/')
        self.assertEqual(reverse('venta_detalle', args=[1]), '/ventas/1/')
        self.assertEqual(reverse('venta_editar', args=[1]), '/ventas/1/editar/')
        self.assertEqual(reverse('venta_eliminar', args=[1]), '/ventas/1/eliminar/')
        self.assertEqual(reverse('detalle_eliminar', args=[1]), '/detalles/1/eliminar/')

    def test_api_url(self):
        self.assertEqual(
            reverse('api_precio_producto', args=[1]),
            '/api/producto/1/precio/'
        )

    def test_resolve_dashboard(self):
        match = resolve('/')
        self.assertEqual(match.url_name, 'dashboard')

    def test_resolve_venta_detalle(self):
        match = resolve('/ventas/5/')
        self.assertEqual(match.url_name, 'venta_detalle')
        self.assertEqual(match.kwargs['pk'], 5)

    def test_resolve_api(self):
        match = resolve('/api/producto/42/precio/')
        self.assertEqual(match.url_name, 'api_precio_producto')
        self.assertEqual(match.kwargs['pk'], 42)
