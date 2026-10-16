# apiApp/views/pedido_views.py
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..utils.email_service import enviar_correo_pedido

from ..models import Pedido, PedidoItem
from ..serializers import PedidoSerializer, PedidoItemSerializer

from ..services.pedido_service import (
    generar_items_html,
    generar_mensaje_html,
    ENVIO_PROVINCIA_COST
)


class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all().order_by('-fecha')
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='codigo/(?P<codigo>[^/.]+)')
    def buscar_por_codigo(self, request, codigo=None):
        try:
            pedido = Pedido.objects.get(codigo=codigo)
            serializer = self.get_serializer(pedido)
            return Response(serializer.data)
        except Pedido.DoesNotExist:
            return Response({"error": "Pedido no encontrado"}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request, *args, **kwargs):
        # El serializer valida, crea el pedido + items y descuenta stock
        # dentro de su propia transacción. El total queda congelado en el pedido.
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pedido = serializer.save()

        # El correo se construye con los items ya guardados (sin recalcular).
        envio = ENVIO_PROVINCIA_COST if pedido.envio_provincia else 0
        items_html = generar_items_html(pedido)
        mensaje_html = generar_mensaje_html(pedido, items_html, pedido.total, envio)

        # Enviar el correo solo después de confirmar la transacción.
        # Si falla el correo, el pedido ya quedó guardado y NO se devuelve error.
        transaction.on_commit(
            lambda: enviar_correo_pedido(
                cliente_email=pedido.correo,
                asunto="Confirmación de tu pedido en Gobady Perú",
                mensaje_html=mensaje_html,
            )
        )

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class PedidoItemViewSet(viewsets.ModelViewSet):
    queryset = PedidoItem.objects.all()
    serializer_class = PedidoItemSerializer
    permission_classes = [IsAuthenticated]
