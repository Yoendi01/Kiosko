"""
Tests de la API /api/producto/<pk>/precio/.
"""
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
import json

from tienda.tests.test_utils import (
    crear_producto, crear_inventario
)


class ApiPrecioProductoTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.prod = crear_producto(nombre="Galletas", precio="18.75")

    def test_devuelve_200_json(self):
        r = self.client.get(reverse('api_precio_producto', args=[self.prod.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'application/json')

    def test_estructura_respuesta(self):
        r = self.client.get(reverse('api_precio_producto', args=[self.prod.pk]))
        data = json.loads(r.content)
        for key in ['ok', 'id', 'nombre', 'precio', 'stock']:
            self.assertIn(key, data)

    def test_precio_correcto(self):
        r = self.client.get(reverse('api_precio_producto', args=[self.prod.pk]))
        data = json.loads(r.content)
        self.assertTrue(data['ok'])
        self.assertEqual(data['precio'], 18.75)
        self.assertEqual(data['nombre'], "Galletas")

    def test_stock_sin_inventario_es_cero(self):
        r = self.client.get(reverse('api_precio_producto', args=[self.prod.pk]))
        data = json.loads(r.content)
        self.assertEqual(data['stock'], 0)

    def test_stock_con_inventario(self):
        crear_inventario(producto=self.prod, cantidad=42)
        r = self.client.get(reverse('api_precio_producto', args=[self.prod.pk]))
        data = json.loads(r.content)
        self.assertEqual(data['stock'], 42)

    def test_producto_inexistente_404(self):
        r = self.client.get(reverse('api_precio_producto', args=[99999]))
        self.assertEqual(r.status_code, 404)
        data = json.loads(r.content)
        self.assertFalse(data['ok'])
        self.assertIn('error', data)

