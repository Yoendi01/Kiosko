from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    # Categorías
    path('categorias/', views.categoria_lista, name='categoria_lista'),
    path('categorias/crear/', views.categoria_crear, name='categoria_crear'),
    path('categorias/<int:pk>/editar/', views.categoria_editar, name='categoria_editar'),
    path('categorias/<int:pk>/eliminar/', views.categoria_eliminar, name='categoria_eliminar'),

    # Productos
    path('productos/', views.producto_lista, name='producto_lista'),
    path('productos/crear/', views.producto_crear, name='producto_crear'),
    path('productos/<int:pk>/editar/', views.producto_editar, name='producto_editar'),
    path('productos/<int:pk>/eliminar/', views.producto_eliminar, name='producto_eliminar'),

    # Inventario
    path('inventario/', views.inventario_lista, name='inventario_lista'),
    path('inventario/crear/', views.inventario_crear, name='inventario_crear'),
    path('inventario/<int:pk>/editar/', views.inventario_editar, name='inventario_editar'),
    path('inventario/<int:pk>/eliminar/', views.inventario_eliminar, name='inventario_eliminar'),

    # Ventas
    path('ventas/', views.venta_lista, name='venta_lista'),
    path('ventas/crear/', views.venta_crear, name='venta_crear'),
    path('ventas/<int:pk>/', views.venta_detalle, name='venta_detalle'),
    path('ventas/<int:pk>/editar/', views.venta_editar, name='venta_editar'),
    path('ventas/<int:pk>/eliminar/', views.venta_eliminar, name='venta_eliminar'),
    path('detalles/<int:pk>/eliminar/', views.detalle_eliminar, name='detalle_eliminar'),
    path('api/producto/<int:pk>/precio/', views.api_precio_producto, name='api_precio_producto'),

    # Vista de checkeo
    path("health/", health),
]

