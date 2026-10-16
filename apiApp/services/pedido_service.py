"""
Servicio para generar el correo de confirmación de un pedido:
- construir items_html a partir de los PedidoItem ya guardados
- generar el mensaje_html del correo
No recalcula precios ni totales: el serializer ya los dejó congelados
en la base de datos (misma fuente de verdad que se muestra en el dashboard).
"""

ENVIO_PROVINCIA_COST = 8


def generar_items_html(pedido):
    """
    Genera el HTML de las filas de productos usando los PedidoItem ya
    guardados (cantidad y precio_unitario congelados al momento de la compra).
    """
    items_html = ""

    for item in pedido.items.all():
        producto = item.producto
        cantidad = item.cantidad
        precio_unitario = float(item.precio_unitario)
        subtotal = float(item.subtotal())

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

    return items_html


def generar_mensaje_html(pedido, items_html, total_general, envio=0):
    """
    Genera el HTML del correo usando la estructura que tenías.
    Retorna string HTML.
    """
    envio_html = f"<p>Envío a provincia: <b>S/. {ENVIO_PROVINCIA_COST:.2f}</b></p>" if envio else ""
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
