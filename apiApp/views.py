from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from utils.email_service import enviar_correo_pedido
from django.shortcuts import get_object_or_404

from django.http import JsonResponse

from .models import (
    Producto, Categoria, Tarifa,
    ImagenProducto, VideoProducto,
    MetodoPago, Pedido, PedidoItem
)
from .serializers import (
    ProductoSerializer, CategoriaSerializer, TarifaSerializer,
    ImagenProductoSerializer, VideoProductoSerializer,
    MetodoPagoSerializer, PedidoSerializer, PedidoItemSerializer
)

# ViewSets
class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre', 'categorias__nombre']

class TarifaViewSet(viewsets.ModelViewSet):
    queryset = Tarifa.objects.all()
    serializer_class = TarifaSerializer

class ImagenProductoViewSet(viewsets.ModelViewSet):
    queryset = ImagenProducto.objects.all()
    serializer_class = ImagenProductoSerializer

class VideoProductoViewSet(viewsets.ModelViewSet):
    queryset = VideoProducto.objects.all()
    serializer_class = VideoProductoSerializer

class MetodoPagoViewSet(viewsets.ModelViewSet):
    queryset = MetodoPago.objects.all()
    serializer_class = MetodoPagoSerializer

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
    


    # 📨 Sobrescribimos create para enviar correo al guardar pedido
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pedido = serializer.save()

        items_html = ""
        total_general = 0

        for item in request.data.get("items", []):
            producto = get_object_or_404(Producto, id=item["producto_id"])
            cantidad = int(item["cantidad"])

            # ✅ Buscar tarifa según cantidad
            tarifa = None
            for t in producto.tarifas.all():
                if (t.minimo is None or cantidad >= t.minimo) and (t.maximo is None or cantidad <= t.maximo):
                    tarifa = t
                    break

            if not tarifa:
                return Response(
                    {"error": f"No hay tarifa válida para {producto.nombre} con cantidad {cantidad}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            precio_unitario = float(tarifa.precio_unitario)
            subtotal = precio_unitario * cantidad
            total_general += subtotal

            # ✅ primera imagen (si existe)
            primera_imagen = producto.imagenes.first()
            imagen_url = primera_imagen.imagen.url if (primera_imagen and primera_imagen.imagen) else "https://via.placeholder.com/50"

            items_html += f"""
            <tr>
                <td style="padding:8px; border:1px solid #ddd; display:flex; align-items:center; gap:8px;">
                    <img src="{imagen_url}" alt="{producto.nombre}" width="50" height="50" style="object-fit:cover; border-radius:4px;">
                    <span>{producto.nombre}</span>
                </td>
                <td style="padding:8px; border:1px solid #ddd; text-align:center;">{cantidad}</td>
                <td style="padding:8px; border:1px solid #ddd; text-align:right;">S/. {precio_unitario:.2f}</td>
                <td style="padding:8px; border:1px solid #ddd; text-align:right;">S/. {subtotal:.2f}</td>
            </tr>
            """

        # 🚚 Envío a provincia
        envio = 0
        if pedido.envio_provincia:
            envio = 8
            total_general += envio

        # 📩 HTML del correo
        mensaje_html = f"""
        <div style="font-family: Arial, sans-serif; max-width:600px; margin:auto; border:1px solid #eee; padding:20px; border-radius:8px;">
            <h2 style="color:#0f172a; text-align:center;">¡Gracias por tu pedido, {pedido.nombre}!</h2>
            <p style="text-align:center;">Tu código de pedido es: <b>{pedido.codigo}</b></p>

            <h3 style="margin-top:30px;">Resumen de pedido</h3>
            <table style="width:100%; border-collapse:collapse; margin-top:10px;">
                <thead>
                    <tr style="background:#f1f5f9;">
                        <th style="padding:8px; border:1px solid #ddd;">Producto</th>
                        <th style="padding:8px; border:1px solid #ddd;">Cantidad</th>
                        <th style="padding:8px; border:1px solid #ddd;">Precio Unit.</th>
                        <th style="padding:8px; border:1px solid #ddd;">Subtotal</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
            </table>

            <div style="margin-top:20px; text-align:right;">
                {"<p>Envío a provincia: <b>S/. 8.00</b></p>" if envio else ""}
                <h3>Total: S/. {total_general:.2f}</h3>
            </div>

            <p style="margin-top:30px; text-align:center; color:#555;">
                Recibimos tu pedido y lo estamos preparando para enviarlo a tu domicilio.<br>
                ¡Gracias por confiar en <b>Gobady Perú</b>!
            </p>
        </div>
        """

        # enviar correo al cliente
        enviar_correo_pedido(
            cliente_email=pedido.correo,
            asunto="Confirmación de tu pedido en Gobady Perú",
            mensaje_html=mensaje_html
        )

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)




class PedidoItemViewSet(viewsets.ModelViewSet):
    queryset = PedidoItem.objects.all()
    serializer_class = PedidoItemSerializer

# Home page view if you want
def HomePage(request):
    return render(request, 'index.html')

