from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.contrib.auth import views as auth_views

from .views import (
    ProductoViewSet, TarifaViewSet, ImagenProductoViewSet, VideoProductoViewSet,
    CategoriaViewSet, MetodoPagoViewSet, PedidoViewSet, PedidoItemViewSet,
    chatbot,
    login_view,
    cloudinary_imagenes_api,
    cloudinary_imagenes_delete,
    dashboard_home,
    producto_list, producto_list_api, producto_create, producto_update, producto_delete,
    categoria_list, categoria_create, categoria_update, categoria_delete,
    pedido_list, pedido_list_api, pedido_detail, pedido_delete,
    pago_list, pago_create, pago_update, pago_delete,
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
    path('chatbot/', chatbot, name='chatbot'),
    path('api/', include(router.urls)),

    # Auth
    path('login/', login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Dashboard
    path('dashboard/', dashboard_home, name='dashboard_home'),
    path('dashboard/cloudinary-imagenes/', cloudinary_imagenes_api, name='cloudinary_imagenes_api'),
    path('dashboard/cloudinary-imagenes/eliminar/', cloudinary_imagenes_delete, name='cloudinary_imagenes_delete'),

    path('dashboard/productos/', producto_list, name='producto_list'),
    path('dashboard/productos/api/', producto_list_api, name='producto_list_api'),
    path('dashboard/productos/nuevo/', producto_create, name='producto_create'),
    path('dashboard/productos/<int:pk>/editar/', producto_update, name='producto_update'),
    path('dashboard/productos/<int:pk>/eliminar/', producto_delete, name='producto_delete'),

    path('dashboard/categorias/', categoria_list, name='categoria_list'),
    path('dashboard/categorias/nueva/', categoria_create, name='categoria_create'),
    path('dashboard/categorias/<int:pk>/editar/', categoria_update, name='categoria_update'),
    path('dashboard/categorias/<int:pk>/eliminar/', categoria_delete, name='categoria_delete'),

    path('dashboard/pedidos/', pedido_list, name='pedido_list'),
    path('dashboard/pedidos/api/', pedido_list_api, name='pedido_list_api'),
    path('dashboard/pedidos/<int:pk>/', pedido_detail, name='pedido_detail'),
    path('dashboard/pedidos/<int:pk>/eliminar/', pedido_delete, name='pedido_delete'),

    path('dashboard/pagos/', pago_list, name='pago_list'),
    path('dashboard/pagos/nuevo/', pago_create, name='pago_create'),
    path('dashboard/pagos/<int:pk>/editar/', pago_update, name='pago_update'),
    path('dashboard/pagos/<int:pk>/eliminar/', pago_delete, name='pago_delete'),


]
