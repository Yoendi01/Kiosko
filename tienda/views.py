from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum, Count, F
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.http import JsonResponse  # <-- agregar arriba con los demás imports
from django.views.decorators.cache import never_cache


from .models import Categoria, Producto, Inventario, Venta, DetalleVenta
from .forms import (CategoriaForm, ProductoForm, InventarioForm,
                    VentaForm, DetalleVentaForm)


# ============ DASHBOARD ============
def dashboard(request):
    hoy = timezone.now().date()
    inicio_semana = hoy - timedelta(days=7)

    total_productos = Producto.objects.count()
    total_categorias = Categoria.objects.count()
    ventas_hoy = Venta.objects.filter(fecha__date=hoy).aggregate(
        total=Sum('total'), cantidad=Count('id')
    )
    ventas_semana = Venta.objects.filter(fecha__date__gte=inicio_semana).aggregate(
        total=Sum('total'), cantidad=Count('id')
    )
    productos_bajo_stock = Inventario.objects.filter(
        cantidad__lte=F('stock_minimo')
    ).select_related('producto')[:5]

    context = {
        'total_productos': total_productos,
        'total_categorias': total_categorias,
        'ventas_hoy_total': ventas_hoy['total'] or 0,
        'ventas_hoy_cantidad': ventas_hoy['cantidad'] or 0,
        'ventas_semana_total': ventas_semana['total'] or 0,
        'ventas_semana_cantidad': ventas_semana['cantidad'] or 0,
        'productos_bajo_stock': productos_bajo_stock,
        'seccion': 'dashboard',
    }
    return render(request, 'dashboard.html', context)


# ============ CATEGORIAS ============
def categoria_lista(request):
    q = request.GET.get('q', '')
    categorias = Categoria.objects.annotate(num_productos=Count('productos'))
    if q:
        categorias = categorias.filter(
            Q(nombre__icontains=q) | Q(descripcion__icontains=q)
        )
    return render(request, 'categorias/lista.html', {
        'categorias': categorias, 'q': q, 'seccion': 'categorias'
    })


def categoria_crear(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría creada exitosamente.')
            return redirect('categoria_lista')
    else:
        form = CategoriaForm()
    return render(request, 'categorias/form.html', {
        'form': form, 'accion': 'Crear', 'seccion': 'categorias'
    })


def categoria_editar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría actualizada.')
            return redirect('categoria_lista')
    else:
        form = CategoriaForm(instance=categoria)
    return render(request, 'categorias/form.html', {
        'form': form, 'accion': 'Editar', 'seccion': 'categorias'
    })


def categoria_eliminar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        categoria.delete()
        messages.success(request, 'Categoría eliminada.')
        return redirect('categoria_lista')
    return render(request, 'categorias/eliminar.html', {
        'categoria': categoria, 'seccion': 'categorias'
    })


# ============ PRODUCTOS ============
def producto_lista(request):
    q = request.GET.get('q', '')
    cat_id = request.GET.get('categoria', '')

    productos = Producto.objects.select_related('categoria')
    if q:
        productos = productos.filter(
            Q(nombre__icontains=q) | Q(categoria__nombre__icontains=q)
        )
    if cat_id:
        productos = productos.filter(categoria_id=cat_id)

    return render(request, 'productos/lista.html', {
        'productos': productos,
        'categorias': Categoria.objects.all(),
        'q': q,
        'cat_id': cat_id,
        'seccion': 'productos',
    })


def producto_crear(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto creado.')
            return redirect('producto_lista')
    else:
        form = ProductoForm()
    return render(request, 'productos/form.html', {
        'form': form, 'accion': 'Crear', 'seccion': 'productos'
    })


def producto_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado.')
            return redirect('producto_lista')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'productos/form.html', {
        'form': form, 'accion': 'Editar', 'seccion': 'productos'
    })


def producto_eliminar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Producto eliminado.')
        return redirect('producto_lista')
    return render(request, 'productos/eliminar.html', {
        'producto': producto, 'seccion': 'productos'
    })


# ============ INVENTARIO ============
def inventario_lista(request):
    q = request.GET.get('q', '')
    filtro = request.GET.get('filtro', '')

    inventarios = Inventario.objects.select_related('producto', 'producto__categoria')
    if q:
        inventarios = inventarios.filter(producto__nombre__icontains=q)
    if filtro == 'bajo':
        inventarios = inventarios.filter(cantidad__lte=F('stock_minimo'))
    elif filtro == 'agotado':
        inventarios = inventarios.filter(cantidad=0)

    return render(request, 'inventario/lista.html', {
        'inventarios': inventarios, 'q': q, 'filtro': filtro,
        'seccion': 'inventario'
    })


def inventario_crear(request):
    if request.method == 'POST':
        form = InventarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registro de inventario creado.')
            return redirect('inventario_lista')
    else:
        form = InventarioForm()
    return render(request, 'inventario/form.html', {
        'form': form, 'accion': 'Crear', 'seccion': 'inventario'
    })


def inventario_editar(request, pk):
    inventario = get_object_or_404(Inventario, pk=pk)
    if request.method == 'POST':
        form = InventarioForm(request.POST, instance=inventario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inventario actualizado.')
            return redirect('inventario_lista')
    else:
        form = InventarioForm(instance=inventario)
    return render(request, 'inventario/form.html', {
        'form': form, 'accion': 'Editar', 'seccion': 'inventario'
    })


def inventario_eliminar(request, pk):
    inventario = get_object_or_404(Inventario, pk=pk)
    if request.method == 'POST':
        inventario.delete()
        messages.success(request, 'Registro de inventario eliminado.')
        return redirect('inventario_lista')
    return render(request, 'inventario/eliminar.html', {
        'inventario': inventario, 'seccion': 'inventario'
    })


# ============ VENTAS ============
def venta_lista(request):
    q = request.GET.get('q', '')
    desde = request.GET.get('desde', '')
    hasta = request.GET.get('hasta', '')

    ventas = Venta.objects.annotate(num_items=Count('detalles'))
    if q:
        ventas = ventas.filter(
            Q(folio__icontains=q) | Q(notas__icontains=q)
        )
    if desde:
        ventas = ventas.filter(fecha__date__gte=desde)
    if hasta:
        ventas = ventas.filter(fecha__date__lte=hasta)

    total_filtrado = ventas.aggregate(total=Sum('total'))['total'] or 0

    return render(request, 'ventas/lista.html', {
        'ventas': ventas, 'q': q, 'desde': desde, 'hasta': hasta,
        'total_filtrado': total_filtrado, 'seccion': 'ventas'
    })


def venta_crear(request):
    if request.method == 'POST':
        form = VentaForm(request.POST)
        if form.is_valid():
            venta = form.save()
            messages.success(request, f'Venta {venta.folio} creada. Ahora agrega productos.')
            return redirect('venta_detalle', pk=venta.pk)
    else:
        form = VentaForm()
    return render(request, 'ventas/form.html', {
        'form': form, 'accion': 'Crear', 'seccion': 'ventas'
    })


def venta_editar(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        form = VentaForm(request.POST, instance=venta)
        if form.is_valid():
            form.save()
            messages.success(request, 'Venta actualizada.')
            return redirect('venta_detalle', pk=venta.pk)
    else:
        form = VentaForm(instance=venta)
    return render(request, 'ventas/form.html', {
        'form': form, 'accion': 'Editar', 'venta': venta, 'seccion': 'ventas'
    })


def venta_detalle(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    detalles = venta.detalles.select_related('producto')
    form = DetalleVentaForm()

    if request.method == 'POST':
        form = DetalleVentaForm(request.POST)
        if form.is_valid():
            detalle = form.save(commit=False)
            detalle.venta = venta

            # Verificar y descontar del inventario
            inventario = Inventario.objects.filter(producto=detalle.producto).first()
            if inventario:
                if inventario.cantidad < detalle.cantidad:
                    messages.error(request,
                        f'Stock insuficiente. Disponible: {inventario.cantidad}')
                    return redirect('venta_detalle', pk=venta.pk)
                inventario.cantidad -= detalle.cantidad
                inventario.save()
            else:
                messages.error(request, 'Este producto no tiene registro de inventario.')
                return redirect('venta_detalle', pk=venta.pk)

            detalle.save()
            venta.recalcular_total()
            messages.success(request, 'Producto agregado a la venta.')
            return redirect('venta_detalle', pk=venta.pk)

    return render(request, 'ventas/detalle.html', {
        'venta': venta, 'detalles': detalles, 'form': form,
        'seccion': 'ventas'
    })


def detalle_eliminar(request, pk):
    detalle = get_object_or_404(DetalleVenta, pk=pk)
    venta = detalle.venta

    if request.method == 'POST':
        # Devolver stock
        inventario = Inventario.objects.filter(producto=detalle.producto).first()
        if inventario:
            inventario.cantidad += detalle.cantidad
            inventario.save()
        detalle.delete()
        venta.recalcular_total()
        messages.success(request, 'Producto removido de la venta.')
        return redirect('venta_detalle', pk=venta.pk)

    return render(request, 'ventas/detalle_eliminar.html', {
        'detalle': detalle, 'seccion': 'ventas'
    })


def venta_eliminar(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        # Devolver stock de todos los detalles
        for detalle in venta.detalles.all():
            inventario = Inventario.objects.filter(producto=detalle.producto).first()
            if inventario:
                inventario.cantidad += detalle.cantidad
                inventario.save()
        venta.delete()
        messages.success(request, 'Venta eliminada y stock restaurado.')
        return redirect('venta_lista')
    return render(request, 'ventas/eliminar.html', {
        'venta': venta, 'seccion': 'ventas'
    })

# ============ API: PRECIO DE PRODUCTO ============
@never_cache
def api_precio_producto(request, pk):
    """Devuelve el precio de venta del producto y su stock actual."""
    try:
        print(f"Recibido: {pk}")
        producto = Producto.objects.get(pk=pk)
        inventario = Inventario.objects.filter(producto=producto).first()
        return JsonResponse({
            'ok': True,
            'id': producto.pk,
            'nombre': producto.nombre,
            'precio': float(producto.precio_venta),
            'stock': inventario.cantidad if inventario else 0,
        })
    except Producto.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Producto no encontrado'}, status=404)