# apiApp/views/home_view.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import os
import json
import hashlib
from datetime import timedelta
from django.core.cache import cache
from django.utils import timezone

import google.generativeai as genai

from ..models import Categoria, Producto, MetodoPago

# NOTA: para seguridad, GEMINI_API_KEY debe estar en variables de entorno
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def HomePage(request):
    return render(request, 'index.html')


def get_client_ip(request):
    """Obtiene la IP real del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def check_rate_limit(ip_address):
    """
    Verifica si el cliente ha excedido el límite de requests
    Retorna (puede_continuar, tiempo_espera)
    """
    cache_key = f"chatbot_rate_{ip_address}"
    requests = cache.get(cache_key, [])
    now = timezone.now()

    # Limpiar requests antiguos (últimos 60 segundos)
    requests = [req_time for req_time in requests if now - req_time < timedelta(seconds=60)]

    # Límite: 10 mensajes por minuto
    if len(requests) >= 10:
        oldest_request = min(requests)
        wait_time = 60 - (now - oldest_request).seconds
        return False, wait_time

    # Agregar nuevo request
    requests.append(now)
    cache.set(cache_key, requests, 60)

    return True, 0


def check_daily_limit(ip_address):
    """Verifica límite diario por IP"""
    cache_key = f"chatbot_daily_{ip_address}"
    count = cache.get(cache_key, 0)

    # Límite de 20 mensajes por día (tal como cambiaste)
    if count >= 20:
        return False

    cache.set(cache_key, count + 1, 86400)  # 24 horas
    return True


def get_cached_response(user_message):
    """Cachea respuestas comunes para ahorrar API calls"""
    message_hash = hashlib.md5(user_message.lower().strip().encode()).hexdigest()
    cache_key = f"chatbot_response_{message_hash}"

    cached = cache.get(cache_key)
    if cached:
        print(f"✅ Respuesta cacheada para: {user_message[:30]}...")
    return cached


def cache_response(user_message, response):
    """Guarda respuesta en cache por 1 hora"""
    message_hash = hashlib.md5(user_message.lower().strip().encode()).hexdigest()
    cache_key = f"chatbot_response_{message_hash}"
    cache.set(cache_key, response, 3600)  # 1 hora


def obtener_contexto_tienda():
    """Genera información actualizada de productos, categorías y precios"""
    categorias = Categoria.objects.all()
    productos = Producto.objects.prefetch_related('categorias', 'tarifas').all()
    metodos_pago = MetodoPago.objects.all()

    contexto = "=== INFORMACIÓN DE GOBADY PERÚ ===\n\n"

    # Categorías disponibles
    contexto += "📦 CATEGORÍAS:\n"
    for cat in categorias:
        cantidad_productos = cat.productos.count()
        contexto += f"- {cat.nombre} ({cantidad_productos} productos)\n"

    contexto += "\n🛍️ PRODUCTOS DISPONIBLES:\n"
    for prod in productos:
        contexto += f"\n▪ {prod.nombre}\n"
        contexto += f"  Descripción: {prod.descripcion}\n"
        contexto += f"  Stock: {prod.cantidad} unidades\n"
        contexto += f"  Categorías: {', '.join([c.nombre for c in prod.categorias.all()])}\n"

        # Agregar tarifas
        if prod.tarifas.exists():
            contexto += "  Precios según cantidad:\n"
            for tarifa in prod.tarifas.all():
                rango = f"{tarifa.minimo}-{tarifa.maximo if tarifa.maximo else '∞'}"
                contexto += f"    • {rango} unidades → S/. {tarifa.precio_unitario} c/u\n"

    # Métodos de pago
    contexto += "\n💳 MÉTODOS DE PAGO:\n"
    for mp in metodos_pago:
        contexto += f"- {mp.nombre}: {mp.descripcion or 'Disponible'}\n"

    contexto += "\n📍 INFORMACIÓN DE ENVÍOS:\n"
    contexto += "- Envío a Lima: Consultar disponibilidad\n"
    contexto += "- Envío a provincia: S/. 8.00 adicionales\n"

    return contexto


@csrf_exempt
def chatbot(request):
    """Vista optimizada del chatbot con rate limiting y cache"""
    if request.method == "POST":
        try:
            # Obtener IP del cliente
            client_ip = get_client_ip(request)

            # Verificar rate limiting (por minuto)
            can_proceed, wait_time = check_rate_limit(client_ip)
            if not can_proceed:
                return JsonResponse({
                    "reply": f"⏱️ Por favor espera {wait_time} segundos antes de enviar otro mensaje.",
                    "rate_limited": True
                }, status=429)

            # Verificar límite diario
            if not check_daily_limit(client_ip):
                return JsonResponse({
                    "reply": "Has alcanzado el límite diario de mensajes. 😅 Vuelve mañana o contáctanos por WhatsApp al 940310504.",
                    "daily_limit_reached": True
                }, status=429)

            data = json.loads(request.body)
            user_message = data.get("message", "").strip()
            historial = data.get("history", [])

            if not user_message:
                return JsonResponse({"error": "Mensaje vacío"}, status=400)

            # Validar longitud del mensaje
            if len(user_message) > 500:
                return JsonResponse({
                    "reply": "Tu mensaje es demasiado largo. Por favor, hazlo más breve. 📝"
                }, status=400)

            # Verificar si hay respuesta cacheada
            cached_reply = get_cached_response(user_message)
            if cached_reply:
                return JsonResponse({"reply": cached_reply, "from_cache": True})

            # Obtener contexto actualizado de la tienda
            contexto_tienda = obtener_contexto_tienda()

            # Construir historial con debug
            historial_texto = ""
            historial_filtrado = [msg for msg in historial if not msg.get("isWelcome", False)]

            print(f"\n📊 === DEBUG CHATBOT ===")
            print(f"📊 Historial recibido: {len(historial)} mensajes")
            print(f"📊 Historial filtrado: {len(historial_filtrado)} mensajes")

            for msg in historial_filtrado[-6:]:  # Solo últimos 6
                rol = msg.get("sender", "user")
                texto = msg.get("text", "")
                if rol == "user":
                    historial_texto += f"Usuario: {texto}\n"
                else:
                    historial_texto += f"Asistente: {texto}\n"

            if historial_texto:
                historial_texto = historial_texto.strip() + "\n"
                print(f"✅ Historial construido:\n{historial_texto}")
            else:
                print("⚠️ No hay historial previo - Primera interacción")

            print(f"💬 Mensaje actual: {user_message}")
            print(f"========================\n")

            # Prompt mejorado
            prompt = f"""
Eres un asistente virtual experto y amigable de **Gobady Perú**, una tienda online de productos importados.

{contexto_tienda}

=== INSTRUCCIONES CRÍTICAS ===
1. Responde de forma conversacional, amigable y profesional
2. **NUNCA repitas saludos como "Hola" si ya hay historial de conversación**
3. Continúa la conversación de forma natural según el contexto previo
4. Si preguntan por productos, menciona nombre, descripción, precio según cantidad y stock
5. Si preguntan por precios específicos, usa las tarifas exactas del contexto
6. Si no sabes algo, sugiere visitar la web o contactar por WhatsApp al 940310504
7. Usa emojis ocasionalmente (máximo 1 por mensaje)
8. Mantén respuestas CORTAS (máximo 2-3 líneas)
9. Ubicación: Av. Óscar R. Benavides 486, Lima - Perú (es almacén, no tienda física)

{f"=== CONVERSACIÓN PREVIA ===" if historial_texto else "=== INICIO DE CONVERSACIÓN ==="}
{historial_texto if historial_texto else "Primera interacción con el usuario."}

=== MENSAJE ACTUAL DEL USUARIO ===
{user_message}

=== TU RESPUESTA (sin repetir saludos si ya hay conversación) ==="""

            # Crear modelo y generar
            model = genai.GenerativeModel(
                "gemini-2.5-flash",
                generation_config={
                    "temperature": 0.6,
                    "top_p": 0.9,
                    "top_k": 30,
                    "max_output_tokens": 200,
                }
            )

            response = model.generate_content(prompt)

            if not response or not response.text:
                return JsonResponse({
                    "reply": "Disculpa, tuve un problema. ¿Podrías reformular tu pregunta? 😊"
                })

            reply = response.text.strip()

            # Limitar longitud de respuesta
            if len(reply) > 500:
                reply = reply[:500] + "..."

            print(f"🤖 Respuesta generada: {reply[:100]}...")

            # Cachear la respuesta
            cache_response(user_message, reply)

            return JsonResponse({"reply": reply, "from_cache": False})

        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido"}, status=400)
        except Exception as e:
            print(f"❌ Error en chatbot: {str(e)}")
            return JsonResponse({
                "reply": "Lo siento, ocurrió un error. Intenta de nuevo en unos momentos. 🙏"
            }, status=500)

    return JsonResponse({"error": "Método no permitido"}, status=405)
