from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from ..models import Proveedor
from ..serializers import ProveedorSerializer


class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all().order_by('nombre')
    serializer_class = ProveedorSerializer
    filter_backends = [SearchFilter]
    search_fields = ['^nombre']
