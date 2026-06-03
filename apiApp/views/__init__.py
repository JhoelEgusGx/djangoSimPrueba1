from .home_view import chatbot
from .categoria_views import CategoriaViewSet
from .producto_views import (
    ProductoViewSet, TarifaViewSet,
    ImagenProductoViewSet, VideoProductoViewSet
)
from .metodo_pago_views import MetodoPagoViewSet
from .pedido_views import PedidoViewSet, PedidoItemViewSet
from .admin import (
    login_view,
    cloudinary_imagenes_api,
    cloudinary_imagenes_delete,
    dashboard_home,
    producto_list, producto_list_api, producto_create, producto_update, producto_delete,
    categoria_list, categoria_create, categoria_update, categoria_delete,
    pedido_list, pedido_list_api, pedido_detail, pedido_delete,
    pago_list, pago_create, pago_update, pago_delete,
)
