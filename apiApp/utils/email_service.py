import logging

import resend
from django.conf import settings

logger = logging.getLogger(__name__)

resend.api_key = settings.RESEND_API_KEY

def enviar_correo_pedido(cliente_email, asunto, mensaje_html):
    """
    Envía un correo al cliente con los datos de su pedido.
    """
    try:
        response = resend.Emails.send({
            "from": settings.RESEND_FROM,
            "to": cliente_email,
            "subject": asunto,
            "html": mensaje_html,
        })
        return response
    except Exception:
        logger.exception("Error al enviar el correo de confirmación del pedido")
        return None
