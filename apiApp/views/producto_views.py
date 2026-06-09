# apiApp/views/producto_views.py
from rest_framework import viewsets, filters

from ..models import Producto, Tarifa, ImagenProducto, VideoProducto
from ..serializers import (
    ProductoSerializer, TarifaSerializer,
    ImagenProductoSerializer, VideoProductoSerializer
)


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all().order_by('-fecha_ingreso', '-id')  # Ordenar por fecha de ingreso
    serializer_class = ProductoSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre', 'descripcion', 'categorias__nombre']


class TarifaViewSet(viewsets.ModelViewSet):
    queryset = Tarifa.objects.all()
    serializer_class = TarifaSerializer


class ImagenProductoViewSet(viewsets.ModelViewSet):
    queryset = ImagenProducto.objects.all()
    serializer_class = ImagenProductoSerializer


class VideoProductoViewSet(viewsets.ModelViewSet):
    queryset = VideoProducto.objects.all()
    serializer_class = VideoProductoSerializer
