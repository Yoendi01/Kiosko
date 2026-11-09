from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=7, default='#6366f1',
                             help_text='Color en formato HEX (ej: #6366f1)')
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=150)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2,
                                        validators=[MinValueValidator(0)])
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE,
                                  related_name='productos')
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    @property
    def stock(self):
        inventario = self.inventarios.first()
        return inventario.cantidad if inventario else 0


class Inventario(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE,
                                 related_name='inventarios')
    cantidad = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=5)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Inventario'
        verbose_name_plural = 'Inventario'
        ordering = ['producto__nombre']

    def __str__(self):
        return f"{self.producto.nombre} - {self.cantidad} unidades"

    @property
    def bajo_stock(self):
        return self.cantidad <= self.stock_minimo


class Venta(models.Model):
    folio = models.CharField(max_length=20, unique=True, editable=False)
    fecha = models.DateTimeField(default=timezone.now)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notas = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-fecha']

    def __str__(self):
        return f"Venta {self.folio} - ${self.total}"

    def save(self, *args, **kwargs):
        if not self.folio:
            ultima = Venta.objects.order_by('-id').first()
            numero = (ultima.id + 1) if ultima else 1
            self.folio = f"V{numero:06d}"
        super().save(*args, **kwargs)

    def recalcular_total(self):
        total = sum(d.subtotal for d in self.detalles.all())
        self.total = total
        self.save(update_fields=['total'])


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE,
                              related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Detalle de Venta'
        verbose_name_plural = 'Detalles de Venta'

    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad}"

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

