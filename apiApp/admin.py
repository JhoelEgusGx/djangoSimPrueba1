from django.contrib import admin
from . import models
# Register your models here.
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
from django.contrib import admin
from .models import Producto, ImagenProducto, VideoProducto, Tarifa, Categoria

# ----------------------------
class ImagenProductoInline(admin.TabularInline):
    model = ImagenProducto
    extra = 1  # cuántos campos vacíos se muestran por defecto

class VideoProductoInline(admin.TabularInline):
    model = VideoProducto
    extra = 1

class TarifaInline(admin.TabularInline):
    model = Tarifa
    extra = 1



class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_ingreso', 'cantidad')
    inlines = [ImagenProductoInline, VideoProductoInline, TarifaInline]
    filter_horizontal = ('categorias',)  # si quieres una interfaz bonita para ManyToMany

admin.site.register(Producto, ProductoAdmin)



#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@



admin.site.register(models.Categoria)
admin.site.register(models.Pedido)
admin.site.register(models.MetodoPago)
admin.site.register(models.VideoProducto)
admin.site.register(models.ImagenProducto)
admin.site.register(models.Tarifa)
admin.site.register(models.PedidoItem)


