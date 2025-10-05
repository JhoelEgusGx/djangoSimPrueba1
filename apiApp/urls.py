from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductoViewSet, CategoriaViewSet, TarifaViewSet,
    ImagenProductoViewSet, VideoProductoViewSet,
    MetodoPagoViewSet, PedidoViewSet, PedidoItemViewSet, HomePage
)
from . import views

router = DefaultRouter()
router.register(r'productos', ProductoViewSet)
router.register(r'categorias', CategoriaViewSet)
router.register(r'tarifas', TarifaViewSet)
router.register(r'imagenes', ImagenProductoViewSet)
router.register(r'videos', VideoProductoViewSet)
router.register(r'metodos-pago', MetodoPagoViewSet)
router.register(r'pedidos', PedidoViewSet)
router.register(r'items-pedido', PedidoItemViewSet)

urlpatterns = [
    path('', views.HomePage, name='home'),
    path('api/', include(router.urls)),
    path('productos/<int:id>/cantidad/', views.producto_cantidad, name='producto_cantidad'),
]
