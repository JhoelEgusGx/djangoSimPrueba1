from .auth_views import login_view, dashboard_home
from .cloudinary_views import cloudinary_imagenes_api, cloudinary_imagenes_delete
from .producto_views import (
    producto_list, producto_list_api,
    producto_create, producto_update, producto_delete,
)
from .categoria_views import (
    categoria_list, categoria_create, categoria_update, categoria_delete,
)
from .pedido_views import (
    pedido_list, pedido_list_api, pedido_detail, pedido_delete,
)
from .pago_views import (
    pago_list, pago_create, pago_update, pago_delete,
)
