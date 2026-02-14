import resend
from django.conf import settings

resend.api_key = settings.RESEND_API_KEY

def enviar_correo_pedido(cliente_email, asunto, mensaje_html):
    """
    Envía un correo al cliente con los datos de su pedido.
    """
    try:
        response = resend.Emails.send({
            "from": "Gobady Perú <onboarding@resend.dev>",  # 👈 Puedes usar dominio verificado después
            "to": cliente_email,
            "subject": asunto,
            "html": mensaje_html,
        })
        return response
    except Exception as e:
        print("Error al enviar correo:", e)
        return None
