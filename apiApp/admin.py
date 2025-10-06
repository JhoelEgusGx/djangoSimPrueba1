from django.contrib import admin
from django import forms
from .models import (
    Producto, ImagenProducto, VideoProducto, Tarifa, Categoria,
    Pedido, PedidoItem, MetodoPago
)


class ImagenProductoForm(forms.ModelForm):
    existing_url = forms.URLField(
        required=False,
        label="Usar URL existente",
        help_text="Pega aquí la URL de Cloudinary si ya tienes la imagen subida"
    )

    class Meta:
        model = ImagenProducto
        fields = ["imagen", "existing_url"]  # mostramos ambos

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get("existing_url"):
            # 👇 si pegaste URL, lo guarda en lugar de subir
            instance.imagen = self.cleaned_data["existing_url"]
        if commit:
            instance.save()
        return instance


class VideoProductoForm(forms.ModelForm):
    existing_url = forms.URLField(
        required=False,
        label="Usar URL existente",
        help_text="Pega aquí la URL de Cloudinary si ya tienes el video subido"
    )

    class Meta:
        model = VideoProducto
        fields = ["video", "existing_url"]

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get("existing_url"):
            instance.video = self.cleaned_data["existing_url"]
        if commit:
            instance.save()
        return instance


# ---------------------------- INLINES ----------------------------
class ImagenProductoInline(admin.TabularInline):
    model = ImagenProducto
    form = ImagenProductoForm   # 👈 aquí usamos el form
    extra = 1


class VideoProductoInline(admin.TabularInline):
    model = VideoProducto
    form = VideoProductoForm
    extra = 1


class TarifaInline(admin.TabularInline):
    model = Tarifa
    extra = 1

# ---------------------------- PRODUCTO ----------------------------


class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_ingreso', 'cantidad')
    inlines = [ImagenProductoInline, VideoProductoInline, TarifaInline]
    filter_horizontal = ('categorias',)


admin.site.register(Producto, ProductoAdmin)

# ---------------------------- PEDIDO ----------------------------


class PedidoItemInline(admin.TabularInline):
    model = PedidoItem
    extra = 0
    fields = ("producto", "cantidad", "precio_unitario", "subtotal")
    readonly_fields = ("subtotal",)

    def subtotal(self, obj):
        if obj.id:  # si ya existe en BD
            return obj.cantidad * obj.precio_unitario
        return "-"
    subtotal.short_description = "Subtotal"


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo", "fecha", "nombre", "apellido", "dni", "telefono", "correo",
        "envio_provincia", "departamento", "provincia", "distrito", "direccion",
        "total", "metodo_pago", "resumen_items"
    )
    list_filter = ("envio_provincia", "metodo_pago", "fecha")
    search_fields = ("codigo", "nombre", "apellido", "correo", "telefono")
    ordering = ("-fecha",)
    inlines = [PedidoItemInline]

    def resumen_items(self, obj):
        return ", ".join([f"{item.cantidad}x {item.producto.nombre}" for item in obj.items.all()])
    resumen_items.short_description = "Productos"


# ---------------------------- OTROS ----------------------------
admin.site.register(Categoria)
admin.site.register(MetodoPago)
