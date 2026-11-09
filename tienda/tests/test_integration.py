"""
Tests de integración: flujos de usuario de principio a fin.
"""
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse

from tienda.models import Categoria, Producto, Inventario, Venta


class FlujoCompletoVentaTest(TestCase):
    """Simula el flujo completo de un kiosquero usando la app."""

    def setUp(self):
        self.client = Client()

    def test_flujo_crear_categoria_producto_vender(self):
        # 1. Crear categoría
        self.client.post(reverse('categoria_crear'), {
            'nombre': 'Bebidas', 'descripcion': 'Refrescos', 'color': '#0000ff',
        })
        cat = Categoria.objects.get(nombre='Bebidas')

        # 2. Crear producto
        self.client.post(reverse('producto_crear'), {
            'nombre': 'Coca-Cola', 'precio_venta': '25.00',
            'categoria': cat.pk,
        })
        prod = Producto.objects.get(nombre='Coca-Cola')

        # 3. Crear inventario
        self.client.post(reverse('inventario_crear'), {
            'producto': prod.pk, 'cantidad': 100, 'stock_minimo': 10,
        })
        inv = Inventario.objects.get(producto=prod)
        self.assertEqual(inv.cantidad, 100)

        # 4. Crear venta
        r = self.client.post(reverse('venta_crear'), {'notas': 'Cliente 1'})
        venta = Venta.objects.get(notas='Cliente 1')
        self.assertRedirects(r, reverse('venta_detalle', args=[venta.pk]))

        # 5. Agregar producto a la venta
        self.client.post(reverse('venta_detalle', args=[venta.pk]), {
            'producto': prod.pk, 'cantidad': 3, 'precio_unitario': '25.00',
        })

        # 6. Verificar stock descontado y total
        inv.refresh_from_db()
        venta.refresh_from_db()
        self.assertEqual(inv.cantidad, 97)
        self.assertEqual(venta.total, Decimal('75.00'))

        # 7. Verificar que la venta aparece en el listado
        r = self.client.get(reverse('venta_lista'))
        self.assertContains(r, venta.folio)

        # 8. Verificar que el dashboard refleja el total
        r = self.client.get(reverse('dashboard'))
        self.assertEqual(r.context['ventas_hoy_total'], Decimal('75.00'))


class FlujoMultiplesVentasTest(TestCase):
    """Verifica que los folios se generen secuencialmente y el stock se descuente correctamente."""

    def setUp(self):
        self.client = Client()
        cat = Categoria.objects.create(nombre="Test", color="#000000")
        self.prod = Producto.objects.create(
            nombre="Prod", precio_venta=Decimal("10.00"), categoria=cat
        )
        Inventario.objects.create(producto=self.prod, cantidad=100, stock_minimo=5)

    def test_tres_ventas_secuenciales(self):
        folios = []
        for i in range(3):
            self.client.post(reverse('venta_crear'), {'notas': f'Venta {i}'})
            venta = Venta.objects.order_by('-id').first()
            folios.append(venta.folio)
            self.client.post(reverse('venta_detalle', args=[venta.pk]), {
                'producto': self.prod.pk, 'cantidad': 2,
                'precio_unitario': '10.00',
            })

        # Folios secuenciales
        self.assertEqual(len(set(folios)), 3)
        # Stock final: 100 - 3*2 = 94
        self.prod.inventarios.first().refresh_from_db()
        self.assertEqual(self.prod.stock, 94)


class FlujoEliminacionRestauraStockTest(TestCase):
    """Eliminar detalles o ventas debe restaurar el stock."""

    def setUp(self):
        self.client = Client()
        cat = Categoria.objects.create(nombre="Restore", color="#000000")
        self.prod = Producto.objects.create(
            nombre="RestoreProd", precio_venta=Decimal("5.00"), categoria=cat
        )
        self.inv = Inventario.objects.create(
            producto=self.prod, cantidad=50, stock_minimo=5
        )

    def test_eliminar_detalle_restaura(self):
        venta = Venta.objects.create()
        self.client.post(reverse('venta_detalle', args=[venta.pk]), {
            'producto': self.prod.pk, 'cantidad': 10,
            'precio_unitario': '5.00',
        })
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.cantidad, 40)

        detalle = venta.detalles.first()
        self.client.post(reverse('detalle_eliminar', args=[detalle.pk]))

        self.inv.refresh_from_db()
        self.assertEqual(self.inv.cantidad, 50)

    def test_eliminar_venta_restaura_todo(self):
        venta = Venta.objects.create()
        self.client.post(reverse('venta_detalle', args=[venta.pk]), {
            'producto': self.prod.pk, 'cantidad': 15,
            'precio_unitario': '5.00',
        })
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.cantidad, 35)

        self.client.post(reverse('venta_eliminar', args=[venta.pk]))

        self.inv.refresh_from_db()
        self.assertEqual(self.inv.cantidad, 50)
        self.assertFalse(Venta.objects.filter(pk=venta.pk).exists())


class FlujoFiltrosTest(TestCase):
    """Verifica que los filtros de cada módulo funcionen encadenados."""

    def setUp(self):
        self.client = Client()

    def test_categorias_filtro_combinado(self):
        Categoria.objects.create(nombre="Bebidas", descripcion="frías")
        Categoria.objects.create(nombre="Snacks", descripcion="frituras")
        Categoria.objects.create(nombre="Bebidas Calientes", descripcion="café")

        r = self.client.get(reverse('categoria_lista'), {'q': 'Bebidas'})
        self.assertEqual(r.context['categorias'].count(), 2)

    def test_productos_filtro_categoria_y_q(self):
        cat1 = Categoria.objects.create(nombre="A", color="#111111")
        cat2 = Categoria.objects.create(nombre="B", color="#222222")
        Producto.objects.create(nombre="Prod A1", precio_venta=1, categoria=cat1)
        Producto.objects.create(nombre="Prod A2", precio_venta=2, categoria=cat1)
        Producto.objects.create(nombre="Prod B1", precio_venta=3, categoria=cat2)

        r = self.client.get(reverse('producto_lista'), {
            'q': 'Prod', 'categoria': cat1.pk,
        })
        self.assertEqual(r.context['productos'].count(), 2)


class FlujoBajoStockTest(TestCase):
    """Un producto que llega al mínimo debe aparecer en el dashboard."""

    def setUp(self):
        self.client = Client()
        cat = Categoria.objects.create(nombre="Stock", color="#000000")
        self.prod = Producto.objects.create(
            nombre="ProdBajoStock", precio_venta=Decimal("10.00"), categoria=cat
        )
        self.inv = Inventario.objects.create(
            producto=self.prod, cantidad=6, stock_minimo=5
        )

    def test_vender_hasta_bajo_stock_aparece_en_dashboard(self):
        venta = Venta.objects.create()
        self.client.post(reverse('venta_detalle', args=[venta.pk]), {
            'producto': self.prod.pk, 'cantidad': 2,
            'precio_unitario': '10.00',
        })
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.cantidad, 4)
        self.assertTrue(self.inv.bajo_stock)

        r = self.client.get(reverse('dashboard'))
        self.assertEqual(len(r.context['productos_bajo_stock']), 1)
        self.assertContains(r, 'ProdBajoStock')
