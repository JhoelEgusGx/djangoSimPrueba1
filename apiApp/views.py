from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response

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

class PedidoItemViewSet(viewsets.ModelViewSet):
    queryset = PedidoItem.objects.all()
    serializer_class = PedidoItemSerializer

# Home page view if you want
def HomePage(request):
    return render(request, 'index.html')
