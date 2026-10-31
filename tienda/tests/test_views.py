"""
Tests de vistas: dashboard, CRUDs, filtros, mensajes y status codes.
"""
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from tienda.models import Categoria, Producto, Inventario, Venta
from tienda.tests.test_utils import (
    crear_categoria, crear_producto, crear_inventario,
    crear_venta, crear_detalle, crear_escenario_completo,
)


class DashboardViewTest(TestCase):


    def setUp(self):
        self.categoria = crear_categoria(nombre="Cigarros")
        self.client = Client()

    def test_dashboard_200(self):
        r = self.client.get(reverse('dashboard'))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'dashboard.html')

    def test_dashboard_context_keys(self):
        r = self.client.get(reverse('dashboard'))
        for key in ['total_productos', 'total_categorias',
                    'ventas_hoy_total', 'ventas_hoy_cantidad',
                    'ventas_semana_total', 'ventas_semana_cantidad',
                    'productos_bajo_stock']:
            self.assertIn(key, r.context)

    def test_dashboard_cuenta_productos(self):
        crear_producto(nombre="P1",categoria=self.categoria)
        crear_producto(nombre="P2",categoria=self.categoria)
        r = self.client.get(reverse('dashboard'))
        self.assertEqual(r.context['total_productos'], 2)

    def test_dashboard_cuenta_categorias(self):
        crear_categoria(nombre="C1")
        crear_categoria(nombre="C2")
        r = self.client.get(reverse('dashboard'))
        self.assertEqual(r.context['total_categorias'], 3)

    def test_dashboard_ventas_hoy(self):
        venta = crear_venta()
        venta.total = Decimal("100.00")
        venta.save()
        r = self.client.get(reverse('dashboard'))
        self.assertEqual(r.context['ventas_hoy_total'], Decimal("100.00"))
        self.assertEqual(r.context['ventas_hoy_cantidad'], 1)

    def test_dashboard_ventas_antiguas_no_cuentan_hoy(self):
        venta = crear_venta()
        venta.fecha = timezone.now() - timedelta(days=30)
        venta.total = Decimal("500.00")
        venta.save()
        r = self.client.get(reverse('dashboard'))
        self.assertEqual(r.context['ventas_hoy_total'], 0)

    def test_dashboard_muestra_bajo_stock(self):
        prod = crear_producto()
        crear_inventario(producto=prod, cantidad=2, stock_minimo=5)
        r = self.client.get(reverse('dashboard'))
        self.assertEqual(len(r.context['productos_bajo_stock']), 1)


class CategoriaViewsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.cat = crear_categoria(nombre="Existente")

    # ---- LISTA ----
    def test_lista_200(self):
        r = self.client.get(reverse('categoria_lista'))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'categorias/lista.html')

    def test_lista_muestra_categorias(self):
        r = self.client.get(reverse('categoria_lista'))
        self.assertContains(r, "Existente")

    def test_lista_filtro_q(self):
        crear_categoria(nombre="Bebidas")
        r = self.client.get(reverse('categoria_lista'), {'q': 'Beb'})
        self.assertContains(r, "Bebidas")
        self.assertNotContains(r, "Existente")

    def test_lista_filtro_sin_resultados(self):
        r = self.client.get(reverse('categoria_lista'), {'q': 'zzz'})
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, "Existente")

    # ---- CREAR ----
    def test_crear_get_200(self):
        r = self.client.get(reverse('categoria_crear'))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'categorias/form.html')

    def test_crear_post_valido(self):
        r = self.client.post(reverse('categoria_crear'), {
            'nombre': 'Nueva', 'descripcion': 'x', 'color': '#000000',
        })
        self.assertRedirects(r, reverse('categoria_lista'))
        self.assertTrue(Categoria.objects.filter(nombre='Nueva').exists())

    def test_crear_post_invalido(self):
        r = self.client.post(reverse('categoria_crear'), {'nombre': ''})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Categoria.objects.filter(nombre='').exists())

    def test_crear_muestra_mensaje(self):
        r = self.client.post(reverse('categoria_crear'), {
            'nombre': 'Mensaje', 'color': '#000000',
        }, follow=True)
        self.assertContains(r, 'Categoría creada')

    # ---- EDITAR ----
    def test_editar_get_200(self):
        r = self.client.get(reverse('categoria_editar', args=[self.cat.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'categorias/form.html')

    def test_editar_post_valido(self):
        r = self.client.post(reverse('categoria_editar', args=[self.cat.pk]), {
            'nombre': 'Actualizada', 'color': '#111111',
        })
        self.assertRedirects(r, reverse('categoria_lista'))
        self.cat.refresh_from_db()
        self.assertEqual(self.cat.nombre, 'Actualizada')

    def test_editar_404(self):
        r = self.client.get(reverse('categoria_editar', args=[99999]))
        self.assertEqual(r.status_code, 404)

    # ---- ELIMINAR ----
    def test_eliminar_get_confirma(self):
        r = self.client.get(reverse('categoria_eliminar', args=[self.cat.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'categorias/eliminar.html')

    def test_eliminar_post_borra(self):
        pk = self.cat.pk
        r = self.client.post(reverse('categoria_eliminar', args=[pk]))
        self.assertRedirects(r, reverse('categoria_lista'))
        self.assertFalse(Categoria.objects.filter(pk=pk).exists())

    def test_eliminar_cascada_borra_productos(self):
        prod = crear_producto(categoria=self.cat)
        pk_prod = prod.pk
        self.client.post(reverse('categoria_eliminar', args=[self.cat.pk]))
        self.assertFalse(Producto.objects.filter(pk=pk_prod).exists())


class ProductoViewsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.cat = crear_categoria(nombre="Bebidas")
        self.prod = crear_producto(categoria=self.cat, nombre="Coca")

    def test_lista_200(self):
        r = self.client.get(reverse('producto_lista'))
        self.assertEqual(r.status_code, 200)

    def test_lista_muestra_producto(self):
        r = self.client.get(reverse('producto_lista'))
        self.assertContains(r, "Coca")

    def test_lista_filtro_q(self):
        crear_producto(categoria=self.cat, nombre="Pepsi")
        r = self.client.get(reverse('producto_lista'), {'q': 'Pep'})
        self.assertContains(r, "Pepsi")
        self.assertNotContains(r, "Coca")

    def test_lista_filtro_categoria(self):
        cat2 = crear_categoria(nombre="Snacks")
        crear_producto(categoria=cat2, nombre="Sabritas")
        r = self.client.get(reverse('producto_lista'), {'categoria': cat2.pk})
        self.assertContains(r, "Sabritas")
        self.assertNotContains(r, "Coca")

    def test_lista_muestra_stock(self):
        crear_inventario(producto=self.prod, cantidad=99)
        r = self.client.get(reverse('producto_lista'))
        self.assertContains(r, "99")

    def test_crear_get(self):
        r = self.client.get(reverse('producto_crear'))
        self.assertEqual(r.status_code, 200)

    def test_crear_post_valido(self):
        r = self.client.post(reverse('producto_crear'), {
            'nombre': 'Nuevo', 'precio_venta': '22.50',
            'categoria': self.cat.pk,
        })
        self.assertRedirects(r, reverse('producto_lista'))
        self.assertTrue(Producto.objects.filter(nombre='Nuevo').exists())

    def test_crear_post_invalido(self):
        r = self.client.post(reverse('producto_crear'), {
            'nombre': '', 'precio_venta': '-5', 'categoria': self.cat.pk,
        })
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Producto.objects.filter(nombre='').exists())

    def test_editar_post(self):
        self.client.post(reverse('producto_editar', args=[self.prod.pk]), {
            'nombre': 'Editado', 'precio_venta': '30.00',
            'categoria': self.cat.pk,
        })
        self.prod.refresh_from_db()
        self.assertEqual(self.prod.nombre, 'Editado')
        self.assertEqual(self.prod.precio_venta, Decimal('30.00'))

    def test_eliminar_post(self):
        pk = self.prod.pk
        r = self.client.post(reverse('producto_eliminar', args=[pk]))
        self.assertRedirects(r, reverse('producto_lista'))
        self.assertFalse(Producto.objects.filter(pk=pk).exists())


class InventarioViewsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.prod = crear_producto(nombre="Refresco")
        self.inv = crear_inventario(producto=self.prod, cantidad=10, stock_minimo=5)

    def test_lista_200(self):
        r = self.client.get(reverse('inventario_lista'))
        self.assertEqual(r.status_code, 200)

    def test_lista_muestra_datos(self):
        r = self.client.get(reverse('inventario_lista'))
        self.assertContains(r, "Refresco")

    def test_lista_filtro_bajo(self):
        crear_inventario(
            producto=crear_producto(nombre="Agotado", categoria=self.prod.categoria),
            cantidad=1, stock_minimo=5,
        )
        r = self.client.get(reverse('inventario_lista'), {'filtro': 'bajo'})
        self.assertContains(r, "Agotado")
        self.assertNotContains(r, "Refresco")  # Refresco tiene 10 > 5

    def test_lista_filtro_agotado(self):
        crear_inventario(
            producto=crear_producto(nombre="Cero", categoria=self.prod.categoria),
            cantidad=0, stock_minimo=5,
        )
        r = self.client.get(reverse('inventario_lista'), {'filtro': 'agotado'})
        self.assertContains(r, "Cero")
        self.assertNotContains(r, "Refresco")

    def test_lista_busqueda_q(self):
        r = self.client.get(reverse('inventario_lista'), {'q': 'Refre'})
        self.assertContains(r, "Refresco")

    def test_crear_post(self):
        prod2 = crear_producto(nombre="Pan", categoria=self.prod.categoria)
        r = self.client.post(reverse('inventario_crear'), {
            'producto': prod2.pk, 'cantidad': 30, 'stock_minimo': 10,
        })
        self.assertRedirects(r, reverse('inventario_lista'))
        self.assertTrue(Inventario.objects.filter(producto=prod2).exists())

    def test_editar_post(self):
        self.client.post(reverse('inventario_editar', args=[self.inv.pk]), {
            'producto': self.prod.pk, 'cantidad': 500, 'stock_minimo': 10,
        })
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.cantidad, 500)

    def test_eliminar_post(self):
        pk = self.inv.pk
        r = self.client.post(reverse('inventario_eliminar', args=[pk]))
        self.assertRedirects(r, reverse('inventario_lista'))
        self.assertFalse(Inventario.objects.filter(pk=pk).exists())


class VentaViewsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.venta = crear_venta(notas="Venta prueba")

    def test_lista_200(self):
        r = self.client.get(reverse('venta_lista'))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'ventas/lista.html')

    def test_lista_muestra_folio(self):
        r = self.client.get(reverse('venta_lista'))
        self.assertContains(r, self.venta.folio)

    def test_lista_filtro_q(self):
        r = self.client.get(reverse('venta_lista'), {'q': self.venta.folio})
        self.assertContains(r, self.venta.folio)

    def test_lista_filtro_fechas(self):
        hoy = timezone.now().date().isoformat()
        r = self.client.get(reverse('venta_lista'), {
            'desde': hoy, 'hasta': hoy,
        })
        self.assertContains(r, self.venta.folio)

    def test_lista_filtro_fechas_futuro_no_muestra(self):
        futuro = (timezone.now() + timedelta(days=10)).date().isoformat()
        r = self.client.get(reverse('venta_lista'), {'desde': futuro})
        self.assertNotContains(r, self.venta.folio)

    def test_lista_total_filtrado(self):
        self.venta.total = Decimal("50.00")
        self.venta.save()
        r = self.client.get(reverse('venta_lista'))
        self.assertEqual(r.context['total_filtrado'], Decimal("50.00"))

    def test_crear_post(self):
        r = self.client.post(reverse('venta_crear'), {'notas': 'Nueva'})
        nueva = Venta.objects.filter(notas='Nueva').first()
        self.assertIsNotNone(nueva)
        self.assertRedirects(r, reverse('venta_detalle', args=[nueva.pk]))

    def test_detalle_200(self):
        r = self.client.get(reverse('venta_detalle', args=[self.venta.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'ventas/detalle.html')

    def test_detalle_404(self):
        r = self.client.get(reverse('venta_detalle', args=[99999]))
        self.assertEqual(r.status_code, 404)

    def test_agregar_detalle_reduce_stock(self):
        prod = crear_producto(nombre="Producto", precio="10.00",
                              categoria=crear_categoria(nombre="Cat2"))
        inv = crear_inventario(producto=prod, cantidad=20)

        r = self.client.post(reverse('venta_detalle', args=[self.venta.pk]), {
            'producto': prod.pk, 'cantidad': 5, 'precio_unitario': '10.00',
        })
        self.assertRedirects(r, reverse('venta_detalle', args=[self.venta.pk]))

        inv.refresh_from_db()
        self.assertEqual(inv.cantidad, 15)
        self.assertEqual(self.venta.detalles.count(), 1)

    def test_agregar_detalle_sin_stock_falla(self):
        prod = crear_producto(nombre="SinStock", categoria=crear_categoria(nombre="Cat3"))
        crear_inventario(producto=prod, cantidad=2)

        r = self.client.post(
            reverse('venta_detalle', args=[self.venta.pk]),
            {'producto': prod.pk, 'cantidad': 99, 'precio_unitario': '10.00'},
            follow=True,
        )
        self.assertContains(r, 'Stock insuficiente')
        self.assertEqual(self.venta.detalles.count(), 0)

    def test_agregar_detalle_sin_inventario_falla(self):
        prod = crear_producto(nombre="SinInv", categoria=crear_categoria(nombre="Cat4"))
        r = self.client.post(
            reverse('venta_detalle', args=[self.venta.pk]),
            {'producto': prod.pk, 'cantidad': 1, 'precio_unitario': '10.00'},
            follow=True,
        )
        self.assertContains(r, 'no tiene registro de inventario')

    def test_eliminar_detalle_devuelve_stock(self):
        prod = crear_producto(nombre="Dev", categoria=crear_categoria(nombre="Cat5"))
        inv = crear_inventario(producto=prod, cantidad=10)
        detalle = crear_detalle(venta=self.venta, producto=prod, cantidad=3)
        inv.cantidad = 7
        inv.save()

        r = self.client.post(reverse('detalle_eliminar', args=[detalle.pk]))
        self.assertRedirects(r, reverse('venta_detalle', args=[self.venta.pk]))

        inv.refresh_from_db()
        self.assertEqual(inv.cantidad, 10)
        self.assertEqual(self.venta.detalles.count(), 0)

    def test_eliminar_venta_devuelve_todo_stock(self):
        prod = crear_producto(nombre="Todo", categoria=crear_categoria(nombre="Cat6"))
        inv = crear_inventario(producto=prod, cantidad=15)
        crear_detalle(venta=self.venta, producto=prod, cantidad=5)
        inv.cantidad = 10
        inv.save()

        r = self.client.post(reverse('venta_eliminar', args=[self.venta.pk]))
        self.assertRedirects(r, reverse('venta_lista'))

        inv.refresh_from_db()
        self.assertEqual(inv.cantidad, 15)
        self.assertFalse(Venta.objects.filter(pk=self.venta.pk).exists())

    def test_venta_editar_post(self):
        self.client.post(reverse('venta_editar', args=[self.venta.pk]), {
            'notas': 'Editada',
        })
        self.venta.refresh_from_db()
        self.assertEqual(self.venta.notas, 'Editada')


class EscenarioCompleto(TestCase):


    def test_escenario_completo(self):

        cat, prod, inv = crear_escenario_completo()
        self.assertEqual(cat.nombre,"Snacks")
        self.assertEqual(prod.nombre,"Papas")
        self.assertEqual(prod.categoria,cat)
        self.assertEqual(inv.producto,prod)
        self.assertEqual(inv.cantidad,20)
