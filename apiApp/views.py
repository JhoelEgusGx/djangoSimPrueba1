# apiApp/views.py
"""
Archivo principal de vistas.
Este archivo centraliza las vistas divididas en submódulos (views/),
manteniendo compatibilidad con Django y un punto único de importación.
"""

# Importa todo desde las vistas organizadas
from .views.home_view import *
from .views.categoria_views import *
from .views.producto_views import *
from .views.metodo_pago_views import *
from .views.pedido_views import *
