from rest_framework import serializers
from .models import (
    Categoria, Producto, Tarifa,
    ImagenProducto, VideoProducto,
    MetodoPago, Pedido, PedidoItem
)

# ---------------------------✅
class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'


# ---------------------------✅
class TarifaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tarifa
        fields = '__all__'


# ---------------------------✅
class ImagenProductoSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    public_id = serializers.SerializerMethodField()
    class Meta:
        model = ImagenProducto
        fields = ["id", "url"]

    def get_url(self, obj):
        if obj.imagen:
            return obj.imagen.url
        return None

    def get_public_id(self, obj):
        return obj.imagen.public_id if obj.imagen else None

# ---------------------------✅
class VideoProductoSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    public_id = serializers.SerializerMethodField()

    class Meta:
        model = VideoProducto
        fields = ["id", "url"]

    def get_url(self, obj):
        if obj.video:
            return obj.video.url
        return None
    
    def get_public_id(self, obj):
        return obj.video.public_id if obj.video else None   


# ---------------------------✅
class ProductoSerializer(serializers.ModelSerializer):
    categorias = CategoriaSerializer(many=True, read_only=True)
    tarifas = TarifaSerializer(many=True, read_only=True)
    imagenes = ImagenProductoSerializer(many=True, read_only=True)
    videos = VideoProductoSerializer(many=True, read_only=True)

    class Meta:
        model = Producto
        fields = '__all__'


# ---------------------------✅
class MetodoPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetodoPago
        fields = '__all__'


# ---------------------------✅
class PedidoItemSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)

    class Meta:
        model = PedidoItem
        fields = ['id', 'producto', 'cantidad', 'precio_unitario', 'subtotal']


# ---------------------------✅
class PedidoSerializer(serializers.ModelSerializer):
    items = PedidoItemSerializer(many=True, read_only=True)
    metodo_pago = MetodoPagoSerializer(read_only=True)

    class Meta:
        model = Pedido
        fields = '__all__'
