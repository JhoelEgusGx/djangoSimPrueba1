# apiApp/views/metodo_pago_views.py
from rest_framework import viewsets
from ..models import MetodoPago
from ..serializers import MetodoPagoSerializer


class MetodoPagoViewSet(viewsets.ModelViewSet):
    queryset = MetodoPago.objects.all()
    serializer_class = MetodoPagoSerializer
