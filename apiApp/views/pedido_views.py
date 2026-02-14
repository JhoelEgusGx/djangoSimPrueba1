# apiApp/views/pedido_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from ..utils.email_service import enviar_correo_pedido

from ..models import Pedido, PedidoItem, Producto
from ..serializers import PedidoSerializer, PedidoItemSerializer

from ..services.pedido_service import (
    procesar_items_y_calcular_totales,
    generar_mensaje_html,
    ENVIO_PROVINCIA_COST
)


class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all().order_by('-fecha')
    serializer_class = PedidoSerializer

    @action(detail=False, methods=['get'], url_path='codigo/(?P<codigo>[^/.]+)')
    def buscar_por_codigo(self, request, codigo=None):
        try:
            pedido = Pedido.objects.get(codigo=codigo)
            serializer = self.get_serializer(pedido)
            return Response(serializer.data)
        except Pedido.DoesNotExist:
            return Response({"error": "Pedido no encontrado"}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request, *args, **kwargs):
        # Validar y guardar el pedido (igual que antes)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pedido = serializer.save()

        try:
            # procesar items y totales usando el servicio
            items_data = request.data.get("items", [])
            items_html, total_general = procesar_items_y_calcular_totales(items_data)

            # envío a provincia
            envio = 0
            if pedido.envio_provincia:
                envio = ENVIO_PROVINCIA_COST
                total_general += envio

            # generar HTML del correo
            mensaje_html = generar_mensaje_html(pedido, items_html, total_general, envio)

            # enviar correo al cliente (tu utils/email_service.py)
            enviar_correo_pedido(
                cliente_email=pedido.correo,
                asunto="Confirmación de tu pedido en Gobady Perú",
                mensaje_html=mensaje_html
            )

        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error al procesar pedido: {e}")
            return Response({"error": "Ocurrió un error al procesar el pedido."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class PedidoItemViewSet(viewsets.ModelViewSet):
    queryset = PedidoItem.objects.all()
    serializer_class = PedidoItemSerializer
