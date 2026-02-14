from rest_framework import serializers
from ..models import Pedido, PedidoItem, Producto, MetodoPago
from .producto_serializers import ProductoSerializer
from .metodo_pago_serializers import MetodoPagoSerializer


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
            raise serializers.ValidationError("El pedido debe tener al menos un producto.")

        dni = data.get('dni', '')
        telefono = data.get('telefono', '')
        if dni and len(dni) != 8:
            raise serializers.ValidationError("El DNI debe tener 8 dígitos.")
        if telefono and len(telefono) != 9:
            raise serializers.ValidationError("El teléfono debe tener 9 dígitos.")
        return data

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        metodo_pago = validated_data.pop('metodo_pago_id')

        total = 0
        prepared_items = []
        for item in items_data:
            producto = item['producto_id']
            cantidad = item['cantidad']

            if cantidad <= 0:
                raise serializers.ValidationError(
                    f"Cantidad inválida para {producto.nombre}."
                )

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

        if validated_data.get('envio_provincia'):
            total += 8

        pedido = Pedido.objects.create(
            metodo_pago=metodo_pago,
            total=total,
            **validated_data
        )

        for it in prepared_items:
            producto = it['producto']
            cantidad = it['cantidad']
            precio_unitario = it['precio_unitario']

            producto.cantidad -= cantidad
            producto.save()

            PedidoItem.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio_unitario
            )

        return pedido
