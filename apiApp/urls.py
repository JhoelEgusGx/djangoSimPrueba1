# apiApp/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductoViewSet, TarifaViewSet, ImagenProductoViewSet, VideoProductoViewSet,
    CategoriaViewSet, MetodoPagoViewSet, PedidoViewSet, PedidoItemViewSet,
    HomePage, chatbot
)

router = DefaultRouter()
router.register(r'productos', ProductoViewSet, basename='producto')
router.register(r'tarifas', TarifaViewSet, basename='tarifa')
router.register(r'imagenes', ImagenProductoViewSet, basename='imagenproducto')
router.register(r'videos', VideoProductoViewSet, basename='videoproducto')
router.register(r'categorias', CategoriaViewSet, basename='categoria')
router.register(r'metodos-pago', MetodoPagoViewSet, basename='metodopago')
router.register(r'pedidos', PedidoViewSet, basename='pedido')
router.register(r'pedido-items', PedidoItemViewSet, basename='pedidoitem')

urlpatterns = [
    path('', HomePage, name='home'),
    path('chatbot/', chatbot, name='chatbot'),
    path('api/', include(router.urls)),
]