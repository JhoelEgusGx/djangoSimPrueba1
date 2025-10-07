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


class TarifaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tarifa
        fields = '__all__'


class ImagenProductoSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    public_id = serializers.SerializerMethodField()

    # 🔥 Nuevo: campo para pasar URL existente de Cloudinary
    existing_url = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = ImagenProducto
        fields = ["id", "url", "public_id", "existing_url", "producto"]

    def get_url(self, obj):
        return obj.imagen.url if obj.imagen else None

    def get_public_id(self, obj):
        return obj.imagen.public_id if obj.imagen else None

    def create(self, validated_data):
        existing_url = validated_data.pop("existing_url", None)
        if existing_url:
            return ImagenProducto.objects.create(
                producto=validated_data["producto"],
                imagen=existing_url
            )
        return super().create(validated_data)


class VideoProductoSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    public_id = serializers.SerializerMethodField()
    existing_url = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = VideoProducto
        fields = ["id", "url", "public_id", "existing_url", "producto"]

    def get_url(self, obj):
        return obj.video.url if obj.video else None

    def get_public_id(self, obj):
        return obj.video.public_id if obj.video else None

    def create(self, validated_data):
        existing_url = validated_data.pop("existing_url", None)
        if existing_url:
            return VideoProducto.objects.create(
                producto=validated_data["producto"],
                video=existing_url
            )
        return super().create(validated_data)


class ProductoSerializer(serializers.ModelSerializer):
    categorias = CategoriaSerializer(many=True, read_only=True)
    tarifas = TarifaSerializer(many=True, read_only=True)
    imagenes = ImagenProductoSerializer(many=True, read_only=True)
    videos = VideoProductoSerializer(many=True, read_only=True)

    class Meta:
        model = Producto
        fields = '__all__'


# serializers.py
class MetodoPagoSerializer(serializers.ModelSerializer):
    qr_imagen_url = serializers.SerializerMethodField()
    qr_imagen_id = serializers.SerializerMethodField()

    # 🔥 Campo adicional para pegar URL de Cloudinary
    existing_url = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = MetodoPago
        fields = [
            "id", "nombre", "descripcion",
            "qr_imagen", "existing_url",  # 👈 importante
            "qr_imagen_url", "qr_imagen_id",
            "numero_cuenta"
        ]
        extra_kwargs = {
            "qr_imagen": {"write_only": True}  # no mostrar el binario en respuesta
        }

    def get_qr_imagen_url(self, obj):
        return obj.qr_imagen.url if hasattr(obj.qr_imagen, "url") else obj.qr_imagen

    def get_qr_imagen_id(self, obj):
        return obj.qr_imagen.public_id if hasattr(obj.qr_imagen, "public_id") else None

    def create(self, validated_data):
        existing_url = validated_data.pop("existing_url", None)
        if existing_url:
            return MetodoPago.objects.create(
                qr_imagen=existing_url,
                **validated_data
            )
        return super().create(validated_data)

    def update(self, instance, validated_data):
        existing_url = validated_data.pop("existing_url", None)
        if existing_url:
            instance.qr_imagen = existing_url
        return super().update(instance, validated_data)



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


class PedidoSerializer(serializers.ModelSerializer):
    # write-only items input, read-only detailed items in response
    items = PedidoItemSerializer(many=True, write_only=True)
    items_detalle = PedidoItemSerializer(
        many=True, read_only=True, source='items')
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
            if tarifa.maximo is not None:
                if tarifa.minimo <= cantidad <= tarifa.maximo:
                    return tarifa.precio_unitario
            else:
                if cantidad >= tarifa.minimo:
                    return tarifa.precio_unitario
        return 0

    def validate(self, data):
        items = data.get('items') or []
        if not items:
            raise serializers.ValidationError(
                "El pedido debe tener al menos un producto.")
        # validar DNI y telefono si deseas
        dni = data.get('dni', '')
        telefono = data.get('telefono', '')
        if dni and len(dni) != 8:
            raise serializers.ValidationError("El DNI debe tener 8 dígitos.")
        if telefono and len(telefono) != 9:
            raise serializers.ValidationError(
                "El teléfono debe tener 9 dígitos.")
        return data

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        metodo_pago = validated_data.pop('metodo_pago_id')

        # Primero validar y calcular total sin tocar DB (doble validación)
        total = 0
        prepared_items = []
        for item in items_data:
            producto = item['producto_id']
            cantidad = item['cantidad']

            if cantidad <= 0:
                raise serializers.ValidationError(
                    f"Cantidad inválida para {producto.nombre}.")

            if cantidad > producto.cantidad:
                raise serializers.ValidationError(
                    f"Stock insuficiente para {producto.nombre}. Solo hay {producto.cantidad} disponibles."
                )

            precio_unitario = self.calcular_precio_unitario(producto, cantidad)
            if precio_unitario == 0:
                raise serializers.ValidationError(
                    f"No existe tarifa válida para {producto.nombre} con {cantidad} unidades."
                )

            subtotal = cantidad * precio_unitario
            total += subtotal

            prepared_items.append({
                "producto": producto,
                "cantidad": cantidad,
                "precio_unitario": precio_unitario,
                "subtotal": subtotal
            })

        # envío provincia
        if validated_data.get('envio_provincia'):
            total += 8

        # Crear pedido con total ya calculado
        pedido = Pedido.objects.create(
            metodo_pago=metodo_pago,
            total=total,
            **validated_data
        )

        # Guardar items y descontar stock (persistir cambios)
        for it in prepared_items:
            producto = it['producto']
            cantidad = it['cantidad']
            precio_unitario = it['precio_unitario']

            # descontar stock
            producto.cantidad -= cantidad
            producto.save()

            # crear item
            PedidoItem.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio_unitario
            )

        return pedido
