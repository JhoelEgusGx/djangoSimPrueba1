"""
Servicio para procesar la lógica de creación de pedidos:
- calcular totales
- generar items_html
- generar mensaje_html del correo
Se lanza ValueError si no hay tarifa válida para un producto.
"""

from django.shortcuts import get_object_or_404
from ..models import Producto

ENVIO_PROVINCIA_COST = 8  # constante tomada de tu lógica original


def procesar_items_y_calcular_totales(items_data):
    """
    items_data: lista de dicts con 'producto_id' y 'cantidad' como en el request.
    Retorna: (items_html, total_general)
    Lanza ValueError si alguna regla no se cumple (no hay tarifa válida).
    """
    items_html = ""
    total_general = 0

    for item in items_data:
        producto = get_object_or_404(Producto, id=item["producto_id"])
        cantidad = int(item["cantidad"])

        # Buscar tarifa según cantidad (misma lógica que tenías)
        tarifa = None
        for t in producto.tarifas.all():
            if (t.minimo is None or cantidad >= t.minimo) and (t.maximo is None or cantidad <= t.maximo):
                tarifa = t
                break

        if not tarifa:
            raise ValueError(f"No hay tarifa válida para {producto.nombre} con cantidad {cantidad}")

        precio_unitario = float(tarifa.precio_unitario)
        subtotal = precio_unitario * cantidad
        total_general += subtotal

        primera_imagen = producto.imagenes.first()
        imagen_url = primera_imagen.imagen.url if (primera_imagen and primera_imagen.imagen) else "https://via.placeholder.com/50"

        items_html += f"""
            <tr>
                <td style="padding:8px; border:1px solid #ddd; display:flex; align-items:center; gap:8px;">
                    <img src="{imagen_url}" alt="{producto.nombre}" width="50" height="50" style="object-fit:cover; border-radius:4px;">
                    <span>{producto.nombre}</span>
                </td>
                <td style="padding:8px; border:1px solid #ddd; text-align:center;">{cantidad}</td>
                <td style="padding:8px; border:1px solid #ddd; text-align:right;">S/. {precio_unitario:.2f}</td>
                <td style="padding:8px; border:1px solid #ddd; text-align:right;">S/. {subtotal:.2f}</td>
            </tr>
        """

    return items_html, total_general


def generar_mensaje_html(pedido, items_html, total_general, envio=0):
    """
    Genera el HTML del correo usando la estructura que tenías.
    Retorna string HTML.
    """
    envio_html = "<p>Envío a provincia: <b>S/. 8.00</b></p>" if envio else ""
    mensaje_html = f"""
    <div style="font-family: Arial, sans-serif; max-width:600px; margin:auto; border:1px solid #eee; padding:20px; border-radius:8px;">
        <h2 style="color:#0f172a; text-align:center;">¡Gracias por tu pedido, {pedido.nombre}!</h2>
        <p style="text-align:center;">Tu código de pedido es: <b>{pedido.codigo}</b></p>

        <h3 style="margin-top:30px;">Resumen de pedido</h3>
        <table style="width:100%; border-collapse:collapse; margin-top:10px;">
            <thead>
                <tr style="background:#f1f5f9;">
                    <th style="padding:8px; border:1px solid #ddd;">Producto</th>
                    <th style="padding:8px; border:1px solid #ddd;">Cantidad</th>
                    <th style="padding:8px; border:1px solid #ddd;">Precio Unit.</th>
                    <th style="padding:8px; border:1px solid #ddd;">Subtotal</th>
                </tr>
            </thead>
            <tbody>
                {items_html}
            </tbody>
        </table>

        <div style="margin-top:20px; text-align:right;">
            {envio_html}
            <h3>Total: S/. {total_general:.2f}</h3>
        </div>

        <p style="margin-top:30px; text-align:center; color:#555;">
            Recibimos tu pedido y lo estamos preparando para enviarlo a tu domicilio.<br>
            ¡Gracias por confiar en <b>Gobady Perú</b>!
        </p>
    </div>
    """
    return mensaje_html
