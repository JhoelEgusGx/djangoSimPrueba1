from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.throttling import ScopedRateThrottle


class TokenThrottledView(ObtainAuthToken):
    """POST /api/token/ con rate limiting: maximo 'token' intentos por minuto
    por IP (fuerza bruta de contraseñas). Tasa definida en
    settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['token']."""

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "token"
