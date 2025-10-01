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
        fields = ["id", "url", "public_id"]

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
        fields = ["id", "url", "public_id"]

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
    producto_id = serializers.PrimaryKeyRelatedField(
        queryset=Producto.objects.all(), write_only=True
    )
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = PedidoItem
        fields = [
            'id', 'producto', 'producto_id',
            'cantidad', 'precio_unitario', 'subtotal'
        ]
        read_only_fields = ['precio_unitario', 'subtotal']

    def get_subtotal(self, obj):
        return obj.cantidad * obj.precio_unitario


# ---------------------------✅
class PedidoSerializer(serializers.ModelSerializer):
    items = PedidoItemSerializer(many=True, write_only=True)
    items_detalle = PedidoItemSerializer(many=True, read_only=True, source='items')
    metodo_pago = MetodoPagoSerializer(read_only=True)
    metodo_pago_id = serializers.PrimaryKeyRelatedField(
        queryset=MetodoPago.objects.all(), write_only=True
    )

    class Meta:
        model = Pedido
        fields = [
            'id', 'codigo', 'fecha',
            'nombre', 'apellido', 'dni', 'telefono', 'correo',
            'envio_provincia', 'departamento', 'provincia', 'distrito', 'direccion',
            'total', 'metodo_pago', 'metodo_pago_id',
            'items', 'items_detalle'
        ]
        read_only_fields = ['codigo', 'fecha', 'metodo_pago', 'total']

    def calcular_precio_unitario(self, producto, cantidad):
        tarifas = producto.tarifas.all().order_by("minimo")

        for tarifa in tarifas:
            if tarifa.maximo:
                if tarifa.minimo <= cantidad <= tarifa.maximo:
                    return tarifa.precio_unitario
            else:
                if cantidad >= tarifa.minimo:
                    return tarifa.precio_unitario
        return 0

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        metodo_pago = validated_data.pop('metodo_pago_id')

        total = 0
        pedido_items = []

        # Calculamos primero todo (validaciones + precios)
        for item_data in items_data:
            producto = item_data['producto_id']
            cantidad = item_data['cantidad']

            # Validar stock
            if cantidad > producto.cantidad:
                raise serializers.ValidationError(
                    f"Stock insuficiente para {producto.nombre}. Solo hay {producto.cantidad} disponibles."
                )

            # Calcular precio unitario con tarifa
            precio_unitario = self.calcular_precio_unitario(producto, cantidad)
            if precio_unitario == 0:
                raise serializers.ValidationError(
                    f"No existe tarifa válida para {producto.nombre} con {cantidad} unidades."
                )

            # Acumulamos el total
            total += cantidad * precio_unitario

            pedido_items.append({
                "producto": producto,
                "cantidad": cantidad,
                "precio_unitario": precio_unitario
            })

        # Costo adicional por envío a provincia
        if validated_data.get("envio_provincia"):
            total += 8

        # Ahora sí, creamos el pedido con total ya calculado
        pedido = Pedido.objects.create(
            metodo_pago=metodo_pago,
            total=total,
            **validated_data
        )

        # Guardamos los items y descontamos stock
        for item in pedido_items:
            producto = item["producto"]
            cantidad = item["cantidad"]
            producto.cantidad -= cantidad
            producto.save()

            PedidoItem.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=item["precio_unitario"]
            )

        return pedido
