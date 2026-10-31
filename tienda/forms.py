from django import forms
from .models import Categoria, Producto, Inventario, Venta, DetalleVenta


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion', 'color']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: Bebidas'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'color': forms.TextInput(attrs={'class': 'form-input', 'type': 'color'}),
        }


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'precio_venta', 'categoria']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.10'}),
            'categoria': forms.Select(attrs={'class': 'form-input'}),
        }


class InventarioForm(forms.ModelForm):
    class Meta:
        model = Inventario
        fields = ['producto', 'cantidad', 'stock_minimo']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-input'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-input'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-input'}),
        }


class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['notas']
        widgets = {
            'notas': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }


class DetalleVentaForm(forms.ModelForm):
    class Meta:
        model = DetalleVenta
        fields = ['producto', 'cantidad', 'precio_unitario']
        widgets = {
            'producto': forms.Select(attrs={
                'class': 'form-input',
                'id': 'id_producto',
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 1,
                'id': 'id_cantidad',
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': '0.01',
                'id': 'id_precio_unitario',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['producto'].queryset = Producto.objects.select_related('categoria')
        # Mostrar el precio en las opciones del select (opcional, pero ayuda)
        self.fields['producto'].label_from_instance = (
            lambda obj: f"{obj.nombre} — ${obj.precio_venta:.2f}"
        )
        self.fields['precio_unitario'].required = True

