from django.contrib import admin
from .models import Categoria, Producto, Inventario, Venta, DetalleVenta

admin.site.site_header = "Kiosko Administración"
admin.site.site_title = "Kiosko"
admin.site.index_title = "Panel de Control"

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'color')
    search_fields = ('nombre',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio_venta', 'categoria')
    list_filter = ('categoria',)
    search_fields = ('nombre',)

@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ('producto', 'cantidad', 'stock_minimo', 'bajo_stock')
    search_fields = ('producto__nombre',)

class DetalleInline(admin.TabularInline):
    model = DetalleVenta
    extra = 1

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('folio', 'fecha', 'total')
    search_fields = ('folio',)
    inlines = [DetalleInline]
