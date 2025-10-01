from django.contrib import admin
from .models import (
    Producto, ImagenProducto, VideoProducto, Tarifa, Categoria,
    Pedido, PedidoItem, MetodoPago
)

# ---------------------------- INLINES ----------------------------
class ImagenProductoInline(admin.TabularInline):
    model = ImagenProducto
    extra = 1

class VideoProductoInline(admin.TabularInline):
    model = VideoProducto
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
